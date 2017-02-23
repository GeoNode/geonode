import sys
import traceback
from pprint import pprint
from celery.task import task
from django.conf import settings
from geonode.geoserver.helpers import ogc_server_settings

from geonode.layers.models import Style
from geoserver.catalog import Catalog
from geonode.layers.models import Layer
from geonode.datarequests.models import DataRequestProfile
#from geonode.datarequests.utils2 import get_shp_ogr, assign_grid_refs, get_juris_data_size
from geonode.datarequests.utils import  get_place_name, get_area_coverage

@task(name='geonode.tasks.jurisdiction.jurisdiction_style', queue='jurisdiction')
def jurisdiction_style(saved_layer):
    try:
        pprint("saved jurisdiction; updating style on geonode ")
        def_style = Style.objects.get(name="Boundary")
        saved_layer.styles.add(def_style)
        saved_layer.default_style=def_style
        saved_layer.is_published = False
        saved_layer.save()
        interest_layer =  saved_layer
        pprint("updated style on geonode; updating style on geoserver")

        cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + 'rest',
            username=settings.OGC_SERVER['default']['USER'],
            password=settings.OGC_SERVER['default']['PASSWORD'])

        boundary_style = cat.get_style('Boundary')
        gs_layer = cat.get_layer(saved_layer.name)
        if boundary_style:
            gs_layer._set_default_style(boundary_style)
            cat.save(gs_layer) #save in geoserver
            saved_layer.sld_body = boundary_style.sld_body
            saved_layer.save() #save in geonode
        pprint("updated style on geoserver")
    except Exception as e:
        exception_type, error, tb = sys.exc_info()
        print traceback.format_exc()

@task(name='geonode.tasks.jurisdiction.place_name_update', queue='jurisdiction')
def  place_name_update(requests_query_list, save=True):
    if len(requests_query_list) < 1:
        pprint("Requests for update is empty")
    else:
        for r in requests_query_list:
            pprint("Updating request id:{0}".format(r.pk))
            jurisdiction = r.jurisdiction_shapefile
            if jurisdiction:
                x = (jurisdiction.bbox_x1+jurisdiction.bbox_x0)/2
                y = (jurisdiction.bbox_y1+jurisdiction.bbox_y0)/2
                r.place_name = get_place_name(x,y)["county"]
                pprint("Place name is: {}".format(r.place_name))
                
                if save:
                    r.save()
