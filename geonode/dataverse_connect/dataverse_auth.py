import hashlib

from django.conf import settings
from django.http import QueryDict
import logging
TOKEN_KEY_NAME = 'geoconnect_token'

#def has_proper_auth(request):
#    hash_object = hashlib.sha256(b'Hello World')

logger = logging.getLogger("geonode.dataverse_connect.dataverse_auth")

def xhas_proper_auth(request):
    """For now, check for DV_TOKEN.
    Future: IP + DV_TOKEN
    Future: oauth
    """
    #logger.info('----- has_proper_auth? -----')

    if not request:
        #logger.info('----- not request -----')

        return False
    
    # Find the token
    if request.POST:
        dv_token = request.POST.get(TOKEN_KEY_NAME, None)
    elif request.GET:
        dv_token = request.GET.get(TOKEN_KEY_NAME, None)
    else:
        return False

    #logger.info('req: "%s"  equal to wm: "%s"' % (dv_token, settings.WORLDMAP_TOKEN_FOR_DATAVERSE) )

    if not dv_token == settings.WORLDMAP_TOKEN_FOR_DATAVERSE:
        return False

    return True
