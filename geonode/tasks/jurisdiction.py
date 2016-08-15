import sys
<<<<<<< HEAD
import traceback
=======
>>>>>>> 91ffe6754782f2404e2097953fe0130bf92546a1
from pprint import pprint
from celery.task import task
from geonode.geoserver.helpers import ogc_server_settings
from geonode.layers.models import Layer
from geonode.layers.models import Style
from geoserver.catalog import Catalog


@task(name='geonode.tasks.jurisdiction.jurisdiction_style', queue='jurisdiction')
def jurisdiction_style(layer):
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
