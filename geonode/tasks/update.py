from geonode import settings
from geonode import GeoNodeException
from geonode.geoserver.helpers import ogc_server_settings
from pprint import pprint
from celery.task import task
from geonode.geoserver.helpers import gs_slurp
from geonode.documents.models import Document
from geonode.cephgeo.models import CephDataObject, DataClassification
from geonode.cephgeo.utils import get_data_class_from_filename
from geonode.cephgeo.gsquery import nested_grid_update
from geonode.layers.models import Layer
from geonode.base.models import TopicCategory
from django.db.models import Q
from geoserver.catalog import Catalog
from geonode.layers.models import Style
from geonode.geoserver.helpers import http_client
from geonode.layers.utils import create_thumbnail

def layer_metadata(layer_list,flood_year,flood_year_probability):
    for layer in layer_list:
        map_resolution = ''
        first_half = ''
        second_half = ''
        if "_10m_30m" in layer.name:
            map_resolution = '30'
        elif "_10m" in layer.name:
            map_resolution = '10'
        elif "_30m" in layer.name:
            map_resolution = '30'

        layer.title = layer.name.replace("_10m","").replace("_30m","").replace("__"," ").replace("_"," ").replace("fh%syr" % flood_year,"%s Year Flood Hazard Map" % flood_year).title()

        first_half = "This shapefile, with a resolution of %s meters, illustrates the inundation extents in the area if the actual amount of rain exceeds that of a %s year-rain return period." % (map_resolution,flood_year) + "\n\n" + "Note: There is a 1/" + flood_year + " (" + flood_year_probability + "%) probability of a flood with " +flood_year + " year return period occurring in a single year. \n\n"
        second_half = "3 levels of hazard:" + "\n" + "Low Hazard (YELLOW)" + "\n" + "Height: 0.1m-0.5m" + "\n\n" + "Medium Hazard (ORANGE)" + "\n" + "Height: 0.5m-1.5m" + "\n\n" + "High Hazard (RED)" + "\n" + "Height: beyond 1.5m"
        layer.abstract = first_half + second_half

        layer.purpose = " The flood hazard map may be used by the local government for appropriate land use planning in flood-prone areas and for disaster risk reduction and management, such as identifying areas at risk of flooding and proper planning of evacuation."

        layer.keywords.add("Flood Hazard Map")
        layer.category = TopicCategory.objects.get(identifier="geoscientificInformation")
        layer.save()

        print "Updated metadata for this layer: %s" % layer.name


@task(name='geonode.tasks.update.layers_metadata_update', queue='update')
def layers_metadata_update():
    # This will work for layer titles with the format '_fhXyr_'
    layer_list = Layer.objects.filter(name__icontains='fh5yr').exclude(Q(keywords__name__icontains='flood hazard map')&Q(category__identifier='geoscientificInformation')&Q(purpose__icontains='the')&Q(abstract__icontains='the'))
    if layer_list is not None:
        layer_metadata(layer_list,'5','20')

    layer_list = Layer.objects.filter(name__icontains='fh25yr').exclude(Q(keywords__name__icontains='flood hazard map')&Q(category__identifier='geoscientificInformation')&Q(purpose__icontains='the')&Q(abstract__icontains='the'))
    if layer_list is not None:
        layer_metadata(layer_list,'25','4')

    layer_list = Layer.objects.filter(name__icontains='fh100yr').exclude(Q(keywords__name__icontains='flood hazard map')&Q(category__identifier='geoscientificInformation')&Q(purpose__icontains='the')&Q(abstract__icontains='the'))
    if layer_list is not None:
        layer_metadata(layer_list,'100','1')

@task(name='geonode.tasks.update.fh_style_update', queue='update')
def fh_style_update():
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                    username=settings.OGC_SERVER['default']['USER'],
                    password=settings.OGC_SERVER['default']['PASSWORD'])
    # gn_style_list = Style.objects.filter(name__icontains='fh').exclude(Q(sld_body__icontains='<sld:CssParameter name="fill">#ffff00</sld:CssParameter>'))
    gn_style_list = Style.objects.filter(name__icontains='fh').exclude(Q(name__icontains="fhm"))
    fh_styles_count = len(gn_style_list)
    ctr = 0
    if gn_style_list is not None:
        fhm_style = cat.get_style("fhm")
        for gn_style in gn_style_list:
            #change style in geoserver
	    print "Style name %s " % gn_style.name
            gs_style  = cat.get_style(gn_style.name)
            gs_style.update_body(fhm_style.sld_body)
            #change style in geonode
            gn_style.sld_body = fhm_style.sld_body
            gn_style.save()
            #for updating thumbnail
            layer = Layer.objects.get(name=gn_style.name)
            if layer is not None:
                params = {
                    'layers': layer.typename.encode('utf-8'),
                    'format': 'image/png8',
                    'width': 200,
                    'height': 150,
                }
                p = "&".join("%s=%s" % item for item in params.items())
                thumbnail_remote_url = ogc_server_settings.PUBLIC_LOCATION + \
                    "wms/reflect?" + p
                # thumbnail_create_url = ogc_server_settings.LOCATION + \
                #     "wms/reflect?" + p
                create_thumbnail(layer, thumbnail_remote_url, thumbnail_remote_url, ogc_client=http_client)
                ctr+=1
                print "'{0}' out of '{1}' : Updated style for '{2}' ".format(ctr,fh_styles_count,gn_style.name)


@task(name='geonode.tasks.update.ceph_metadata_udate', queue='update')
def ceph_metadata_udate(uploaded_objects):
    """
        NOTE: DOES NOT WORK
          Outputs error 'OperationalError: database is locked'
          Need a better way of making celery write into the database
    """
    #Save each ceph object
    for obj_meta_dict in uploaded_objects:
        ceph_obj = CephDataObject(  name = obj_meta_dict['name'],
                                    #last_modified = time.strptime(obj_meta_dict['last_modified'], "%Y-%m-%d %H:%M:%S"),
                                    last_modified = obj_meta_dict['last_modified'],
                                    size_in_bytes = obj_meta_dict['bytes'],
                                    content_type = obj_meta_dict['content_type'],
                                    data_class = get_data_class_from_filename(obj_meta_dict['name']),
                                    file_hash = obj_meta_dict['hash'],
                                    grid_ref = obj_meta_dict['grid_ref'])
        ceph_obj.save()

@task(name='geonode.tasks.update.grid_feature_update', queue='update')
def grid_feature_update(gridref_dict_by_data_class, field_value=1):
    """
        :param gridref_dict_by_data_class: contains mapping of [feature_attr] to [grid_ref_list]
        :param field_value: [1] or [0]
        Update the grid shapefile feature attribute specified by [feature_attr] on gridrefs in [gridref_list]
    """
    for feature_attr, grid_ref_list in gridref_dict_by_data_class.iteritems():
        nested_grid_update(grid_ref_list, feature_attr, field_value)

@task(name='geonode.tasks.update.geoserver_update_layers', queue='update')
def geoserver_update_layers(*args, **kwargs):
    """
    Runs update layers.
    """
    return gs_slurp(*args, **kwargs)


@task(name='geonode.tasks.update.create_document_thumbnail', queue='update')
def create_document_thumbnail(object_id):
    """
    Runs the create_thumbnail logic on a document.
    """

    try:
        document = Document.objects.get(id=object_id)

    except Document.DoesNotExist:
        return

    image = document._render_thumbnail()
    filename = 'doc-%s-thumb.png' % document.id
    document.save_thumbnail(filename, image)
