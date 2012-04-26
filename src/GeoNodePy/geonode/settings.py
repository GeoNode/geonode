# -*- coding: utf-8 -*-
# Django settings for GeoNode project.
import os
import geonode

# Main GeoNode directory
GEONODE_ROOT = os.path.dirname(geonode.__file__)
# Project directory (where current settings file is)
#  Resolve any links so it returns actual real path
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
print GEONODE_ROOT
print PROJECT_ROOT

###########################################################
# MODE SPECIFIC SETTINGS - PRODUCTION vs DEVELOPMENT
###########################################################

# Production indicates if development server is in use or not
DEVELOPMENT = True

DEBUG = DEVELOPMENT
TEMPLATE_DEBUG = DEBUG

# Default sqlite3 database useful for development
# Override in settings_local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT,'development.db'),
        'USER': '',     # Not used with sqlite
        'PASSWORD': '', # Not used with sqlite
        'HOST': '',     # Not used with sqlite
        'PORT': ''      # Not used with sqlite
    }
}

###########################################################
# SITE SPECIFIC SETTINGS - change for each site
###########################################################

SITE_ID = 1
SITENAME = "GeoNode"
# If DEVELOPMENT=True, SITEURL overridden to http://localhost:8000/
SITEURL = "geonode.domain.com"

ROOT_URLCONF = 'geonode.urls'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'
REGISTRATION_OPEN = False

#Import uploaded shapefiles into a database such as PostGIS?
DB_DATASTORE=False
#Database datastore connection settings
DB_DATASTORE_NAME = ''
DB_DATASTORE_USER = ''
DB_DATASTORE_PASSWORD = ''
DB_DATASTORE_HOST = ''
DB_DATASTORE_PORT = ''
DB_DATASTORE_TYPE=''

# Local time zone for this installation. http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment set to same as your system time zone.
TIME_ZONE = 'America/Chicago'

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS

###########################################################
# LOCATIONS OF THINGS
###########################################################

# For URL's always use trailing slash if there is a path component
# Examples: "http://media.lawrence.com", "http://example.com/media/"

LOGIN_REDIRECT_URL = "/"

# ASSETS_ROOT is only used on production servers when using collectstatic command
ASSETS_ROOT = '/var/www/geonode/'
# URL to static web server that serves CSS, uploaded media, javascript, ec.
ASSETS_URL = '/'

# Media are any files uploaded by users
# Absolute path to the directory that holds media.
MEDIA_ROOT = os.path.join(ASSETS_ROOT, "media")
# URL that handles the media served from MEDIA_ROOT.
MEDIA_URL = os.path.join(ASSETS_URL,'media/')

GEONODE_UPLOAD_PATH = MEDIA_ROOT

# Absolute path to the directory that holds static files
# Example: "/home/media/media.lawrence.com/apps/"
# Not used in production
STATIC_ROOT = os.path.join(ASSETS_ROOT,'static/')
# Additional directories which hold static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static/'),
    os.path.join(GEONODE_ROOT, 'static/')
)
# URL that handles the static files ( http://media.lawrence.com/static/ )
STATIC_URL = os.path.join(ASSETS_URL,'static/')
# this needs to be under STATIC_URL
GEONODE_CLIENT_LOCATION = os.path.join(STATIC_URL,'geonode/')

# Note that Django automatically includes the "templates" dir in all the
# INSTALLED_APPS, se there is no need to add maps/templates or admin/templates
TEMPLATE_DIRS = (
    # Look for templates in Project directory first
    os.path.join(PROJECT_ROOT,"templates"),
    # Then look in GeoNode templates
    os.path.join(GEONODE_ROOT,"templates"),
)

###########################################################
# MAP DEFAULTS
###########################################################

DEFAULT_LAYERS_OWNER='admin'

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (-84.7, 12.8)

# 0 = entire world; maximum zoom 12 - 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 7

