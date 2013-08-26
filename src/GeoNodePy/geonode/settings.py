# -*- coding: utf-8 -*-
# Django settings for GeoNode project.
import logging
import os

gettext = lambda s: s

#
# General Django development settings
#

# Defines the directory that contains the settings file as the PROJECT_ROOT
# It is used for relative settings elsewhere.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Setting debug to true makes Django serve static media and
# present pretty error pages.
DEBUG = TEMPLATE_DEBUG = True

#Email settings (example gmail account) for registration, passwords, etc
#DEFAULT_FROM_EMAIL = 'your_email@gmail.com'
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_HOST_USER = 'your_email@gmail.com'
#EMAIL_HOST_PASSWORD = 'password'
#EMAIL_PORT = 587
#EMAIL_USE_TLS = True

# Defines settings for development
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'wm_db',
        'USER': 'wm_user',
        'PASSWORD': 'wm_password',
        'HOST': 'localhost', 'PORT': '5432'
        }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

LANGUAGES = (
    ('en', 'English'),
    ('fr', 'Français'),
)

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
    'autocomplete_light',
    'djcelery',
    'djkombu',

    # GeoNode internal apps
    'geonode.core',
    'geonode.maps',
    'geonode.proxy',
    'geonode.profile',
    'geonode.register',
    'geonode.mapnotes',
    'geonode.capabilities',
    'geonode.queue',
    'geonode.certification',
    #'geonode.hoods',
    #'geonode.gazetteer',
    #'debug_toolbar',

)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(message)s',        },
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers':['null'],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'geonode': {
            'handlers': ['console'],
            'level': 'WARNING',
        },
    }
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
#If upgrading from an earlier version of WorldMap,
#you may need to comment this out
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
GEOSERVER_BASE_URL = "http://localhost:8080/geoserver/"

# The username and password for a user that can add and edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", SECRET_KEY

# The FULLY QUALIFIED url to the GeoNetwork instance for this GeoNode
GEONETWORK_BASE_URL = "http://localhost:8080/geonetwork/"

# The username and password for a user with write access to GeoNetwork
GEONETWORK_CREDENTIALS = "admin", "admin"
LOGIN_REDIRECT_URL = "/"

DEFAULT_LAYERS_OWNER='admin'

# GeoNode javascript client configuration

# Google Api Key needed for 3D maps / Google Earth plugin
GOOGLE_API_KEY = None
GOOGLE_SECRET_KEY = None
GOOGLE_ANALYTICS_CODE=""

YAHOO_API_KEY=""

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (0, 0)

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 2


DEFAULT_LAYER_SOURCE = {
    "ptype":"gxp_gnsource",
    "url":"/geoserver/wms",
    "restUrl": "/gs/rest"
}


REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 30
SERVE_MEDIA = DEBUG;


MAP_BASELAYERS = [
 {
        "source": {"ptype": "gx_olsource"},
        "type": "OpenLayers.Layer",
        "args": [gettext("No background")],
        "visibility": False,
        "fixed": True,
        "group": "background"
    }, {
        "source": {"ptype": "gx_olsource"},
        "type": "OpenLayers.Layer.OSM",
        "args": [gettext("OpenStreetMap")],
        "visibility": False,
        "fixed": True,
        "group": "background"
    }, {
        "source": {"ptype": "gxp_mapquestsource"},
        "name": "osm",
        "group": "background",
        "visibility": True
    }, {
        "source": {"ptype": "gxp_mapquestsource"},
        "name": "naip",
        "group": "background",
        "visibility": False
    }, {
        "source": {"ptype": "gxp_bingsource"},
        "name": "AerialWithLabels",
        "fixed": True,
        "visibility": False,
        "group": "background"
    }, {
        "source": {"ptype": "gxp_mapboxsource"},
    },
    {
        "source": {"ptype": "gx_googlesource"},
        "group": "background",
        "name": "SATELLITE",
        "visibility": False,
        "fixed": True,
    }, {
        "source": {"ptype": "gx_googlesource"},
        "group": "background",
        "name": "TERRAIN",
        "visibility": False,
        "fixed": True,
    }, {
        "source": {"ptype": "gx_googlesource"},
        "group": "background",
        "name": "HYBRID",
        "visibility": False,
        "fixed": True,
    }, {
        "source": {"ptype": "gx_googlesource"},
        "group": "background",
        "name": "ROADMAP",
        "visibility": False,
        "fixed": True,
        "group": "background"
    }
]


#GEONODE_CLIENT_LOCATION = "http://localhost:9090/"
GEONODE_CLIENT_LOCATION = "/static/geonode/"


# GeoNode vector data backend configuration.

#Import uploaded shapefiles into a database such as PostGIS?
DB_DATASTORE = False

#
#Database datastore connection settings
#
DB_DATASTORE_DATABASE = ''
DB_DATASTORE_USER = ''
DB_DATASTORE_PASSWORD = ''
DB_DATASTORE_HOST = ''
DB_DATASTORE_PORT = ''
DB_DATASTORE_TYPE = ''
# Name of the store in geoserver
DB_DATASTORE_NAME = ''
DB_DATASTORE_ENGINE = 'django.contrib.gis.db.backends.postgis'

USE_GAZETTEER = False
##### START GAZETTEER SETTINGS #####
# Defines settings for multiple databases,
# only use if PostGIS integration enabled
# and USE_GAZETTEER = True
#DATABASES = {
#    'default': {
#        'ENGINE': DATABASE_ENGINE,
#        'NAME': DATABASE_NAME,
#        'USER' : DATABASE_USER,
#        'PASSWORD': DATABASE_PASSWORD,
#        'PORT': DATABASE_PORT,
#        'HOST': DATABASE_HOST
#    },
#    'wmdata': {
#        'ENGINE': DB_DATASTORE_ENGINE,
#        'NAME': DB_DATASTORE_DATABASE,
#        'USER' : DB_DATASTORE_USER,
#        'PASSWORD': DB_DATASTORE_PASSWORD,
#        'PORT': DB_DATASTORE_PORT,
#        'HOST': DATABASE_HOST
#    }
#
#}
#DATABASE_ROUTERS = ['geonode.utils.WorldmapDatabaseRouter']
#SOUTH_DATABASE_ADAPTERS = {
#    'default': "south.db.sqlite3",
#    'wmdata' : "south.db.postgresql_psycopg2",
#
#    }
#SOUTH_TESTS_MIGRATE = False
GAZETTEER_FULLTEXTSEARCH = False
##### END GAZETTEER SETTINGS #####

#Set to true to schedule asynchronous updates of
#layer bounds updates (after creating/editing features)
#and gazetteer updates
USE_QUEUE = False
QUEUE_INTERVAL = '*/10'
CELERY_IMPORTS = ("geonode.queue", )
BROKER_URL = "django://"
if USE_QUEUE:
    import djcelery
    djcelery.setup_loader()


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


### Boston neighborhood settings  ###
### These need to be set to the correct values for the worldmap instance ###
# HOODS_TEMPLATE_LAYER = 'tl_2010_25025_tabblock10_f2j_651' # layer name in geoserver
# HOODS_TEMPLATE_ID = 8  #Map id to be used as template
# HOODS_TEMPLATE_ATTRIBUTE = 'GEOID10'  #Attribute to be used for block id
# HOODS_MASTER_LAYER = 'masterhoodlayer_nuw'

GEOPS_IP =  '128.30.77.57:8083'
#GEOPS_IP =  '140.247.116.252:8083'
GEOPS_DOWNLOAD = ''

try:
    from local_settings import *
except ImportError:
    pass
