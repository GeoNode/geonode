import csv
from django.conf import settings
from django.core.files import File
from django.http import HttpResponse
from django.views.generic import View


try:
    import json
except ImportError:
    from django.utils import simplejson as json


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
    def get(self, request, layername):
        return HttpResponse('Atiq')

    def post(self, request, layername):
        csv_file = File(request.FILES['file']).file
        spamreader = csv.reader(csv_file, delimiter=' ', quotechar='|')
        for row in spamreader:
            print ', '.join(row)

        return HttpResponse({})