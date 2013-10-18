from django.http import HttpResponse
from django.utils import simplejson
from helpers import get_stores
from helpers import gs_slurp
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User

def stores(request, store_type=None):
    stores = get_stores(store_type)
    data = simplejson.dumps(stores)
    return HttpResponse(data)

@user_passes_test(lambda u: u.is_superuser)
def updatelayers(request):
    params = request.REQUEST
    #Get the owner specified in the request if any, otherwise used the logged user
    owner = params.get('owner', None)
    owner = User.objects.get(username=owner) if owner is not None else request.user
    workspace = params.get('workspace', None)
    store = params.get('store',None)
    filter = params.get('filter',None)

    output = gs_slurp(ignore_errors=False, owner=owner, workspace=workspace, store=store, filter=filter)
    return HttpResponse(simplejson.dumps(output))
