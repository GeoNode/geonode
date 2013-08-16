from django.http import HttpResponse
from django.utils import simplejson
from helpers import get_stores

def stores(request, store_type=None):
    stores = get_stores(store_type)
    data = simplejson.dumps(stores)
    return HttpResponse(data)
