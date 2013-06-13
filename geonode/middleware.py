from django.conf import settings
from django.utils import simplejson as json

from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS

class PrintProxyMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST':
            if request.GET.has_key('url') and 'pdf' in request.GET['url']:
                print_map(request)

def print_map(request):
    from django.conf import settings
    from proxy.views import proxy
    from layers.models import Layer

    permissions = {}
    params = json.loads(request.body)
    for layer in params['layers']:
        if settings.GEOSERVER_BASE_URL in layer['baseURL']:
            for layer_name in layer['layers']:
                layer_obj = Layer.objects.get(typename=layer_name)
                permissions[layer_obj] = {}
                permissions[layer_obj]['anonymous'] = layer_obj.get_gen_level(ANONYMOUS_USERS)
                permissions[layer_obj]['authenticated'] = layer_obj.get_gen_level(AUTHENTICATED_USERS)
                layer_obj.set_gen_level(ANONYMOUS_USERS,'layer_readonly')
    try:
        resp =  proxy(request)
    except Exception, e:
        return HttpResponse('There was an error connecting to the printing server')
    finally:
        for layer_obj in permissions.keys():
            perm_spec = permissions[layer_obj]
            layer_obj.set_gen_level(ANONYMOUS_USERS,perm_spec['anonymous'])
            layer_obj.set_gen_level(AUTHENTICATED_USERS,perm_spec['authenticated'])

    return resp
