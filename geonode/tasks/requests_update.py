from geonode.geoserver.helpers import ogc_server_settings
from pprint import pprint
from celery.task import task
from geonode import settings
from geonode.layers.models import Layer
from geonode.datarequests.models import DataRequestProfile
from geonode.datarequests.utils import get_shp_ogr, get_area_coverage,  get_juris_data_size, get_place_name

@task(name='geonode.tasks.requests_update.compute_size_update', queue='requests_update')
def compute_size_update(requests_query_list, area_compute = True, data_size = True, save=True):
    pprint("Updating requests data size and area coverage")
    if len(requests_query_list) < 1:
        pprint("Requests for update is empty")
    else:
        for r in requests_query_list:
            pprint("Updating request id:{0}".format(r.pk))
            shapefile = get_shp_ogr(r.jurisdiction_shapefile.name)
            if shapefile:
                if area_compute:
                    r.area_coverage = get_area_coverage(shapefile)
                if data_size:
                    r.juris_data_size = get_juris_data_size(shapefile)
                
                if save:
                    r.save()

@task(name='geonode.tasks.requests_update.place_name_update', queue='requests_update')
def  place_name_update(requests_query_list):
    if len(requests_query_list) < 1:
        pprint("Requests for update is empty")
    else:
        for r in requests_query_list:
            pprint("Updating request id:{0}".format(r.pk))
            
