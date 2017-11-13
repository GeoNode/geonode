from django.conf import settings
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
        from django.core.files import File
        # import pdb;pdb.set_trace()
        print layername, request.FILES
        for l in File(request.FILES['file']).file:
            print l
        # file = File(request.FILES[0]);
        return HttpResponse({})