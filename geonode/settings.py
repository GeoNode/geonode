# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

# Django settings for the GeoNode project.
import os

#
# General Django development settings
#

# Defines the directory that contains the settings file as the PROJECT_ROOT
# It is used for relative settings elsewhere.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Setting debug to true makes Django serve static media and
# present pretty error pages.
DEBUG = TEMPLATE_DEBUG = True

# This is needed for integration tests, they require
# geonode to be listening for GeoServer auth requests.
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000'

# Defines settings for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'development.db'),
    }
}

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
    ('de', 'Deutsch'),
    ('el', 'Ελληνικά'),
    ('id', 'Bahasa Indonesia'),
    ('zh', '中文'),
)

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
    'django_forms_bootstrap',
    'registration',
    'profiles',
    'avatar',
    'dialogos',
    'agon_ratings',
    'taggit',
    'south',

    # GeoNode internal apps
    'geonode.maps',
    'geonode.layers',
    'geonode.people',
    'geonode.proxy',
    'geonode.security',
    'geonode.catalogue',
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
        "geonode": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "gsconfig.catalog": {
            "handlers": ["console"],
            "level": "ERROR",
        },
        "owslib": {
            "handlers": ["console"],
            "level": "ERROR",
        },    
    },
}

#
# Customizations to built in Django settings required by GeoNode
#


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    # The context processor belows add things like SITEURL
    # and GEOSERVER_BASE_URL to all pages that use a RequestContext
    'geonode.context_processors.resource_urls',
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
)


# Replacement of default authentication backend in order to support
# permissions per object.
AUTHENTICATION_BACKENDS = ('geonode.security.auth.GranularBackend',)

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
    "layers.Layer": {
        "layer": "How good is this layer?"
    },
}

# For South migrations
SOUTH_MIGRATION_MODULES = {
    'registration': 'geonode.migrations.registration',
    'avatar': 'geonode.migrations.avatar',
}

# For django-profiles
AUTH_PROFILE_MODULE = 'people.Contact'

# For django-registration
REGISTRATION_OPEN = False

#
# Test Settings
#

# Setting a custom test runner to avoid running the tests for
# some problematic 3rd party apps
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

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
#      '--stop',
      ]

#
# GeoNode specific settings
#

SITENAME = "GeoNode"

SITEURL = "http://localhost:8000/"

# GeoServer information

# The FULLY QUALIFIED url to the GeoServer instance for this GeoNode.
GEOSERVER_BASE_URL = "http://localhost:8080/geoserver/"

# The username and password for a user that can add and
# edit layer details on GeoServer
GEOSERVER_CREDENTIALS = "geoserver_admin", SECRET_KEY

# CSW settings
CATALOGUE = {
    'default': {
        # The underlying CSW implementation
        'ENGINE': 'geonode.catalogue.backends.pycsw_local',

        # The FULLY QUALIFIED base url to the CSW instance for this GeoNode
        'URL': '%scatalogue/csw' % SITEURL,
        #'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
        #'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',
    
        # login credentials (for GeoNetwork)
        'USER': 'admin',
        'PASSWORD': 'admin',
    }
}

# pycsw settings
PYCSW = {
    # pycsw configuration
    'CONFIGURATION': {
        'server': {
            'home': '.',
            'url': CATALOGUE['default']['URL'],
            'encoding': 'UTF-8',
            'language': LANGUAGE_CODE,
            'maxrecords': '10',
            #'loglevel': 'DEBUG',
            #'logfile': '/tmp/pycsw.log',
            #'federatedcatalogues': 'http://geo.data.gov/geoportal/csw/discovery',
            #'pretty_print': 'true',
            #'domainquerytype': 'range',
            #'domaincounts': 'true',
           'profiles': 'apiso,atom,dif,ebrim,fgdc',
        },
        'metadata:main': {
            'identification_title': '%s Catalogue' % SITENAME,
            'identification_abstract': 'GeoNode is an open source platform that facilitates the creation, sharing, and collaborative use of geospatial data',
            'identification_keywords': '%s,sdi,catalogue,discovery,metadata,GeoNode' % SITENAME,
            'identification_keywords_type': 'theme',
            'identification_fees': 'None',
            'identification_accessconstraints': 'None',
            'provider_name': 'Organization Name',
            'provider_url': SITEURL,
            'contact_name': 'Lastname, Firstname',
            'contact_position': 'Position Title',
            'contact_address': 'Mailing Address',
            'contact_city': 'City',
            'contact_stateorprovince': 'Administrative Area',
            'contact_postalcode': 'Zip or Postal Code',
            'contact_country': 'Country',
            'contact_phone': '+xx-xxx-xxx-xxxx',
            'contact_fax': '+xx-xxx-xxx-xxxx',
            'contact_email': 'Email Address',
            'contact_url': 'Contact URL',
            'contact_hours': 'Hours of Service',
            'contact_instructions': 'During hours of service. Off on weekends.',
            'contact_role': 'pointOfContact',
        },
        'repository': {
            'source': 'geonode',
            'mappings': 'geonode/catalogue/backends/pycsw_local.py',
        },
        'metadata:inspire': {
            'enabled': 'true',
            'languages_supported': 'eng,gre',
            'default_language': 'eng',
            'date': 'YYYY-MM-DD',
            'gemet_keywords': 'Utility and governmental services',
            'conformity_service': 'notEvaluated',
            'contact_name': 'Organization Name',
            'contact_email': 'Email Address',
            'temp_extent': 'YYYY-MM-DD/YYYY-MM-DD',
        }
    }
}

# GeoNode javascript client configuration

# Google Api Key needed for 3D maps / Google Earth plugin
GOOGLE_API_KEY = "ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw"

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (0, 0)

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 0

MAP_BASELAYERS = [{
    "source": {
        "ptype": "gxp_wmscsource",
        "url": GEOSERVER_BASE_URL + "wms",
        "restUrl": "/gs/rest"
     }
  },{
    "source": {"ptype": "gx_olsource"},
    "type":"OpenLayers.Layer",
    "args":["No background"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  }, {
    "source": {"ptype": "gx_olsource"},
    "type":"OpenLayers.Layer.OSM",
    "args":["OpenStreetMap"],
    "visibility": False,
    "fixed": True,
    "group":"background"
  }, {
    "source": {"ptype": "gxp_mapquestsource"},
    "name":"osm",
    "group":"background",
    "visibility": True
  }, {
    "source": {"ptype": "gxp_mapquestsource"},
    "name":"naip",
    "group":"background",
    "visibility": False
  }, {
    "source": {"ptype": "gxp_bingsource"},
    "name": "AerialWithLabels",
    "fixed": True,
    "visibility": False,
    "group":"background"
  },{
    "source": {"ptype": "gxp_mapboxsource"},
  }, {
    "source": {"ptype": "gx_olsource"},
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
        "tilesOrigin": [-20037508.34, -20037508.34]
      },
      {"buffer": 0}
    ]

}]

GEONODE_CLIENT_LOCATION = "/static/geonode/"

# GeoNode vector data backend configuration.

#Import uploaded shapefiles into a database such as PostGIS?
DB_DATASTORE = False

#Database datastore connection settings
DB_DATASTORE_DATABASE = ''
DB_DATASTORE_USER = ''
DB_DATASTORE_PASSWORD = ''
DB_DATASTORE_HOST = ''
DB_DATASTORE_PORT = ''
DB_DATASTORE_TYPE = ''
#The name of the store in Geoserver
DB_DATASTORE_NAME = ''

# Load more settings from a file called local_settings.py if it exists
try:
    from local_settings import *
except ImportError:
    pass
