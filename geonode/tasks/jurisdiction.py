import sys
import traceback
from pprint import pprint
from celery.task import task
from django.conf import settings
from geonode.geoserver.helpers import ogc_server_settings
from geonode.layers.models import Layer
from geonode.layers.models import Style
from geonode.datarequests.models import DataRequestProfile
from geonode.datarequests.utils import get_juris_data_size, get_area_coverage, get_shp_ogr
from geoserver.catalog import Catalog


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
        
@task(name='geonode.tasks.jurisdiction.compute_size_update',queue='jurisdiction')
def compute_size_update(requests_query_list, area_compute = True, data_size = True, save=True):
    pprint("Updating requests data size and area coverage")
    if len(requests_query_list) < 1:
        pprint("Requests for update is empty")
    else:
        for r in requests_query_list:
            pprint("Updating request id:{0}".format(r.pk))
            shapefile = get_shp_ogr(r.jurisdiction_shapefile.name)
            if shapefile:
                pprint("Shapefile found")
                if area_compute:
                    r.area_coverage = get_area_coverage(r.jurisdiction_shapefile.name)
                    pprint(r.juris_data_size)
                if data_size:
                    r.juris_data_size = get_juris_data_size(r.jurisdiction_shapefile.name)
                    pprint(r.juris_data_size)
                
                if save:
                    r.save()
