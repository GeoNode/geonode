# flake8: noqa
##### Settings to be included last

###############################################
# Master Geosite settings
# These settings are called at/near the end of a GeoSite settings
# to finalize some derived settings
###############################################

# geonode local_settings
try:
    # load in local_settings from system installed geonode
    execfile(os.path.join(GEONODE_ROOT, 'local_settings.py'))
except:
    # there are no system geonode local_settings to import
    pass

# master local_settings
try:
    # load in local_settings (usually for setting SITEURL and DATABASES for production)
    execfile(os.path.join(SITE_ROOT, '../', 'local_settings.py'))
except:
    # there are no master local_settings to import
    pass

# site local_settings
try:
    # load in local_settings (usually for setting SITEURL and DATABASES for production)
    execfile(os.path.join(SITE_ROOT, 'local_settings.py'))
except:
    # there are no site local_settings to import
    pass

OGC_SERVER['default']['LOCATION'] = GEOSERVER_URL
OGC_SERVER['default']['PUBLIC_LOCATION'] = os.path.join(SITEURL, 'geoserver/')
CATALOGUE['default']['URL'] = '%scatalogue/csw' % SITEURL
PYCSW['CONFIGURATION']['metadata:main']['provider_url'] = SITEURL
LOCAL_GEOSERVER['source']['url'] = OGC_SERVER['default']['PUBLIC_LOCATION'] + 'wms'

# Directories to search for templates
TEMPLATE_DIRS = (
    os.path.join(SITE_ROOT, 'templates/'),
    os.path.join(GEOSITES_ROOT, 'templates/'),
    os.path.join(GEONODE_ROOT, 'templates/'),
)

# Directories which hold static files
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'static/'),
    os.path.join(GEOSITES_ROOT, 'static/'),
    os.path.join(GEONODE_ROOT, 'static/')
)

# Update databases if site has own database
if SITE_DATABASES:
    DATABASES.update(SITE_DATABASES)

# Update apps if site has own apps
if SITE_APPS:
	INSTALLED_APPS += SITE_APPS

# Put static files in root
STATIC_ROOT = os.path.join(SERVE_PATH, 'static')

# Put media files in root
MEDIA_ROOT = os.path.join(SERVE_PATH, 'uploaded')

OGC_SERVER['default']['LOCATION'] = os.path.join(GEOSERVER_URL, 'geoserver/')


# add datastore if defined
if DATASTORE in DATABASES.keys():
    OGC_SERVER['default']['DATASTORE'] = DATASTORE


# If using nginx/gunicorn this should be added
# add gunicorn logging
# LOGGING['handlers']['gunicorn'] = {
#     'level': 'DEBUG',
#     'class': 'logging.handlers.RotatingFileHandler',
#     'formatter': 'verbose',
#     'filename': '/geo/logs/gunicorn.errors',
# }
# LOGGING['loggers']['gunicorn'] = {
#     'level': 'DEBUG',
#     'handlers': ['gunicorn'],
#     'propagate': True,
# }

# DEBUG_TOOLBAR can interfere with Django - keep it off until needed
if DEBUG_TOOLBAR:
    DEBUG_TOOLBAR_PATCH_SETTINGS = False
    def show_if_superuser(request):
        return True if request.user.is_superuser else False
    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar',)
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        'SHOW_TOOLBAR_CALLBACK': 'cdesign.settings.show_if_superuser',
    }
