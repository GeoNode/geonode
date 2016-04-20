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

 

@task(name='geonode.tasks.update.fh_perms_update', queue='update')
def fh_perms_update(layer,filename):
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
        filename.write(Err_msg)
        pass

@task(name='geonode.tasks.update.fh_style_update', queue='update')
def fh_style_update(layer,filename):
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
                    username=settings.OGC_SERVER['default']['USER'],
                    password=settings.OGC_SERVER['default']['PASSWORD'])

    #layer_list = Layer.objects.filter(name__icontains='fh')#initial run of script includes all fhm layers for cleaning of styles in GN + GS
    #layer_list = Layer.objects.filter(name__icontains='fh').exclude(styles__name__icontains='fhm'
    #total_layers = len(layer_list)
    layer_attrib = layer.attributes[0].attribute.encode("utf-8")
    fhm_style = None
    if layer_attrib == "Var":
        fhm_style = cat.get_style("fhm")
    else:
        fhm_style = cat.get_style("fhm_merge")
    ctr = 0
    #for layer in layer_list:
        #print "[FH STYLE] {0}/{1} : {2} ".format(ctr,total_layers,layer.name)
        #delete thumbnail first because of permissions
    try:
        print "Layer thumbnail url: %s " % layer.thumbnail_url
        if "192" in settings.BASEURL:
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

@task(name='geonode.tasks.update.geoserver_seed_layers', queue='update')
def geoserver_seed_layers(layer_list):
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
    f = open(fh_err_log,'w')
    for layer in layer_list:
        print "Layer: %s" % layer.name
        fh_style_update(layer,f)
        fh_perms_update(layer,f)

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
    f.close()
    

@task(name='geonode.tasks.update.layers_metadata_update', queue='update')
def fhm_metadata_update(skip_prev=True, flood_years=(5, 25, 100)):
    for year in flood_years:
        fhm_year_metadata(year, skip_prev)

def pl2_metadata_agb():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='agb')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("agb","Biomass Estimation").title()
        
        layer.abstract = """These are rasters, with a resolution of 10 meters, that display the estimated biomass of a forested area. It shows the total biomass (in kg) per 10sqm of the selected area."""

        layer.purpose = "Forest Resources Assesment/Management"
        layer.keywords.add("FRExLS")
        layer.keywords.add("Biomass")
        layer.keywords.add("PhilLiDAR2")
        
        layer.category = TopicCategory.objects.get(identifier="biota")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_chm():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='chm')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("chm","Canopy Height Model").title()
        
        layer.abstract = """These are rasters, with resolution of 1 meter, that display the canopy height of a forested area.It shows the height of trees/vegetation (in meter) present in the sample area"""

        layer.purpose = "Forest Resources Assesment/Management"
        layer.keywords.add("FRExLS")
        layer.keywords.add("Canopy Height")
        layer.keywords.add("PhilLiDAR2")
        
        layer.category = TopicCategory.objects.get(identifier="biota")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_ccm():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='ccm')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("ccm","Canopy Cover Model").title()
        
        layer.abstract = """These are rasters, with resolution of 1 meter, that display the canopy cover of a forested area. It shows Canopy Cover % which ranges from Low to High"""

        layer.purpose = "Forest Resources Assesment/Management"
        layer.keywords.add("FRExLS")
        layer.keywords.add("Canopy Cover")
        layer.keywords.add("PhilLiDAR2")

        layer.category = TopicCategory.objects.get(identifier="biota")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_trees():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='trees')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("trees","DBH (diameter at breast height) and Standing Tree Volume Estimations").title()
        
        layer.abstract = """These are points that display the estimated diameter at breast height (DBH) of a forested area. It shows the percentage of trees per dbh class (in cm).
These are points that display the estimated tree volume of a forested area. It shows the percentage of trees per volume class (in cum)"""

        layer.purpose = "Forest Resources Assesment/Management"
        layer.keywords.add("FRExLS")
        layer.keywords.add("Trees")
        layer.keywords.add("PhilLiDAR2")
        layer.keywords.add("DBH")
        layer.keywords.add("Standing Tree Volume")
        
        layer.category = TopicCategory.objects.get(identifier="biota")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_wetlands():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='wetlands')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("streams","River Basin Inland Wetlands").title()
        
        layer.abstract = """This shapefile contains extacted inland wetlands derived from LiDAR DEM and orthophotos. Depressions that can be detected from the elevation model were indicative of the presence of wetlands."""


        layer.purpose = "Inland wetlands are key to preserving biodiversity. These features are home to various species that rely on a healthy ecosystem to thrive. Also, wetlands are sometimes used for water storage that can later be utilized in agricultural activities."
        layer.keywords.add("Inland Wetlands")
        layer.keywords.add("Wetlands")
        layer.keywords.add("PhilLiDAR2")
        layer.keywords.add("Depressions")
        layer.keywords.add("PHD")
        layer.keywords.add("Hydrology")

        layer.category = TopicCategory.objects.get(identifier="inlandWaters")
        layer.save()
        print "Layer: %s" % layer.name