DEFAULT_LAYER_SOURCE = {
    "ptype":"gxp_wmscsource",
    "url":"/geoserver/wms",
    "restUrl": "/gs/rest"
}

GOOGLE_API_KEY = "ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw"

MAP_BASELAYERS = [{
    "source": {"ptype": "gx_olsource"},
    "type":"OpenLayers.Layer",
    "args":["No background"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  },{
    "source": { "ptype":"gx_olsource"},
    "type":"OpenLayers.Layer.OSM",
    "args":["OpenStreetMap"],
    "visibility": True,
    "fixed": True,
    "group":"background"
  },{
    "source": {"ptype":"gx_olsource"},
    "type":"OpenLayers.Layer.WMS",
    "group":"background",
    "visibility": False,
    "fixed": True,
    "args":[
      "bluemarble",
      "http://maps.opengeo.org/geowebcache/service/wms",
      {
        "layers":["bluemarble"],
        "format":"image/png",
        "tiled": True,
        "tilesOrigin":[-20037508.34,-20037508.34]
      },
      {"buffer":0}
    ]
}]

###########################################################
# GEONODE SPECIFIC SETTINGS - unlikely to require changing
###########################################################

_ = lambda x: x

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
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

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django_extensions',
    'registration',
    'profiles',
    'avatar',
    'south',
    'geonode.core',
    'geonode.maps',
    'geonode.proxy',
    'geonode'
)

# Setting a custom test runner to avoid running the tests for some problematic 3rd party apps
TEST_RUNNER='django_nose.NoseTestSuiteRunner'

NOSE_ARGS = [
      '--verbosity=2',
      '--cover-erase',
      '--nocapture',
      '--with-coverage',
      '--cover-package=geonode',
      '--cover-inclusive',
      '--cover-tests',
      '--detailed-errors',
      '--with-xunit',
# This is very beautiful/usable but requires: pip install rudolf
#      '--with-color',
# The settings below are useful while debugging test failures or errors
#      '--failed',
#      '--pdb-failures',
#      '--stop',
#      '--pdb',
      ]

SOUTH_MIGRATION_MODULES = {
    'registration': 'geonode.migrations.registration',
    'avatar': 'geonode.migrations.avatar',
}

# This isn't required for running the geonode site, but it when running sites that inherit the geonode.settings module.
LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, "locale"),
    os.path.join(PROJECT_ROOT, "maps", "locale"),
)

AUTHENTICATION_BACKENDS = ('geonode.core.auth.GranularBackend',)

def get_user_url(u):
    from django.contrib.sites.models import Site
    s = Site.objects.get_current()
    return "http://" + s.domain + "/profiles/" + u.username

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': get_user_url
}

AUTH_PROFILE_MODULE = 'maps.Contact'

if DEVELOPMENT:
    SITEURL = 'http://localhost:8000/'

# The settings here require a proxy to be set up for both GeoServer and GeoNetwork
# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = SITEURL + "/geoserver/"
# Default password for the geoserver admin user, autogenerated during bootstrap
GEOSERVER_TOKEN = open(os.path.join(PROJECT_ROOT,"..","..", "..","geoserver_token")).readline()[0:-1]
# The username and password for a user that can add and edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", GEOSERVER_TOKEN

# The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
GEONETWORK_BASE_URL = SITEURL + "/geonetwork/"
# The username and password for a user with write access to GeoNetwork
GEONETWORK_CREDENTIALS = "admin", "admin"

# Serves static files in development
# SERVE_MEDIA is used with the dev server to serve static files
SERVE_MEDIA = DEVELOPMENT

###########################################################
# INTERNATIONALIZATION
###########################################################

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('fr', 'Français'),
    ('de', 'Deutsch'),
    ('el', 'Ελληνικά'),
    ('id', 'Bahasa Indonesia'),
    ('zh', '中國的'),
)

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

try:
    from local_settings import *
except ImportError:
    pass