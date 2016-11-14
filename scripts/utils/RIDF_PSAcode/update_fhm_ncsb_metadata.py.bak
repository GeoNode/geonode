#!/usr/bin/env python

from geonode.settings import GEONODE_APPS
import geonode.settings as settings
from geonode.cephgeo.models import RIDF
from geonode.layers.models import Layer
from collections import defaultdict
from pprint import pprint
from geoserver.catalog import Catalog
from geonode.layers.models import Style
from django.contrib.auth.models import Group
import time, datetime
from geonode.base.models import TopicCategory

def fh_perms_update(layer):
    # anonymous_group, created = Group.objects.get_or_create(name='anonymous')
    #layer_list = Layer.objects.filter(name__icontains='fh')
    #total_layers = len(layer_list)
    #ctr = 1
    #for layer in layer_list:

    try:
        # geoadmin = User.objects.get.filter(username='geoadmin')
        # for user in User.objects.all():
        layer.remove_all_permissions()
        anon_group = Group.objects.get(name='anonymous')
        assign_perm('view_resourcebase', anon_group, layer.get_self_resource())
        assign_perm('download_resourcebase', anon_group, layer.get_self_resource())
        # superusers=get_user_model().objects.filter(Q(is_superuser=True))
        # for superuser in superusers:
        #     assign_perm('view_resourcebase', superuser, layer.get_self_resource())
        #     assign_perm('download_resourcebase', superuser, layer.get_self_resource())
        assign_perm('view_resourcebase', get_anonymous_user(), layer.get_self_resource())
        assign_perm('download_resourcebase', get_anonymous_user(), layer.get_self_resource())
        #print "[FH PERMISSIONS] {0}/{1} : {2} ".format(ctr,total_layers,layer.name)
        # layer.remove_all_permissions()
        # assign_perm('view_resourcebase', get_anonymous_user(), layer.get_self_resource())
        # assign_perm('download_resourcebase', get_anonymous_user(), layer.get_self_resource())
        #ctr+=1
    except:
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        Err_msg = st + " Error in updating style of " + layer.name + "\n"
        pass

def style_update(layer,style_template):
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                    username=settings.OGC_SERVER['default']['USER'],
                    password=settings.OGC_SERVER['default']['PASSWORD'])

    #layer_list = Layer.objects.filter(name__icontains='fh')#initial run of script includes all  layers for cleaning of styles in GN + GS
    #layer_list = Layer.objects.filter(name__icontains='fh').exclude(styles__name__icontains='fhm'
    #total_layers = len(layer_list)
    try:
        layer_attrib = layer.attributes[0].attribute.encode("utf-8")
    except Exception as e:
            print "No layer attribute %s" % e
    ctr = 0
    #for layer in layer_list:
        #print "[FH STYLE] {0}/{1} : {2} ".format(ctr,total_layers,layer.name)
        #delete thumbnail first because of permissions

    if '_fh' in layer.name:
        style = None
        if layer_attrib == "Var":
            style = cat.get_style(style_template)
        else:
            style = cat.get_style("fhm_merge")
    else:
        style = cat.get_style(style_template)

    if style is not None:
        try:
            print "Layer thumbnail url: %s " % layer.thumbnail_url
            if "lipad" not in settings.BASEURL:
                url = "geonode/uploaded/thumbs/layer-"+ layer.uuid + "-thumb.png"
                os.remove(url)
            else:
                url = "/var/www/geonode/uploaded/thumbs/layer-" +layer.uuid + "-thumb.png"
                os.chown(url,'www-data','www-data')
                os.remove(url)

            gs_layer = cat.get_layer(layer.name)
            print "GS LAYER: %s " % gs_layer.name
            gs_layer._set_default_style(style)
            cat.save(gs_layer)
            
            ctr+=1
            gs_style = cat.get_style(layer.name)
            if gs_style is not None:
                print "GS STYLE: %s " % gs_style.name
                print "Geoserver: Will delete style %s " % gs_style.name
                cat.delete(gs_style)
            gn_style = Style.objects.get(name=layer.name)
            if gn_style is not None:
                print "Geonode: Will delete style %s " % gn_style.name
                gn_style.delete()

            layer.sld_body = style.sld_body
            _style = Style.objects.get(name=style_template)
            layer.default_style = _style
            layer.save()
        except Exception as e:
            print "%s" % e


