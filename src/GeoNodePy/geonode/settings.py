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
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "uploaded")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/uploaded/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "static_root")

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/static/"

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "static"),
    ]

# Note that Django automatically includes the "templates" dir in all the
# INSTALLED_APPS, se there is no need to add maps/templates or admin/templates
TEMPLATE_DIRS = (
    os.path.join(PROJECT_ROOT, "templates"),
)

# Location of translation files
LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, "locale"),
)

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = os.path.join(STATIC_URL, "admin/")

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'

# Location of url mappings
ROOT_URLCONF = 'geonode.urls'

# Site id in the Django sites framework
SITE_ID = 1


INSTALLED_APPS = (

    # Apps bundled with Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.messages',

    # Third party apps
    'django_extensions',
    'registration',
    'profiles',
    'avatar',
    'dialogos',
    'agon_ratings',
    'taggit',
    'south',
    #'debug_toolbar',

    # GeoNode internal apps
    'geonode.core',
    'geonode.maps',
    'geonode.proxy',
    'geonode',
    'geonode.registration',
    'geonode.profiles',
    )

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    #'django.template.loaders.eggs.load_template_source',
    'django.template.loaders.app_directories.Loader',
    )

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "django.utils.log.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": True,
        },
        "geonode": {
            "handlers": ["console"],
            "level": "WARNING",
        },
    },
}


#
# Customizations to built in Django settings required by GeoNode
#

# Setting a custom test runner to avoid running the tests for
# some problematic 3rd party apps
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    # The context processor belows add things like SITEURL
    # and GEOSERVER_BASE_URL to all pages that use a RequestContext
    'geonode.maps.context_processors.resource_urls',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # The setting below makes it possible to serve different languages per
    # user depending on things like headers in HTTP requests.
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    )

#This is only required for the Django Debug Toolbar
INTERNAL_IPS = ('127.0.0.1',)

# Replacement of default authentication backend in order to support
# permissions per object.
AUTHENTICATION_BACKENDS = ('geonode.core.auth.GranularBackend',)


def get_user_url(u):
    from django.contrib.sites.models import Site
    s = Site.objects.get_current()
    return "http://" + s.domain + "/profiles/" + u.username


ABSOLUTE_URL_OVERRIDES = {
    'auth.user': get_user_url
}

# Redirects to home page after login
# FIXME(Ariel): I do not know why this setting is needed,
# it would be best to use the ?next= parameter
LOGIN_REDIRECT_URL = "/"


#
# Settings for third party apps
#

# Agon Ratings
AGON_RATINGS_CATEGORY_CHOICES = {
    "maps.Map": {
        "map": "How good is this map?"
    },
    "maps.Layer": {
        "layer": "How good is this layer?"
    },
}

# For South migrations
SOUTH_MIGRATION_MODULES = {
    'registration': 'geonode.migrations.registration',
    'avatar': 'geonode.migrations.avatar',
}

# For django-profiles
AUTH_PROFILE_MODULE = 'maps.Contact'

# For django-registration
REGISTRATION_OPEN = False

# Arguments for the test runner
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
      ]

#
# GeoNode specific settings
#

SITENAME = "GeoNode"

SITEURL = "http://localhost:8000/"

# GeoServer information

# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = "http://localhost:8001/geoserver/"

# The username and password for a user that can add and
# edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", SECRET_KEY


# GeoNetwork information

# The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
GEONETWORK_BASE_URL = "http://localhost:8001/geonetwork/"

# The username and password for a user with write access to GeoNetwork
GEONETWORK_CREDENTIALS = "admin", "admin"


# GeoNode javascript client configuration

# Google Api Key needed for 3D maps / Google Earth plugin
GOOGLE_API_KEY = "ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw"
GOOGLE_ANALYTICS_ID = "UA-XXXXXXXX-1"

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
        "source": {"ptype": "gx_olsource"},
        "type":"OpenLayers.Layer",
        "args":["No background"],
        "visibility": True,
        "fixed": False,
        "group":"background"
    },
        {
        "source": {"ptype": "gx_googlesource"},
        "group":"background",
        "name":"SATELLITE",
        "visibility": False,
        "fixed": True,
        },{
        "source": {"ptype": "gx_googlesource"},
        "name":"TERRAIN",
        "visibility": True,
        "fixed": True,
        "group":"background"
    },            {
        "source": {"ptype": "gx_googlesource"},
        "group":"background",
        "name":"ROADMAP",
        "visibility": False,
        "fixed": True,
        },{
        "source": {"ptype": "gx_googlesource"},
        "group":"background",
        "name":"HYBRID",
        "visibility": False,
        "fixed": True,
        },{
        "source": {"ptype": "gx_olsource"},
        "type":"OpenLayers.Layer.OSM",
        "args":["OpenStreetMap"],
        "visibility": False,
        "fixed": True,
        "group":"background"
    }]


REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 30
SERVE_MEDIA = DEBUG;

#GEONODE_CLIENT_LOCATION = "http://localhost:8001/geonode-client/"
GEONODE_CLIENT_LOCATION = "/media/static/"


# GeoNode vector data backend configuration.

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

#Set name of additional permissions group (besides anonymous and authenticated)
CUSTOM_GROUP_NAME = 'Organization Users'

#If you want to redirect members of your organization to a separate authentication system when registering, change the following settings
USE_CUSTOM_ORG_AUTHORIZATION = False
CUSTOM_ORG_AUTH_TEXT = 'Are you affiliated with XXXX?'
#Automatically add users with the following email address suffix to the custom group, if created via layer/map permissions
CUSTOM_GROUP_EMAIL_SUFFIX = ''
#URL to redirect to if user indicates they are a member of your organization
CUSTOM_AUTH_URL = ''

DEFAULT_WORKSPACE = 'geonode'

HGL_VALIDATION_KEY='Contact Harvard Geospatial Library to request the validation key'
CACHE_BACKEND = 'dummy://'

try:
    from local_settings import *
except ImportError:
    pass
