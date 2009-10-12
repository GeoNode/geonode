from geonode.settings import *

GEOSERVER_BASE_URL = "http://localhost:8889/geoserver/"
GEOSERVER_CREDENTIALS = ('admin', 'geoserver')

INSTALLED_APPS += 'capra.hazard', 

TEMPLATE_DIRS = (path_extrapolate("capra/hazard/templates"),) + TEMPLATE_DIRS 

if DEBUG: 
    if MINIFIED_RESOURCES: 
        MEDIA_LOCATIONS["capra_script"] = "/capra_static/CAPRA.js"
    else:
        MEDIA_LOCATIONS["capra_script"] = "/capra_static/src/script/app/loader.js"
else:
    pass
    #TODO: Populate map for production

