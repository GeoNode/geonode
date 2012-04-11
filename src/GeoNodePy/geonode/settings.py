# -*- coding: utf-8 -*-
# Django settings for GeoNode project.
from urllib import urlencode
import logging
import os


_ = lambda x: x

DEBUG = True
SITENAME = "WorldMap"
SITEURL = "http://localhost:8000/"
#TEMPLATE_DEBUG = DEBUG
TEMPLATE_DEBUG = True
DEFAULT_FROM_EMAIL="me@me.com"
NO_REPLY_EMAIL = "do-not-reply@worldmap.harvard.edu"

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

#Email settings (example gmail account) for registration, passwords, etc
#DEFAULT_FROM_EMAIL = 'your_email@gmail.com'
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_HOST_USER = 'your_email@gmail.com'#EMAIL_HOST_PASSWORD = 'password'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True

# FILE_UPLOAD_HANDLERS is only necessary if you want to track upload
# progress in your Django app -- if you have a front-end proxy like
# nginx or lighttpd, Django doesn't need to be involved in the upload
# tracking.
#FILE_UPLOAD_HANDLERS = ('geonode.maps.upload_handlers.UploadProgressCachedHandler',
#                        'django.core.files.uploadhandler.MemoryFileUploadHandler',
#'django.core.files.uploadhandler.TemporaryFileUploadHandler',)


MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(PROJECT_ROOT,"..","..","..","development.db")
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Not used with sqlite3.
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
    ('en', 'English'),
    ('es', 'Español'),
    ('it', 'Italiano'),
    ('fr', 'Français'),
    ('el', 'Ελληνικά'),
    ('id', 'Bahasa Indonesia'),
    ('zh', '中國的'),
)

SITE_ID = 1

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

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/site_media/media/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "media", "static")

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/media/"

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "media"),
]

GEONODE_UPLOAD_PATH = os.path.join(STATIC_URL, "upload/")

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = os.path.join(STATIC_URL, "admin/")

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    #'django.template.loaders.eggs.load_template_source',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "geonode.maps.context_processors.resource_urls",
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

#This is only required for the Django Debug Toolbar
INTERNAL_IPS = ('127.0.0.1',)

# This isn't required for running the geonode site, but it when running sites that inherit the geonode.settings module.
LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, "locale"),
    os.path.join(PROJECT_ROOT, "maps", "locale"),
)

ROOT_URLCONF = 'geonode.urls'

# Note that Django automatically includes the "templates" dir in all the
# INSTALLED_APPS, se there is no need to add maps/templates or admin/templates
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT,"templates"),    
)

# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = "http://localhost:8001/geoserver/"

# Default password for the geoserver admin user, autogenerated during bootstrap
GEOSERVER_TOKEN = open(os.path.join(PROJECT_ROOT,"..","..", "..","geoserver_token")).readline()[0:-1]

# The username and password for a user that can add and edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", GEOSERVER_TOKEN

# The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
GEONETWORK_BASE_URL = "http://localhost:8001/geonetwork/"

# The username and password for a user with write access to GeoNetwork
GEONETWORK_CREDENTIALS = "admin", "admin"

AUTHENTICATION_BACKENDS = ('geonode.core.auth.GranularBackend',)

GOOGLE_API_KEY = "ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw"
GOOGLE_ANALYTICS_ID = "UA-XXXXXXXX-1"


LOGIN_REDIRECT_URL = "/"

DEFAULT_LAYERS_OWNER='admin'

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (0,0)

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 2

DEFAULT_LAYER_SOURCE = {
    "ptype":"gxp_gnsource",
    "url":"/geoserver/wms",
    "restUrl": "/gs/rest"
}

MAP_BASELAYERS = [
        {
        "source":{"ptype": "gx_googlesource"},
        "group":"background",
        "name":"SATELLITE",
        "visibility": False,
        "fixed": True,
        },
        {
        "source":{"ptype": "gx_googlesource"},
        "group":"background",
        "name":"TERRAIN",
        "visibility": True,
        "fixed": True,
        },            {
        "source":{"ptype": "gx_googlesource"},
        "group":"background",
        "name":"ROADMAP",
        "visibility": False,
        "fixed": True,
        },
        {
        "source":{"ptype": "gx_googlesource"},
        "group":"background",
        "name":"HYBRID",
        "visibility": False,
        "fixed": True,
        },
        {
        "source": {"url": "http://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer", "ptype": "gxp_arcrestsource"},
        "group":"background",
        "name":"World Imagery",
        "visibility": False,
        "fixed": True,
        "title": "ESRI World Imagery"
    },
        {
        "source":{"ptype": "gx_olsource"},
        "type":"OpenLayers.Layer.OSM",
        "args":["OpenStreetMap"],
        "visibility": False,
        "fixed": True,
        "group":"background"
    }]


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'staticfiles',
    'django_extensions',
    'registration',
    'profiles',
    'avatar',
    'south',
    'geonode.core',
    'geonode.maps',
    'geonode.proxy',
    'geonode',
    'geonode.registration',
    'geonode.profiles',
    #'debug_toolbar',
)

def get_user_url(u):
    from django.contrib.sites.models import Site
    s = Site.objects.get_current()
    return "http://" + s.domain + "/profiles/" + u.username


ABSOLUTE_URL_OVERRIDES = {
    'auth.user': get_user_url
}

AUTH_PROFILE_MODULE = 'maps.Contact'
REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 30
SERVE_MEDIA = DEBUG;

#GEONODE_CLIENT_LOCATION = "http://localhost:8001/geonode-client/"
GEONODE_CLIENT_LOCATION = "/media/static/"


#Google Analytics
#Make this code an empty string if you DONT intend to use it;
# if you do use it replace UA-XXXXXXXX-1 with your own ID
GOOGLE_ANALYTICS_CODE = ""

#Set name of additional permissions group (besides anonymous and authenticated)
CUSTOM_GROUP_NAME = 'Organization Users'

#If you want to redirect members of your organization to a separate authentication system when registering, change the following settings
USE_CUSTOM_ORG_AUTHORIZATION = False
CUSTOM_ORG_AUTH_TEXT = 'Are you affiliated with XXXX?'
#Automatically add users with the following email address suffix to the custom group, if created via layer/map permissions
CUSTOM_GROUP_EMAIL_SUFFIX = ''
#URL to redirect to if user indicates they are a member of your organization
CUSTOM_AUTH_URL = ''


#Import uploaded shapefiles into a database such as PostGIS?
DB_DATASTORE=False

#Database datastore connection settings
DB_DATASTORE_DATABASE = ''
DB_DATASTORE_NAME = ''
DB_DATASTORE_USER = ''
DB_DATASTORE_PASSWORD = ''
DB_DATASTORE_HOST = ''
DB_DATASTORE_PORT = ''
DB_DATASTORE_TYPE=''

SOUTH_MIGRATION_MODULES = {
}

DEFAULT_WORKSPACE = 'geonode'

HGL_VALIDATION_KEY='Contact Harvard Geospatial Library to request the validation key'
CACHE_BACKEND = 'dummy://'


### Boston neighborhood settings  ###
### These need to be set to the correct values for the worldmap instance ###
HOODS_TEMPLATE_LAYER = 'boston_census_block_neighborhoods' # layer name in geoserver
HOODS_TEMPLATE_ID = 188  #Map id to be used as template
HOODS_TEMPLATE_ATTRIBUTE = 'GEOID10'  #Attribute to be used for block id

DB_GAZETTEER_TABLE = "worldmap_gazetteer"

try:
    from local_settings import *
except ImportError:
    pass
