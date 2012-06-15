from django.conf import settings
from geonode import get_version

def resource_urls(request):
    return dict(
        STATIC_URL = settings.STATIC_URL,
        GEONODE_CLIENT_LOCATION = settings.GEONODE_CLIENT_LOCATION,
        GEOSERVER_BASE_URL = settings.GEOSERVER_BASE_URL,
        GOOGLE_API_KEY = settings.GOOGLE_API_KEY,
        SITENAME = settings.SITENAME,
        REGISTRATION_OPEN = settings.REGISTRATION_OPEN,
        VERSION = get_version(),
    )
