from django.conf import settings

def resource_urls(request): 
    return dict(
        GEOSERVER_BASE_URL = settings.GEOSERVER_BASE_URL,
        GOOGLE_API_KEY = settings.GOOGLE_API_KEY,
        SITENAME = settings.SITENAME,
        REGISTRATION_OPEN = settings.REGISTRATION_OPEN,
    )
