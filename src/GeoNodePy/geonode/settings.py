# Django settings for GeoNode project.
from utils import path_extrapolate
from urllib import urlencode
import logging

LOG_FILENAME='/Users/mbertrand/Development/googlecode/cga-worldmap/geonode.log'
logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s %(levelname)s %(message)s',filename = LOG_FILENAME,filemode = 'w')

_ = lambda x: x

DEBUG = True
SITENAME = "WorldMap"
SITEURL = "http://localhost:8000/"
TEMPLATE_DEBUG = DEBUG


ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

#DATABASE_ENGINE = 'sqlite3'
#DATABASE_NAME = '/home/matt/installs/geonode/src/GeoNodePy/geonode/development.db'
DATABASE_ENGINE = 'django.db.backends.postgresql_psycopg2'
DATABASE_NAME = 'gisdb'
DATABASE_USER = 'africamaps'             # Not used with sqlite3.
DATABASE_PASSWORD = 'j0kerz'         # Not used with sqlite3.
DATABASE_HOST = 'localhost'             # Not used with sqlite3.
DATABASE_PORT = '5432'             # Not used with sqlite3.
#DATABASE_USER = ''             # Not used with sqlite3.
#DATABASE_PASSWORD = ''         # Not used with sqlite3.
#DATABASE_HOST = ''             # Not used with sqlite3.
DATABASE_PORT = ''             # Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', _('English')),
    ('es', _('Spanish')),
)

SITE_ID = 1

# Setting a custom test runner to avoid running the tests for some problematic 3rd party apps
TEST_RUNNER='geonode.testrunner.GeoNodeTestRunner'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'http://localhost:8001/geoserver/www/'

GEONODE_UPLOAD_PATH = path_extrapolate('../../gs-data/www')

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "geonode.maps.context_processors.resource_urls",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

# This isn't required for running the geonode site, but it when running sites that inherit the geonode.settings module.
LOCALE_PATHS = (
    path_extrapolate('geonode/locale'),
    path_extrapolate('geonode/maps/locale'),
)

ROOT_URLCONF = 'geonode.urls'

TEMPLATE_DIRS = path_extrapolate('geonode/templates'), \
                path_extrapolate('geonode/maps/templates'), \
                path_extrapolate('django/contrib/admin/templates', 'django'),



# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = "http://localhost:8001/geoserver/"

# The username and password for a user that can add and edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", open(path_extrapolate('../../geoserver_token')).readline()[0:-1]

# The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
GEONETWORK_BASE_URL = "http://localhost:8001/geonetwork/"

# The username and password for a user with write access to GeoNetwork
GEONETWORK_CREDENTIALS = "admin", "admin"

AUTHENTICATION_BACKENDS = ('geonode.core.auth.GranularBackend',)

GOOGLE_API_KEY = "ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw"
LOGIN_REDIRECT_URL = "/"

DEFAULT_LAYERS_OWNER='admin'

MAP_BASELAYERSOURCES = {
    "any": {
        "ptype":"gx_olsource"
    },
    "google":{
        "ptype":"gx_googlesource",
        "apiKey": GOOGLE_API_KEY
    }
}

MAP_BASELAYERS = [{
    "source":"any",
    "type":"OpenLayers.Layer",
    "args":["No background"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  },{
    "source":"any",
    "type":"OpenLayers.Layer.OSM",
    "args":["OpenStreetMap"],
    "visibility": True,
    "fixed": True,
    "group":"background"
  },{
    "source":"google",
    "group":"background",
    "name":"SATELLITE",
    "visibility": False,
    "fixed": True,
}]

# NAVBAR expects a dict of dicts or a path to an ini file
#NAVBAR = path_extrapolate('geonode/core/templatetags/navbar.ini')
NAVBAR = \
{'maps': {'id': '%sLink',
               'item_class': '',
               'link_class': '',
               'text': 'Create Your Own Map View',
               'url': "geonode.maps.views.newmap"},
#  'index': {'id': '%sLink',
#            'item_class': '',
#            'link_class': '',
#            'text': 'Featured Map',
#            'url': 'geonode.views.index'},
 'master': {'id': '%sLink',
            'item_class': '',
            'link_class': '',
            'text': 'This page has no tab for this navigation'},
 'meta': {'active_class': 'here',
          'default_id': '%sLink',
          'default_item_class': '',
          'default_link_class': '',
          'end_class': 'last',
          'id': '%sLink',
          'item_class': '',
          'link_class': '',
          'visible': 'maps'}}


# Determines whether the minified or the "raw" JavaScript files are included.
# Only applies in development mode. (That is, when DEBUG==True)
#MINIFIED_RESOURCES = False
MINIFIED_RESOURCES = False

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_extensions',
    'registration',
    'profiles',
    'avatar',
    'geonode.core',
    'geonode.maps',
    'geonode.proxy',
    'geonode.sites',
)

