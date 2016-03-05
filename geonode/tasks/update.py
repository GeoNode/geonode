import os
from geonode import settings
from geonode import GeoNodeException
from geonode import local_settings
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
from django.core.exceptions import ObjectDoesNotExist

def layer_metadata(layer_list,flood_year,flood_year_probability):
    layer_list_count = len(layer_list)
    ctr = 0
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

        print "Layer: %s" % layer.name
        layer.title = layer.name.replace("_10m","").replace("_30m","").replace("__"," ").replace("_"," ").replace("fh%syr" % flood_year,"%s Year Flood Hazard Map" % flood_year).title()

        first_half = "This shapefile, with a resolution of %s meters, illustrates the inundation extents in the area if the actual amount of rain exceeds that of a %s year-rain return period." % (map_resolution,flood_year) + "\n\n" + "Note: There is a 1/" + flood_year + " (" + flood_year_probability + "%) probability of a flood with " +flood_year + " year return period occurring in a single year. \n\n"
        second_half = "3 levels of hazard:" + "\n" + "Low Hazard (YELLOW)" + "\n" + "Height: 0.1m-0.5m" + "\n\n" + "Medium Hazard (ORANGE)" + "\n" + "Height: 0.5m-1.5m" + "\n\n" + "High Hazard (RED)" + "\n" + "Height: beyond 1.5m"
        layer.abstract = first_half + second_half

        layer.purpose = " The flood hazard map may be used by the local government for appropriate land use planning in flood-prone areas and for disaster risk reduction and management, such as identifying areas at risk of flooding and proper planning of evacuation."

        layer.keywords.add("Flood Hazard Map")
        layer.category = TopicCategory.objects.get(identifier="geoscientificInformation")
        layer.save()
        ctr+=1
        print "'{0}' out of '{1}' : Updated metadata for '{2}' ".format(ctr,layer_list_count,layer.name)


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

    #layer_list = Layer.objects.filter(name__icontains='fh')
    layer_list = Layer.objects.filter(name__icontains='fh').exclude(styles__name__icontains='fhm')#initial run of script includes all fhm layers for cleaning of styles in GN + GS
    fhm_style = cat.get_style("fhm")
    ctr = 1
    for layer in layer_list:
        print " {0} out of {1} layers. Will edit style of {2} ".format(ctr,len(layer_list),layer.name)
        #delete thumbnail first because of permissions

        print "Layer thumbnail url: %s " % layer.thumbnail_url
        if "192" in local_settings.BASEURL:
            url = "geonode"+layer.thumbnail_url #if on local
            os.remove(url)
        else:
            url = "/var/www/geonode"+layer.thumbnail_url #if on lipad
            os.remove(url)
        gs_layer = cat.get_layer(layer.name)
        gs_layer._set_default_style(fhm_style.name)
        cat.save(gs_layer) #save in geoserver
        layer.sld_body = fhm_style.sld_body
        layer.save() #save in geonode
        ctr+=1
        try:
            gs_style = cat.get_style(layer.name)
            print "Geoserver: Will delete style %s " % gs_style.name
            cat.delete(gs_style) #erase in geoserver the default layer_list
            gn_style = Style.objects.get(name=layer.name)
            print "Geonode: Will delete style %s " % gn_style.name
            gn_style.delete()#erase in geonode
        except:
            "Error in %s" % layer.name
            pass

@task(name='geonode.tasks.update.ceph_metadata_update', queue='update')
def ceph_metadata_update(uploaded_objects_list, update_grid=True):
    """
        NOTE: DOES NOT WORK
          Outputs error 'OperationalError: database is locked'
          Need a better way of making celery write into the database
    """
    # Loop through each metadata element
    csv_delimiter=','
    objects_inserted=0
    objects_updated=0
    gridref_dict_by_data_class=dict()
    for ceph_obj_metadata in uploaded_objects_list:
        metadata_list = ceph_obj_metadata.split(csv_delimiter)

        # Check if metadata list is valid
        if len(metadata_list) is 6:
            #try:
                """
                    Retrieve and check if metadata is present, update instead if there is
                """
                ceph_obj=None
                try:
                    ceph_obj = CephDataObject.objects.get(name=metadata_list[0])
                    # Commented attributes are not relevant to update
                    #ceph_obj.grid_ref = metadata_list[5]
                    #ceph_obj.data_class = get_data_class_from_filename(metadata_list[0])
                    #ceph_obj.content_type = metadata_list[3]

                    ceph_obj.last_modified = metadata_list[1]
                    ceph_obj.size_in_bytes = metadata_list[2]
                    ceph_obj.file_hash = metadata_list[4]

                    ceph_obj.save()

                    objects_updated += 1
                except ObjectDoesNotExist:
                    ceph_obj = CephDataObject(  name = metadata_list[0],
                                                #last_modified = time.strptime(metadata_list[1], "%Y-%m-%d %H:%M:%S"),
                                                last_modified = metadata_list[1],
                                                size_in_bytes = metadata_list[2],
                                                content_type = metadata_list[3],
                                                data_class = get_data_class_from_filename(metadata_list[0]),
                                                file_hash = metadata_list[4],
                                                grid_ref = metadata_list[5])
                    ceph_obj.save()

                    objects_inserted += 1
                if ceph_obj is not None:
                # Construct dict of gridrefs to update
                    if DataClassification.gs_feature_labels[ceph_obj.data_class] in gridref_dict_by_data_class:
                        gridref_dict_by_data_class[DataClassification.gs_feature_labels[ceph_obj.data_class].encode('utf8')].append(ceph_obj.grid_ref.encode('utf8'))
                    else:
                        gridref_dict_by_data_class[DataClassification.gs_feature_labels[ceph_obj.data_class].encode('utf8')] = [ceph_obj.grid_ref.encode('utf8'),]
                #except Exception as e:
                #    print("Skipping invalid metadata list: {0}".format(metadata_list))
        else:
            print("Skipping invalid metadata list (invalid length): {0}".format(metadata_list))

    # Pass to celery the task of updating the gird shapefile
    result_msg = "Succesfully encoded metadata of [{0}] of objects. Inserted [{1}], updated [{2}].".format(objects_inserted+objects_updated, objects_inserted, objects_updated)
    if update_grid:
        result_msg += " Starting update for PhilGrid."
        grid_feature_update.delay(gridref_dict_by_data_class)
    print result_msg

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