def fhm_year_metadata(flood_year, skip_prev):
    flood_year_probability = int(100/flood_year)
    layer_list = []
    # if skip_prev:
    #     layer_list = Layer.objects.filter(name__icontains='fh{0}yr'.format(flood_year)).exclude(Q(keywords__name__icontains='flood hazard map')&Q(category__identifier='geoscientificInformation')&Q(purpose__icontains='the')&Q(abstract__icontains='the'))
    # else:
    #     layer_list = Layer.objects.filter(name__icontains='fh{0}yr'.format(flood_year))
    # layer_list = Layer.objects.filter(name__icontains='fh{0}yr'.format(flood_year))
    # Search for layers that start with an underscore and numbers
    layer_list = Layer.objects.filter(name__iregex=r'^_[0-9]+_fh' + str(flood_year))
    total_layers = len(layer_list)
    print("Updating metadata of [{0}] Flood Hazard Maps for Flood Year [{1}]".format(total_layers, flood_year))
    ctr = 0
    fh_err_log = "Flood-Hazard-Error-Log.txt"
    
    for layer in layer_list:
        try:
            print "Layer: %s" % layer.name
            style_update(layer,'fhm')
            fh_perms_update(layer)
            #fh_perms_update(layer,f)

            #batch_seed(layer)

            map_resolution = ''

            if "_10m_30m" in layer.name:
                map_resolution = '30'
            elif "_10m" in layer.name:
                map_resolution = '10'
            elif "_30m" in layer.name:
                map_resolution = '30'
            
            print "Layer: %s" % layer.name
            # layer.title = layer.name.replace("_10m","").replace("_30m","").replace("__"," ").replace("_"," ").replace("fh%syr" % flood_year,"%s Year Flood Hazard Map" % flood_year).title()
            
            ## Use nscb for layer title
            nscb = int(layer.name.split('_')[1])
            r = RIDF.objects.get(nscb_code=nscb)
            if r is not None:
                ridf = str(eval('r._' + str(flood_year) + 'yr'))
            else:
                return 'RIDF not found'
            layer.title = (r.municipality + ', ' + r.province + ' %s Year Flood Hazard Map' % flood_year).title()

            print layer.title
            layer.abstract = """This shapefile, with a resolution of {0} meters, illustrates the inundation extents in the area if the actual amount of rain exceeds that of a {1} year-rain return period.

    Note: There is a 1/{2} ({3}%) probability of a flood with {4} year return period occurring in a single year. The RIDF is {5}.

    3 levels of hazard:
    Low Hazard (YELLOW)
    Height: 0.1m-0.5m

    Medium Hazard (ORANGE)
    Height: 0.5m-1.5m

    High Hazard (RED)
    Height: beyond 1.5m""".format(map_resolution, flood_year, flood_year, flood_year_probability, flood_year, ridf)


            layer.purpose = " The flood hazard map may be used by the local government for appropriate land use planning in flood-prone areas and for disaster risk reduction and management, such as identifying areas at risk of flooding and proper planning of evacuation."
            
            layer.keywords.add("Flood Hazard Map")
            for tag in r.riverbasins.all():
                layer.keywords.add(tag)
            layer.category = TopicCategory.objects.get(identifier="geoscientificInformation")
            layer.save()
            ctr+=1
            print "[{0} YEAR FH METADATA] {1}/{2} : {3}".format(flood_year,ctr,total_layers,layer.name)
        except Exception as e:
            print "%s" % e
            pass
    
    

def fhm_metadata_update(skip_prev=True, flood_years=(5, 25, 100)):
    for year in flood_years:
        fhm_year_metadata(year, skip_prev)


if __name__ == '__main__':
    fhm_metadata_update()
