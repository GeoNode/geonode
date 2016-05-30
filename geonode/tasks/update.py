from geonode.geoserver.helpers import ogc_server_settings
from pprint import pprint
from celery.task import task
from geonode.geoserver.helpers import gs_slurp
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.base.models import TopicCategory
from django.db.models import Q
from geoserver.catalog import Catalog
from geonode.layers.models import Style
from geonode.geoserver.helpers import http_client
from geonode.layers.utils import create_thumbnail
from django.core.exceptions import ObjectDoesNotExist
from celery.utils.log import get_task_logger
import geonode.settings as settings
import os, subprocess, time, datetime
logger = get_task_logger("geonode.tasks.update")
from geonode.security.models import PermissionLevelMixin
from django.contrib.auth.models import Group
from guardian.shortcuts import assign_perm, get_anonymous_user
from string import Template
 

@task(name='geonode.tasks.update.fh_perms_update', queue='update')
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

    if 'fh' in layer.name:
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
            print "GS STYLE: %s " % gs_style.name
            print "Geoserver: Will delete style %s " % gs_style.name
            cat.delete(gs_style)
            gn_style = Style.objects.get(name=layer.name)
            print "Geonode: Will delete style %s " % gn_style.name
            gn_style.delete()

            layer.sld_body = style.sld_body
            layer.save()
        except Exception as e:
            print "%s" % e
            

@task(name='geonode.tasks.update.seed_layers', queue='update')
def seed_layers(keyword):
    layer_list = Layer.objects.filter(keywords__name__icontains=keyword)
    for layer in layer_list:
        try:
            out = subprocess.check_output([settings.PROJECT_ROOT + '/gwc.sh', 'seed',
            '{0}:{1}'.format(layer.workspace,layer.name) , 'EPSG:4326', '-v', '-a',
            settings.OGC_SERVER['default']['USER'] + ':' +
            settings.OGC_SERVER['default']['PASSWORD'], '-u',
            settings.OGC_SERVER['default']['LOCATION'] + 'gwc/rest'],
            stderr=subprocess.STDOUT)
            print out
        except subprocess.CalledProcessError as e:
            print 'Error seeding layer:', layer
            print 'e.returncode:', e.returncode
            print 'e.cmd:', e.cmd
            print 'e.output:', e.output


def fhm_year_metadata(flood_year, skip_prev):
    flood_year_probability = int(100/flood_year)
    layer_list = []
    # if skip_prev:
    #     layer_list = Layer.objects.filter(name__icontains='fh{0}yr'.format(flood_year)).exclude(Q(keywords__name__icontains='flood hazard map')&Q(category__identifier='geoscientificInformation')&Q(purpose__icontains='the')&Q(abstract__icontains='the'))
    # else:
    #     layer_list = Layer.objects.filter(name__icontains='fh{0}yr'.format(flood_year))
    layer_list = Layer.objects.filter(name__icontains='fh{0}yr'.format(flood_year))
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
            layer.title = layer.name.replace("_10m","").replace("_30m","").replace("__"," ").replace("_"," ").replace("fh%syr" % flood_year,"%s Year Flood Hazard Map" % flood_year).title()
            
            layer.abstract = """This shapefile, with a resolution of {0} meters, illustrates the inundation extents in the area if the actual amount of rain exceeds that of a {1} year-rain return period.

    Note: There is a 1/{2} ({3}%) probability of a flood with {4} year return period occurring in a single year.

    3 levels of hazard:
    Low Hazard (YELLOW)
    Height: 0.1m-0.5m

    Medium Hazard (ORANGE)
    Height: 0.5m-1.5m

    High Hazard (RED)
    Height: beyond 1.5m""".format(map_resolution, flood_year, flood_year, flood_year_probability, flood_year)


            layer.purpose = " The flood hazard map may be used by the local government for appropriate land use planning in flood-prone areas and for disaster risk reduction and management, such as identifying areas at risk of flooding and proper planning of evacuation."
            
            layer.keywords.add("Flood Hazard Map")
            layer.category = TopicCategory.objects.get(identifier="geoscientificInformation")
            layer.save()
            ctr+=1
            print "[{0} YEAR FH METADATA] {1}/{2} : {3}".format(flood_year,ctr,total_layers,layer.name)
        except Exception as e:
            print "%s" % e
            pass
    
    

@task(name='geonode.tasks.update.layers_metadata_update', queue='update')
def fhm_metadata_update(skip_prev=True, flood_years=(5, 25, 100)):
    for year in flood_years:
        fhm_year_metadata(year, skip_prev)