def pl2_metadata_streams():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='streams')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("streams","River Basin Streams (Lidar), Streams (Sar)").title()
        
        layer.abstract = """This shapefile contains extracted stream network derived from LiDAR DEM with a 1-meter resolution (solid lines) and SAR DEM with 10-m resolution (broken lines).
Note: The extracted streams are based on thalwegs (lines of lowest elevation) and not on centerlines."""


        layer.purpose = "Stream network maps provides important information to planners and decision makers in managing and controlling streams to make these bodies of water more useful and less disruptive to human activity. "
        layer.keywords.add("Streams")
        layer.keywords.add("Rivers")
        layer.keywords.add("PhilLiDAR2")
        layer.keywords.add("Creeks")
        layer.keywords.add("Drainages")
        layer.keywords.add("PHD")
        layer.keywords.add("Hydrology")

        layer.category = TopicCategory.objects.get(identifier="inlandWaters")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_irrigation():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='irrigation')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("irrigation","River Basin Irrigation Network").title()
        
        layer.abstract = """This shapefile contains extracted irrigation networks from LiDAR DEM and orthophotos. """


        layer.purpose = "Irrigation network maps are useful for planning irrigation structures to fully utilize water resources and distribute water to non-irrigated lands. This data contains irrigation classification and the corresponding elevations of start and end-point of each segment that can be used for further studies that involve irrigation network modeling."
        layer.keywords.add("Irrigation Networks")
        layer.keywords.add("Canals")
        layer.keywords.add("PhilLiDAR2")
        layer.keywords.add("Ditches")
        layer.keywords.add("Hydrology")
        layer.keywords.add("PHD")

        layer.category = TopicCategory.objects.get(identifier="inlandWaters")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_agricoastlandcover():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='agricoastlandcover')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("agricoastlandcover","Agricultural and Coastal Landcover").title()
        
        layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include initial Land Cover Map of Agricultural Resources integrated with Coastal Resources.
 
 Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
 Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
 Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on
 the source datasets, and limitations of the software and algorithms used and implemented procedures.
 The Products are provided \"as is\" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program 
 does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or
 use of the Products will be error free."""


        layer.purpose = "Integrated Agricultural and Coastal Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making. This complements on-going programs of the Department of Agriculture by utilizing LiDAR data for the mapping of high value crops and vulnerability assessment."
        layer.keywords.add("PARMap")
        layer.keywords.add("Agriculture")
        layer.keywords.add("Landcover")
        layer.keywords.add("PhilLiDAR2")
        layer.keywords.add("COASTMap")
        layer.keywords.add("Mangrove")
        layer.keywords.add("Aquaculture")


        layer.category = TopicCategory.objects.get(identifier="imageryBaseMapsEarthCover")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_agrilandcover():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='agrilandcover')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").replace("agrilandcover","agricultural landcover").title()
        
        layer.abstract = """Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include initial Land Cover Map of Agricultural Resources.
 
 Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
 Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
 Accuracy and Limitations: The accuracy of the delivered Products ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free."""

        layer.purpose = "Detailed Agricultural Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making. This complements on-going programs of the Department of Agriculture by utilizing LiDAR data for the mapping of high value crops and vulnerability assessment."
        layer.keywords.add("PARMap")
        layer.keywords.add("Agriculture")
        layer.keywords.add("Landcover")
        layer.keywords.add("PhilLiDAR2")

        layer.category = TopicCategory.objects.get(identifier="imageryBaseMapsEarthCover")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_mangroves():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='mangroves')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").title()
        
        layer.abstract = """""Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include extracted mangrove areas from the LiDAR data and/or orthophoto..
 
 Note: Datasets subject to updating. Maps show land cover on date of    data acquisition and may not reflect present land cover. 
 Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
 Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free.""
"""

        layer.purpose = "Detailed Coastal (aquaculture, mangroves) Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making."
        layer.keywords.add("CoastMap")
        layer.keywords.add("Mangroves")
        layer.keywords.add("PhilLiDAR2")

        layer.category = TopicCategory.objects.get(identifier="imageryBaseMapsEarthCover")
        layer.save()
        print "Layer: %s" % layer.name

def pl2_metadata_aquaculture():
    layer_list = []
    layer_list = Layer.objects.filter(name__icontains='aquaculture')
    total_layers = len(layer_list)
    ctr = 0
    for layer in layer_list:
        print "Layer: %s" % layer.name
        #batch_seed(layer)

        layer.title = layer.name.replace("_"," ").title()
        
        layer.abstract = """"Maps prepared by Phil-LiDAR 2 Program B & reviewed by Phil-LiDAR 2 Program A Project 1. The use of the datasets provided herewith are covered by End Users License Agreement (EULA). Shapefiles include extracted aquaculture (fishponds, fish pens, fish traps, fish corrals) from the LiDAR data and/or orthophoto..
 
 Note: Datasets subject to updating. Maps show land cover on date of data acquisition and may not reflect present land cover. 
 Major Source of Information: LiDAR Datasets from DREAM/Phil-LiDAR 1 Program
 Accuracy and Limitations: The accuracy of the delivered Products/ouputs are dependent on the source datasets, and limitations of the software and algorithms used and implemented procedures. The Products are provided "as is" without any warranty of any kind, expressed or implied. Phil-LiDAR 2 Program does not warrant that the Products will meet the needs or expectations of the end users, or that the operations or use of the Products will be error free."
"""

        layer.purpose = "Detailed Coastal (aquaculture, mangroves) Land Cover Maps are needed by Government Agencies and Local Government Units for planning and decision making."
        layer.keywords.add("CoastMap")
        layer.keywords.add("Aquaculture")
        layer.keywords.add("Fish")
        layer.keywords.add("Pens")
        layer.keywords.add("Fish Ponds")
        layer.keywords.add("PhilLiDAR2")

        layer.category = TopicCategory.objects.get(identifier="imageryBaseMapsEarthCover")
        layer.save()
        print "Layer: %s" % layer.name

@task(name='geonode.tasks.update.pl2_metadata_update', queue='update')
def pl2_metadata_update():
    pl2_metadata_agb()
    pl2_metadata_chm()
    pl2_metadata_ccm()
    pl2_metadata_trees()
    pl2_metadata_wetlands()
    pl2_metadata_streams()
    pl2_metadata_irrigation()
    pl2_metadata_agricoastlandcover()
    pl2_metadata_agrilandcover()
    pl2_metadata_mangroves()
    pl2_metadata_aquaculture()

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
