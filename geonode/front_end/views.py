import csv
import logging
try:
    import json
except ImportError:
    from django.utils import simplejson as json

from django.conf import settings
from django.core.files import File
from django.http import HttpResponse
from django.views.generic import View
from geonode.class_factory import ClassFactory
from geonode.layers.models import Layer
from geonode.layers.views import _resolve_layer


db_logger = logging.getLogger('db')


class GeoserverSettings (View):
    '''
    This is a view to retrieve Geoserver Settings
    '''
    def get(self, request):
        return HttpResponse(json.dumps(
            {'url': getattr(settings, 'GEOSERVER_LOCATION', None)},
            ensure_ascii=False),
            content_type='application/javascript')


class LayerAttributeUploadView(View):
    '''
    This class will process a csv file for a layer attribute
    '''
    def post(self, request, layername):
        layer_obj = _resolve_layer(request, layername)
        factory = ClassFactory()
        model_instance = factory.get_model(name=str(layer_obj.title_en), table_name=str(layer_obj.name), db=str(layer_obj.store))
        csv_file = File(request.FILES['file']).file
        csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
        headers = csv_reader.next()
        headers = [h.lower().replace(' ', '_') for h in headers]
        success_count, failed_count = 0, 0
        for row in csv_reader:
            row = dict(zip(headers, row))
            try:
                obj = model_instance(**row)
                obj.save()
                success_count += 1
            except Exception as ex:
                db_logger.exception(ex)
                failed_count += 1
        
        return HttpResponse(
                    json.dumps(
                        dict(success=success_count, failed=failed_count),
                        ensure_ascii=False), 
                    content_type='application/javascript')
    