@task(name='geonode.tasks.update.sar_metadata_update', queue='update')
def sar_metadata_update():

    ###############################
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                    username=settings.OGC_SERVER['default']['USER'],
                    password=settings.OGC_SERVER['default']['PASSWORD'])

    count_notification = Template('[$ctr/$total] Editing Metadata for Layer: $layername')

    ###
    #   SAR
    #   with sld template
    ###
    filter_substring = 'sar_'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    total=len(layer_list)
    ctr=0
    title = Template('$area SAR DEM')

    for layer in layer_list:
        ctr+=1
        print "Layer: %s" % layer.name
        style_update(layer,'dem')
        text_split = layer.name.split(filter_substring)
        area = text_split[1].title().replace('_',' ') #from sar_area to ['','area']
        print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
        layer.title = title.substitute(area=area)
        layer.abstract = """All Synthetic Aperture Radar digital elevation models was acquired from MacDonald, Dettwiler and Associates Ltd. (MDA), British Columbia, Canada and post-processed by the UP Training Center for Applied Geodesy and Photogrammetry (UP-TCAGP), through the DOST-GIA funded Disaster Risk and Exposure Assessment for Mitigation (DREAM) Program.

            Projection:     WGS84 UTM Zone 51
            Resolution:     10 m
            Tile Size:  10km by 10km
            Absolute vertical map accuracy: LE 90
            Date of Acquisition: February 21, 2012-September 13, 2013
            """
        layer.keywords.add("SAR")
        layer.save()

