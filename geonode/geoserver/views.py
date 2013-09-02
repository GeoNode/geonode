from django.http import HttpResponse
from django.utils import simplejson
from helpers import get_stores
from helpers import gs_slurp
from django.contrib.auth.decorators import user_passes_test

def stores(request, store_type=None):
    stores = get_stores(store_type)
    data = simplejson.dumps(stores)
    return HttpResponse(data)

@user_passes_test(lambda u: u.is_superuser)
def updatelayers(request):
    params = request.REQUEST
    user = params.get('user',None)
    workspace = params.get('workspace', None)
    store = params.get('store',None)
    layer = params.get('layer',None)

    output = gs_slurp(ignore_errors=False, owner=user, workspace=workspace, store=store, filter=layer)
    return HttpResponse(simplejson.dumps(output))