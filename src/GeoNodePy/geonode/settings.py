# -*- coding: utf-8 -*-
# Django settings for GeoNode project.

import os
import geonode

# Main GeoNode directory
GEONODE_ROOT = os.path.dirname(geonode.__file__)
# Project directory (where current settings file is)
# Resolve links so it returns actual real path
PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))

###########################################################
# SITE SPECIFIC SETTINGS
# Default to generic, development. Override in settings_local
###########################################################

SITE_ID = 1
SITENAME = "GeoNode"
# Change to actual URL
SITEURL = 'http://localhost:8000/'
ROOT_URLCONF = 'geonode.urls'

# Unique, site specific key used for geoserver password and pw hashing
# Generate new one for production environment using "generate_secret_key" management command
SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'
REGISTRATION_OPEN = False
ACCOUNT_ACTIVATION_DAYS = 7

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# Datastore settings to make geonode upload vector layers directly to postgis
DB_DATASTORE=False
DB_DATASTORE_NAME = ''
DB_DATASTORE_DATABASE = '' #DATABASE_NAME
DB_DATASTORE_USER = '' #DATABASE_USER
DB_DATASTORE_PASSWORD = '' #DATABASE_PASSWORD
DB_DATASTORE_HOST = ''
DB_DATASTORE_PORT = ''
DB_DATASTORE_TYPE='postgis'

# Local time zone for this installation. http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment set to same as your system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation.
LANGUAGE_CODE = 'en'

# ASSETS_ROOT is only used on production servers when using collectstatic command
# it is where all the static and media files are served from
ASSETS_ROOT = '/var/www/geonode/'
# URL to static web server that serves CSS, uploaded media, javascript, etc.
# for serving from same server or in development, use '/'
ASSETS_URL = '/'

# Google API key if using Google maps
GOOGLE_API_KEY = "ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw"

###########################################################
# MODE SPECIFIC SETTINGS
# These settings assume a development environment.
# For production, override these in settings_local
###########################################################

DEBUG = True
TEMPLATE_DEBUG = DEBUG
# This tells the development server to serve static files
SERVE_MEDIA = DEBUG

# Default sqlite3 database (flatfile)
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
# MAP DEFAULTS
###########################################################

DEFAULT_LAYERS_OWNER='admin'
# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (-84.7, 12.8)
# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 7

DEFAULT_LAYER_SOURCE = {
    "ptype":"gxp_wmscsource",
    "url":"/geoserver/wms",
    "restUrl": "/gs/rest"
}

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
# GeoNode specific settings. Rarely should need changing
###########################################################

_ = lambda x: x

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

SOUTH_MIGRATION_MODULES = {
    'registration': 'geonode.migrations.registration',
    'avatar': 'geonode.migrations.avatar',
}

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

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

LANGUAGES = (
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('fr', 'Français'),
    ('el', 'Ελληνικά'),
    ('id', 'Bahasa Indonesia'),
    ('zh', '中國的'),
)

# This isn't required for running the geonode site, but it when running sites that inherit the geonode.settings module.
LOCALE_PATHS = (
    os.path.join(GEONODE_ROOT, "locale"),
    os.path.join(GEONODE_ROOT, "maps", "locale"),
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "geonode.maps.context_processors.resource_urls",
)

# Directories to search for templates
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT,'templates'),  # files common to all sites
    os.path.join(GEONODE_ROOT, 'templates')
)

# Additional directories which hold static files
STATICFILES_DIRS = (
    os.path.join(PROJECT_ROOT, 'static/'), # static is what I like to call it
    os.path.join(GEONODE_ROOT, 'static/')
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

LOGIN_REDIRECT_URL = "/"
AUTHENTICATION_BACKENDS = ('geonode.core.auth.GranularBackend',)
AUTH_PROFILE_MODULE = 'maps.Contact'

def get_user_url(u):
    from django.contrib.sites.models import Site
    s = Site.objects.get_current()
    return "http://" + s.domain + "/profiles/" + u.username

ABSOLUTE_URL_OVERRIDES = {
    'auth.user': get_user_url
}

ADMINS = ()

# The username and password for a user that can add and edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", SECRET_KEY
GEONETWORK_CREDENTIALS = 'admin', 'admin'

###########################################################
# Read in settings_local to override Site and Mode settings
###########################################################

try:
    from local_settings import *
except ImportError:
    pass

###########################################################
# Locations that might have changed after settings_local
###########################################################

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(ASSETS_ROOT,'uploads/')
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = os.path.join(ASSETS_URL,'media/')

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.path.join(ASSETS_ROOT,'static/')

# URL that handles the static files like app media.
STATIC_URL = os.path.join(ASSETS_URL,'static/')
# this needs to be under STATIC_URL
GEONODE_CLIENT_LOCATION = os.path.join(STATIC_URL,'geonode/')

GEONODE_UPLOAD_PATH = MEDIA_ROOT #os.path.join(STATIC_URL, 'uploaded/')

# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = SITEURL + 'geoserver/'
# The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
GEONETWORK_BASE_URL = SITEURL + 'geonetwork/'

# Not sure if this is still used or where
MANAGERS = ADMINS