@task(name='geonode.tasks.update.pl2_metadata_update', queue='update')
def pl2_metadata_update():
    # 

    ###############################
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                    username=settings.OGC_SERVER['default']['USER'],
                    password=settings.OGC_SERVER['default']['PASSWORD'])

    count_notification = Template('[$ctr/$total] Editing Metadata for Layer: $layername')

    ###
    #   TREES - DBH (diameter at breast height) and Standing Tree Volume Estimation
    #   with sld template
    ###
    filter_substring = '_trees'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier = "biota"
            title = Template('$area DBH (diameter at breast height) and Standing Tree Volume Estimation')
            for layer in layer_list:  
                ctr+=1
                print "Layer: %s" % layer.name
                style_update(layer,'trees_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """These are points that display the estimated diameter at breast height (DBH) of a forested area. It shows the percentage of trees per dbh class (in cm).

                These are points that display the estimated tree volume of a forested area. It shows the percentage of trees per volume class (in cum)
                """
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", " Trees", " DBH", "Standing Tree Volume", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   CCM - Canopy Cover Model
    ###
    filter_substring = '_ccm'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier = "biota"
            title = Template('$area Canopy Cover Model')
           
            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "These are rasters, with resolution of 1 meter, that display the canopy cover of a forested area. It shows Canopy Cover % which ranges from Low to High"
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", "Canopy Cover", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   CHM - Canopy Height Models
    ###

    filter_substring = '_chm'
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier = "biota"
            title = Template('$area Canopy Height Model')
           
            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "These are rasters, with resolution of 1 meter, that display the canopy height of a forested area.It shows the height of trees/vegetation (in meter) present in the sample area"
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", "Canopy Height", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   AGB - Area Biomass Estimation
    ###
    filter_substring="_agb"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier = "biota"
            title = Template('$area Biomass Estimation')
           
            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "These are rasters, with a resolution of 10 meters, that display the estimated biomass of a forested area. It shows the total biomass (in kg) per 10sqm of the selected area."
                layer.purpose = "Forest Resources Assesment/Management"
                layer.keywords.add("FRExLS", "Biomass", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   aquaculture - Aquaculture
    ###
    filter_substring="_aquaculture"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="imageryBaseMapsEarthCover"
            title = Template('$area Aquaculture')
           
            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                style_update(layer,layer.name+'_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B and reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include extracted aquaculture (fishponds, fish pens, fish traps, fish corrals) from the LiDAR data and/or orthophoto.
             
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free."
                """
                layer.purpose = "Detailed Coastal (aquaculture, mangroves) Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making."
                layer.keywords.add("CoastMap", "Aquaculture", "Fish Pens", "Fish Ponds", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass   
    ###
    #   mangroves - Mangroves
    ###
    filter_substring="_mangroves"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="imageryBaseMapsEarthCover"
            title = Template('$area Mangroves')
           
            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                style_update(layer,layer.name+'_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include extracted mangrove areas from the LiDAR data and/or orthophoto.
             
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free.
                """
                layer.purpose = "Detailed Coastal (aquaculture, mangroves) Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making."
                layer.keywords.add("CoastMap", "Mangroves", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   agrilandcover - Agricultural Landcover
    ###
    filter_substring="_agrilandcover"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="imageryBaseMapsEarthCover"
            title = Template('$area Agricultural Landcover')
           
            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                style_update(layer,layer.name+'_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include initial Land Cover Map of Agricultural Resources.
             
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free.
                """
                layer.purpose = "Detailed Agricultural Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making. This complements on-going programs of the Department of Agriculture by utilizing LiDAR data for the mapping of high value crops and vulnerability assessment."
                layer.keywords.add("PARMap", "Agriculture", "Landcover", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass  
    ###
    #   agricoastlandcover - Agricultural and Coastal Landcover
    ###

    filter_substring="_agricoastlandcover"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="imageryBaseMapsEarthCover"
            title = Template('$area Agricultural and Coastal Landcover')
           
            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """ Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include initial Land Cover Map of Agricultural Resources integrated with Coastal Resources.
     
                Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
                Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
                Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free.
                """
                layer.purpose = "Integrated Agricultural and Coastal Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making. This complements on-going programs of the Department of Agriculture by utilizing LiDAR data for the mapping of high value crops and vulnerability assessment."
                layer.keywords.add("PARMap", "Agriculture", "COASTMap", "Mangrove", "Landcover", "PhilLiDAR2")
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

    ###
    #   irrigation - River Basin Irrigation Network
    #   with sld template
    ###
    filter_substring="_irrigation"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="inlandWaters"
            title = Template('$area River Basin Irrigation Network')

            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                style_update(layer,'irrigation_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "This shapefile contains extracted irrigation networks from LiDAR DEM and orthophotos."
                layer.purpose = "Irrigation network maps are useful for planning irrigation structures to fully utilize water resources and distribute water to non-irrigated lands. This data contains irrigation classification and the corresponding elevations of start and end-point of each segment that can be used for further studies that involve irrigation network modeling. "
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.keywords.add("Irrigation Networks", "Canals", "Ditches", "Hydrology", "PHD", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   streams - River Basin Streams (LiDAR), Streams (SAR)
    ###
    filter_substring="_streams"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="inlandWaters"
            title = Template('$area River Basin Streams (LiDAR), Streams (SAR)')

            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                # style_update(layer,'')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = """This shapefile contains extracted stream network derived from LiDAR DEM with a 1-meter resolution (solid lines) and SAR DEM with 10-m resolution (broken lines).

                Note: The extracted streams are based on thalwegs (lines of lowest elevation) and not on centerlines."
                """
                layer.purpose = "Stream network maps provides important information to planners and decision makers in managing and controlling streams to make these bodies of water more useful and less disruptive to human activity."
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.keywords.add("Streams", "Rivers", "Creeks", "Drainages", "Hydrology", "PHD", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
    ###
    #   wetlands - River Basin Inland Wetlands
    #   with sld template
    ###
    filter_substring="_wetlands"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="inlandWaters"
            title = Template('$area River Basin Inland Wetlands')

            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                style_update(layer,'wetlands_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area)
                layer.abstract = "This shapefile contains extacted inland wetlands derived from LiDAR DEM and orthophotos. Depressions that can be detected from the elevation model were indicative of the presence of wetlands."
                layer.purpose = "Inland wetlands are key to preserving biodiversity. These features are home to various species that rely on a healthy ecosystem to thrive. Also, wetlands are sometimes used for water storage that can later be utilized in agricultural activities."
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.keywords.add("Inland Wetlands", "Wetlands", "Depressions", "Hydrology", "PHD", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass

            
    ###
    #   power - Hydropower Potential Sites
    #   with sld template
    ###
    filter_substring="_power"
    layer_list = Layer.objects.filter(name__icontains=filter_substring)
    if layer_list is not None:
        try:
            total=len(layer_list)
            ctr=0
            identifier="environment"
            title = Template('Hydropower Potential Sites $distance $area') #depends if 1000

            for layer in layer_list:
                ctr+=1
                print "Layer: %s" % layer.name
                style_update(layer,'power_template')
                text_split = layer.name.split(filter_substring)
                area = text_split[0].title().replace('_',' ')
                distance = text_split[1].replace('_',' ').lstrip()
                print count_notification.substitute(ctr=ctr,total=total,layername=layer.name)
                layer.title = title.substitute(area=area,distance=distance)
                layer.abstract = """Each province has 3 datasets - for horizontal distances of 100m, 500m, 1000m - with the following information: head, simulated flow, simulated power and hydropower classification.

                The hydropower resource potential is theoretical based on the hydrologic model ArcSWAT and terrain analysis. Hydropower classification is based on theoretical capacity with 80% technical efficiency as prescribed by the DOE."""
                layer.purpose = "Site Identification of Hydropower Sites for future development"
                layer.category = TopicCategory.objects.get(identifier=identifier)
                layer.keywords.add("Hydropower", "REMap", "PhilLiDAR2")
                layer.save()
        except Exception as e:
            print "%s" % e
            pass
            

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
