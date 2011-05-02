# Django settings for GeoNode project.
from urllib import urlencode
import logging
import os

logging.basicConfig(level = logging.DEBUG,format = '%(asctime)s %(levelname)s %(message)s',filename = 'geonode.log',filemode = 'w')

_ = lambda x: x

DEBUG = True
SITENAME = "WorldMap"
SITEURL = "http://localhost:8000/"
#TEMPLATE_DEBUG = DEBUG
TEMPLATE_DEBUG = True
DEFAULT_FROM_EMAIL="me@me.com"

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
#     'django.template.loaders.eggs.load_template_source',
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
)

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

MAP_BASELAYERSOURCES = {
    "any": {
        "ptype":"gx_olsource"
    },
    "capra": {
        "url":"/geoserver/wms"
    },
    "google":{
        "ptype":"gx_googlesource",
        "apiKey": GOOGLE_API_KEY
    }
}

MAP_BASELAYERS = [
{
    "source":"any",
    "type":"OpenLayers.Layer",
    "args":["No background"],
    "visibility": True,
    "fixed": False,
    "group":"background"
  },
 {
    "source":"google",
    "group":"background",
    "name":"SATELLITE",
    "visibility": False,
    "fixed": True,
},{
    "source":"google",
    "group":"background",
    "name":"TERRAIN",
    "visibility": True,
    "fixed": True,
},            {
    "source":"google",
    "group":"background",
    "name":"ROADMAP",
    "visibility": False,
    "fixed": True,
},{
    "source":"google",
    "group":"background",
    "name":"HYBRID",
    "visibility": False,
    "fixed": True,
},{
    "source":"any",
    "type":"OpenLayers.Layer.OSM",
    "args":["OpenStreetMap"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  }]

# NAVBAR expects a dict of dicts or a path to an ini file
NAVBAR = \
{'maps': {'id': '%sLink',
               'item_class': '',
               'link_class': '',
               'text': 'Create Your Own Map',
               'url': "geonode.maps.views.newmap"},
'help': {'id': '%sLink',
               'item_class': '',
               'link_class': '',
               'text': 'Help',
               'url': "geonode.views.static 'help'"},      
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
          'visible': 'maps\nhelp'}}

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'staticfiles',
    'django_extensions',
    'registration',
    'profiles',
    'avatar',
    'geonode.core',
    'geonode.maps',
    'geonode.proxy',
    'geonode.accountforms',
    'geonode.profileforms',
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
#URL to redirect to if user indicates they are a member of your organization
CUSTOM_AUTH_URL = ''

#Import uploaded shapefiles into PostGIS?
POSTGIS_DATASTORE=False

#PostGIS datastore connection settings
POSTGIS_NAME = ''
POSTGIS_USER = ''
POSTGIS_PASSWORD = ''
POSTGIS_HOST = ''
POSTGIS_PORT = ''

try:
    from local_settings import *
except ImportError:
    pass
