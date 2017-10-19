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
