from django.conf import settings

def resource_urls(request): 
    return {
        "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL,
        "GOOGLE_API_KEY": settings.GOOGLE_API_KEY,
        "MEDIA_LOCATIONS": settings.MEDIA_LOCATIONS
    }
