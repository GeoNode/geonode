import hashlib

from django.conf import settings
from django.http import QueryDict

TOKEN_KEY_NAME = 'geoconnect_token'

def has_proper_auth(request):
    hash_object = hashlib.sha256(b'Hello World')
    hex_dig = hash_object.hexdigest()
    #print(hex_dig)
    len(hex_dig)
    #64


def has_proper_auth(request):
    """For now, check for DV_TOKEN.
    Future: IP + DV_TOKEN
    Future: oauth
    """
    if not request:
        return False
    
    # Find the token
    if request.POST:
        dv_token = request.POST.get(TOKEN_KEY_NAME, None)
    elif request.GET:
        dv_token = request.GET.get(TOKEN_KEY_NAME, None)
    else:
        return False
    
    if not dv_token == settings.DVN_TOKEN:
        return False

    return True
