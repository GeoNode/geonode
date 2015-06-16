from django.utils import simplejson as json
from django.http import HttpResponse

from geonode.geoserver.helpers import ogc_server_settings
from geonode.security.views import _perms_info_json


class PrintProxyMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST':
            if 'url' in request.GET and 'pdf' in request.GET['url']:
                print_map(request)


def print_map(request):
    from proxy.views import proxy
    from layers.models import Layer

    permissions = {}
    params = json.loads(request.body)
    for layer in params['layers']:
        if ogc_server_settings.LOCATION in layer['baseURL']:
            for layer_name in layer['layers']:
                layer_obj = Layer.objects.get(typename=layer_name)
                permissions[layer_obj] = _perms_info_json(layer_obj)
                layer_obj.set_default_permissions()
    try:
        resp = proxy(request)
    except Exception:
        return HttpResponse('There was an error connecting to the printing server')
    finally:
        for layer_obj in permissions.keys():
            layer_obj.set_permissions(json.loads(permissions[layer_obj]))

    return resp
