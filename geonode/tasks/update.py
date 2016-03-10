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
from geonode.security.models import PermissionLevelMixin
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_anonymous_user
import time
import datetime

@task(name='geonode.tasks.update.fh_perms_update', queue='update')
def fh_perms_update(layer,filename):
    # anonymous_group, created = Group.objects.get_or_create(name='anonymous')
    #layer_list = Layer.objects.filter(name__icontains='fh')
    #total_layers = len(layer_list)
    #ctr = 1
    #for layer in layer_list:

    try:
        #print "[FH PERMISSIONS] {0}/{1} : {2} ".format(ctr,total_layers,layer.name)
        layer.remove_all_permissions()
        assign_perm('view_resourcebase', get_anonymous_user(), layer.get_self_resource())
        assign_perm('download_resourcebase', get_anonymous_user(), layer.get_self_resource())
        #ctr+=1
    except:
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        Err_msg = st + " Error in updating style of " + layer.name + "\n"
        filename.write(Err_msg)
        pass

#@task(name='geonode.tasks.update.fh_style_update', queue='update')
def fh_style_update(layer,filename):
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                    username=settings.OGC_SERVER['default']['USER'],
                    password=settings.OGC_SERVER['default']['PASSWORD'])

    #layer_list = Layer.objects.filter(name__icontains='fh')#initial run of script includes all fhm layers for cleaning of styles in GN + GS
    #layer_list = Layer.objects.filter(name__icontains='fh').exclude(styles__name__icontains='fhm'
    #total_layers = len(layer_list)
    fhm_style = cat.get_style("fhm")
    ctr = 0
    #for layer in layer_list:
        #print "[FH STYLE] {0}/{1} : {2} ".format(ctr,total_layers,layer.name)
        #delete thumbnail first because of permissions
    try:
        print "Layer thumbnail url: %s " % layer.thumbnail_url
        if "192" in local_settings.BASEURL:
            url = "geonode/uploaded/thumbs/layer-"+ layer.uuid + "-thumb.png" #if on local
            os.remove(url)
        else:
            url = "/var/www/geonode/uploaded/thumbs/layer-" +layer.uuid + "-thumb.png" #if on lipad
            os.remove(url)

        gs_layer = cat.get_layer(layer.name)
        print "GS LAYER: %s " % gs_layer.name
        gs_layer._set_default_style(fhm_style)
        cat.save(gs_layer) #save in geoserver

        ctr+=1

        gs_style = cat.get_style(layer.name)
        print "GS STYLE: %s " % gs_style.name
        print "Geoserver: Will delete style %s " % gs_style.name
        cat.delete(gs_style) #erase in geoserver the default layer_list
        gn_style = Style.objects.get(name=layer.name)
        print "Geonode: Will delete style %s " % gn_style.name
        gn_style.delete()#erase in geonode

        layer.sld_body = fhm_style.sld_body
        layer.save() #save in geonode
    except Exception as e:
        print "%s" % e
        pass
    #     print "%s"
        # "Error in %s" % layer.name
        # ts = time.time()
        # st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        # Err_msg = st + " Error in updating style of " + layer.name + "\n"
        # filename.write(Err_msg)

# f.close()

def layer_metadata(layer_list,flood_year,flood_year_probability):
    total_layers = len(layer_list)
    ctr = 0
    fh_err_log = "Flood-Hazard-Error-Log.txt"
    f = open(fh_err_log,'w')
    for layer in layer_list:
        print "Layer: %s" % layer.name
        fh_style_update(layer,f)
        fh_perms_update(layer,f)

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
        print "[{0} YEAR FH METADATA] {1}/{2} : {3}".format(flood_year,ctr,total_layers,layer.name)
    f.close()

@task(name='geonode.tasks.update.layers_metadata_update', queue='update')
def layers_metadata_update():
    # This will work for layer titles with the format '_fhXyr_'
    # layer_list = Layer.objects.filter(name__icontains='fh5yr').exclude(Q(keywords__name__icontains='flood hazard map')&Q(category__identifier='geoscientificInformation')&Q(purpose__icontains='the')&Q(abstract__icontains='the'))
    layer_list = Layer.objects.filter(name__icontains='fh5yr')
    total_layers = 0
    if layer_list is not None:
        total_layers = total_layers + len(layer_list)
        layer_metadata(layer_list,'5','20')

    layer_list = Layer.objects.filter(name__icontains='fh25yr')
    if layer_list is not None:
        total_layers = total_layers + len(layer_list)
        layer_metadata(layer_list,'25','4')

    layer_list = Layer.objects.filter(name__icontains='fh100yr')
    if layer_list is not None:
        total_layers = total_layers + len(layer_list)
        layer_metadata(layer_list,'100','1')

    print "Updated a total of %d layers" % total_layers

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
