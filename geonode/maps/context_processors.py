from django.conf import settings
from geonode import get_version

def resource_urls(request):
    return dict(
        STATIC_URL = settings.STATIC_URL,
        SITE_URL = settings.SITEURL,
        GEONODE_CLIENT_LOCATION = settings.GEONODE_CLIENT_LOCATION,
        GEOSERVER_BASE_URL = settings.GEOSERVER_BASE_URL,
        GOOGLE_API_KEY = settings.GOOGLE_API_KEY,
        GOOGLE_ANALYTICS_CODE = settings.GOOGLE_ANALYTICS_CODE,
        SITENAME = settings.SITENAME,
        REGISTRATION_OPEN = settings.REGISTRATION_OPEN,
        VERSION = get_version(),
        CUSTOM_GROUP_NAME = settings.CUSTOM_GROUP_NAME if settings.USE_CUSTOM_ORG_AUTHORIZATION else '',
        USE_CUSTOM_ORG_AUTHORIZATION = settings.USE_CUSTOM_ORG_AUTHORIZATION,
        USE_GAZETTEER = settings.USE_GAZETTEER,
    )