AUTH_PROFILE_MODULE = 'maps.Contact'
REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 7
GEONODE_CLIENT_LOCATION = "http://localhost:8000"

SERVE_MEDIA = True;

try:
    from local_settings import *
except ImportError:
    pass

if SERVE_MEDIA:
    if MINIFIED_RESOURCES: 
        MEDIA_LOCATIONS = {
            "ext_base": "/static/ext/",
            "ext_lib": "/static/ext/ext-all.js",
            "ol_theme": "/static/ol/theme/default/style.css",
            "ol_script":"/static/ol/OpenLayers.js",
            "gx_themes":"/static/gx/theme/",
            "gx_script":"/static/gx/GeoExt.js",
            "PrintPreview_script":"/static/PrintPreview/PrintPreview.js",
            "PrintPreview_themes": "/static/PrintPreview/theme/",
            "gxp_script":"/static/gxp/gxp.js",
            "gxp_theme":"/static/gxp/theme/all.css",
            "geo_script":"/static/gn/GeoExplorer.js",
            "app_themes": "/static/gn/theme/app/",
            "app_script":"/static/gn/GeoNode.js",
            "ux_script":"/static/gn/ux.js",
            "ux_resources":"/static/gn/ux/",
        }                
    else:
        MEDIA_LOCATIONS = {
            "ext_base": "/static/externals/ext/",
            "ext_lib": "/static/externals/ext/ext-all-debug.js",
            "ol_theme": "/static/externals/openlayers/theme/default/style.css",
            "ol_script":"/static/externals/openlayers/lib/OpenLayers.js",
            "gx_themes":"/static/externals/geoext/geoext/resources/",
            "gx_script":"/static/externals/geoext/geoext/lib/GeoExt.js",
            "PrintPreview_script":"/static/externals/PrintPreview/lib/GeoExt.ux/PrintPreview.js",
            "PrintPreview_themes": "/static/externals/PrintPreview/resources/",
            "gxp_script":"/static/externals/gxp/src/script/loader.js",
            "gxp_theme":"/static/externals/gxp/src/theme/all.css",
            "geo_script":"/static/src/script/app/geo-debug.js",
            "app_themes": "/static/src/theme/app/",
            "app_script":"/static/src/script/app/app-debug.js",
            "ux_script":"/static/src/script/ux/loader.js",
            "ux_resources":"/static/src/script/ux/",
        }
else:
    MEDIA_LOCATIONS = {
        "ext_base": GEONODE_CLIENT_LOCATION + "/geonode-client/ext/",
        "ext_lib": GEONODE_CLIENT_LOCATION + "/geonode-client/ext/ext-all.js",
        "ol_theme":  GEONODE_CLIENT_LOCATION + "/geonode-client/ol/theme/default/style.css",
        "ol_script": GEONODE_CLIENT_LOCATION + "/geonode-client/ol/OpenLayers.js",
        "gx_themes": GEONODE_CLIENT_LOCATION + "/geonode-client/gx/theme/",
        "gx_script": GEONODE_CLIENT_LOCATION + "/geonode-client/gx/GeoExt.js",
        "PrintPreview_script": GEONODE_CLIENT_LOCATION + "/geonode-client/PrintPreview/PrintPreview.js",
        "PrintPreview_themes": GEONODE_CLIENT_LOCATION + "/geonode-client/PrintPreview/theme/",
        "gxp_script": GEONODE_CLIENT_LOCATION + "/geonode-client/gxp/gxp.js",
        "gxp_theme": GEONODE_CLIENT_LOCATION + "/geonode-client/gxp/theme/all.css",
        "geo_script": GEONODE_CLIENT_LOCATION + "/geonode-client/gn/GeoExplorer.js",
        "app_themes": GEONODE_CLIENT_LOCATION + "/geonode-client/gn/theme/app/",
        "app_script": GEONODE_CLIENT_LOCATION + "/geonode-client/gn/GeoNode.js",
        "ux_script": GEONODE_CLIENT_LOCATION + "/geonode-client/gn/ux.js",
        "ux_resources": GEONODE_CLIENT_LOCATION + "/geonode-client/gn/ux/",
    }
