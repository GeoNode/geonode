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
from kombu import Queue
from celery_app import app  # flake8: noqa

#
# General Django development settings
#

# Defines the directory that contains the settings file as the PROJECT_ROOT
# It is used for relative settings elsewhere.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Setting debug to true makes Django serve static media and
# present pretty error pages.
DEBUG = TEMPLATE_DEBUG = True

# Set to True to load non-minified versions of (static) client dependencies
# Requires to set-up Node and tools that are required for static development
# otherwise it will raise errors for the missing non-minified dependencies
DEBUG_STATIC = False

# This is needed for integration tests, they require
# geonode to be listening for GeoServer auth requests.
os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = 'localhost:8000'

# Defines settings for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'development.db'),
    },
    # vector datastore for uploads
    # 'datastore' : {
    #    'ENGINE': 'django.contrib.gis.db.backends.postgis',
    #    'NAME': '',
    #    'USER' : '',
    #    'PASSWORD' : '',
    #    'HOST' : '',
    #    'PORT' : '',
    # }
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
    ('zh-cn', '中文'),
    ('ja', '日本語'),
    ('fa', 'Persian'),
    ('ar', 'Arabic'),
    ('bn', 'Bengali'),
    ('ne', 'Nepali'),
    ('sq', 'Albanian'),
    ('af', 'Afrikaans'),
    ('sw', 'Swahili'),
    ('pt', 'Portuguese'),
    ('ru', 'Russian'),
    ('vi', 'Vietnamese'),
    ('ko', '한국어'),
    ('am', 'Amharic'),
    ('km', 'Khmer'),
    ('pl', 'Polish'),
    ('sv', 'Swedish'),
    ('th', 'Thai'),
    ('uk', 'Ukranian'),
    ('si', 'Sinhala'),
    ('ta', 'Tamil'),
    ('tl', 'Tagalog'),
)

EXTRA_LANG_INFO = {
    'am': {
        'bidi': False,
        'code': 'am',
        'name': 'Amharic',
        'name_local': 'Amharic',
        },
    'tl': {
        'bidi': False,
        'code': 'tl',
        'name': 'Tagalog',
        'name_local': 'tagalog',
        },
    'ta': {
        'bidi': False,
        'code': 'ta',
        'name': 'Tamil',
        'name_local': u'tamil',
        },
    'si': {
        'bidi': False,
        'code': 'si',
        'name': 'Sinhala',
        'name_local': 'sinhala',
        },
}

AUTH_USER_MODEL = 'people.Profile'

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

MODELTRANSLATION_LANGUAGES = ['en', ]

MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'

MODELTRANSLATION_FALLBACK_LANGUAGES = ('en',)

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

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

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

# Login and logout urls override
LOGIN_URL = '/account/login/'
LOGOUT_URL = '/account/logout/'

# Documents application
ALLOWED_DOCUMENT_TYPES = [
    'doc', 'docx', 'gif', 'jpg', 'jpeg', 'ods', 'odt', 'odp', 'pdf', 'png', 'ppt',
    'pptx', 'rar', 'tif', 'tiff', 'txt', 'xls', 'xlsx', 'xml', 'zip', 'gz'
]
MAX_DOCUMENT_SIZE = 2  # MB
DOCUMENT_TYPE_MAP = {
    'txt': 'text',
    'log': 'text',
    'doc': 'text',
    'docx': 'text',
    'ods': 'text',
    'odt': 'text',
    'xls': 'text',
    'xlsx': 'text',
    'xml': 'text',

    'gif': 'image',
    'jpg': 'image',
    'jpeg': 'image',
    'png': 'image',
    'tif': 'image',
    'tiff': 'image',

    'odp': 'presentation',
    'ppt': 'presentation',
    'pptx': 'presentation',
    'pdf': 'presentation',

    'rar': 'archive',
    'gz': 'archive',
    'zip': 'archive',
}


GEONODE_APPS = (


    # GeoNode internal apps
    'geonode.people',
    'geonode.base',
    'geonode.layers',
    'geonode.maps',
    'geonode.proxy',
    'geonode.security',
    'geonode.social',
    'geonode.catalogue',
    'geonode.documents',
    'geonode.api',
    'geonode.groups',
    'geonode.services',

    # GeoNode Contrib Apps

    # 'geonode.contrib.dynamic',

    # GeoServer Apps
    # Geoserver needs to come last because
    # it's signals may rely on other apps' signals.
    'geonode.geoserver',
    'geonode.upload',
    'geonode.tasks'
)

INSTALLED_APPS = (

    # Boostrap admin theme
    # 'django_admin_bootstrapped.bootstrap3',
    # 'django_admin_bootstrapped',

    # Apps bundled with Django
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.gis',

    # Third party apps

    # Utility
    'pagination',
    'taggit',
    'friendlytagloader',
    'geoexplorer',
    'leaflet',
    'django_extensions',
    # 'haystack',
    'autocomplete_light',
    'mptt',
    'modeltranslation',
    'djcelery',

    # Theme
    "pinax_theme_bootstrap_account",
    "pinax_theme_bootstrap",
    'django_forms_bootstrap',

    # Social
    'account',
    'avatar',
    'dialogos',
    'agon_ratings',
    #'notification',
    'announcements',
    'actstream',
    'user_messages',
    'tastypie',
    'polymorphic',
    'guardian',

) + GEONODE_APPS

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level': 'ERROR',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR', 'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"], "level": "ERROR", },
        "geonode": {
            "handlers": ["console"], "level": "ERROR", },
        "gsconfig.catalog": {
            "handlers": ["console"], "level": "ERROR", },
        "owslib": {
            "handlers": ["console"], "level": "ERROR", },
        "pycsw": {
            "handlers": ["console"], "level": "ERROR", },
        },
    }

#
# Customizations to built in Django settings required by GeoNode
#


TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    "django.core.context_processors.tz",
    'django.core.context_processors.media',
    "django.core.context_processors.static",
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'account.context_processors.account',
    # The context processor below adds things like SITEURL
    # and GEOSERVER_BASE_URL to all pages that use a RequestContext
    'geonode.context_processors.resource_urls',
    'geonode.geoserver.context_processors.geoserver_urls',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # The setting below makes it possible to serve different languages per
    # user depending on things like headers in HTTP requests.
    'django.middleware.locale.LocaleMiddleware',
    'pagination.middleware.PaginationMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # This middleware allows to print private layers for the users that have 
    # the permissions to view them.
    # It sets temporary the involved layers as public before restoring the permissions.
    # Beware that for few seconds the involved layers are public there could be risks.
    # 'geonode.middleware.PrintProxyMiddleware',
)


# Replacement of default authentication backend in order to support
# permissions per object.
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

ANONYMOUS_USER_ID = -1
GUARDIAN_GET_INIT_ANONYMOUS_USER = 'geonode.people.models.get_anonymous_user_instance'

# Whether the uplaoded resources should be public and downloadable by default or not
DEFAULT_ANONYMOUS_VIEW_PERMISSION = True
DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION = True

#
# Settings for default search size
#
DEFAULT_SEARCH_SIZE = 10


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
    "documents.Document": {
        "document": "How good is this document?"
    }
}

# Activity Stream
ACTSTREAM_SETTINGS = {
    'MODELS': (
        'people.Profile',
        'layers.layer',
        'maps.map',
        'dialogos.comment',
        'documents.document',
        'services.service'),
    'FETCH_RELATIONS': True,
    'USE_PREFETCH': False,
    'USE_JSONFIELD': True,
    'GFK_FETCH_DEPTH': 1,
}

# Settings for Social Apps
REGISTRATION_OPEN = False
ACCOUNT_EMAIL_CONFIRMATION_EMAIL = False
ACCOUNT_EMAIL_CONFIRMATION_REQUIRED = False
ACCOUNT_APPROVAL_REQUIRED = False

# Email for users to contact admins.
THEME_ACCOUNT_CONTACT_EMAIL = 'admin@example.com'

#
# Test Settings
#

# Setting a custom test runner to avoid running the tests for
# some problematic 3rd party apps
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

# Arguments for the test runner
NOSE_ARGS = [
    '--nocapture',
    '--detailed-errors',
]

#
# GeoNode specific settings
#

SITEURL = "http://localhost:8000/"

USE_QUEUE = False

DEFAULT_WORKSPACE = 'geonode'
CASCADE_WORKSPACE = 'geonode'

OGP_URL = "http://geodata.tufts.edu/solr/select"

# Topic Categories list should not be modified (they are ISO). In case you
# absolutely need it set to True this variable
MODIFY_TOPICCATEGORY = False

MISSING_THUMBNAIL = 'geonode/img/missing_thumb.png'

# Search Snippet Cache Time in Seconds
CACHE_TIME = 0

# OGC (WMS/WFS/WCS) Server Settings
# OGC (WMS/WFS/WCS) Server Settings
OGC_SERVER = {
    'default': {
        'BACKEND': 'geonode.geoserver',
        'LOCATION': 'http://localhost:8080/geoserver/',
        # PUBLIC_LOCATION needs to be kept like this because in dev mode
        # the proxy won't work and the integration tests will fail
        # the entire block has to be overridden in the local_settings
        'PUBLIC_LOCATION': 'http://localhost:8080/geoserver/',
        'USER': 'admin',
        'PASSWORD': 'geoserver',
        'MAPFISH_PRINT_ENABLED': True,
        'PRINT_NG_ENABLED': True,
        'GEONODE_SECURITY_ENABLED': True,
        'GEOGIG_ENABLED': False,
        'WMST_ENABLED': False,
        'BACKEND_WRITE_ENABLED': True,
        'WPS_ENABLED': False,
        'LOG_FILE': '%s/geoserver/data/logs/geoserver.log' % os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir)),
        # Set to name of database in DATABASES dictionary to enable
        'DATASTORE': '',  # 'datastore',
        'TIMEOUT': 10  # number of seconds to allow for HTTP requests
    }
}

# Uploader Settings
UPLOADER = {
    'BACKEND': 'geonode.rest',
    'OPTIONS': {
        'TIME_ENABLED': False,
        'GEOGIG_ENABLED': False,
    }
}

# CSW settings
CATALOGUE = {
    'default': {
        # The underlying CSW implementation
        # default is pycsw in local mode (tied directly to GeoNode Django DB)
        'ENGINE': 'geonode.catalogue.backends.pycsw_local',
        # pycsw in non-local mode
        # 'ENGINE': 'geonode.catalogue.backends.pycsw_http',
        # GeoNetwork opensource
        # 'ENGINE': 'geonode.catalogue.backends.geonetwork',
        # deegree and others
        # 'ENGINE': 'geonode.catalogue.backends.generic',

        # The FULLY QUALIFIED base url to the CSW instance for this GeoNode
        'URL': '%scatalogue/csw' % SITEURL,
        # 'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
        # 'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',

        # login credentials (for GeoNetwork)
        'USER': 'admin',
        'PASSWORD': 'admin',
    }
}

# pycsw settings
PYCSW = {
    # pycsw configuration
    'CONFIGURATION': {
        # uncomment / adjust to override server config system defaults
        #'server': {
        #    'maxrecords': '10',
        #    'pretty_print': 'true',
        #    'federatedcatalogues': 'http://catalog.data.gov/csw'
        #},
        'metadata:main': {
            'identification_title': 'GeoNode Catalogue',
            'identification_abstract': 'GeoNode is an open source platform that facilitates the creation, sharing, \
             and collaborative use of geospatial data',
            'identification_keywords': 'sdi,catalogue,discovery,metadata,GeoNode',
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

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (0, 0)

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 0

MAP_BASELAYERS = [{
    "source": {"ptype": "gxp_olsource"},
    "type": "OpenLayers.Layer",
    "args": ["No background"],
    "visibility": False,
    "fixed": True,
    "group":"background"
}, {
    "source": {"ptype": "gxp_osmsource"},
    "type": "OpenLayers.Layer.OSM",
    "name": "mapnik",
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
}]

SOCIAL_BUTTONS = True

SOCIAL_ORIGINS = [{
    "label":"Email",
    "url":"mailto:?subject={name}&body={url}",
    "css_class":"email"
}, {
    "label":"Facebook",
    "url":"http://www.facebook.com/sharer.php?u={url}",
    "css_class":"fb"
}, {
    "label":"Twitter",
    "url":"https://twitter.com/share?url={url}",
    "css_class":"tw"
}, {
    "label":"Google +",
    "url":"https://plus.google.com/share?url={url}",
    "css_class":"gp"
}]

#CKAN Query String Parameters names pulled from
#https://github.com/ckan/ckan/blob/2052628c4a450078d58fb26bd6dc239f3cc68c3e/ckan/logic/action/create.py#L43
CKAN_ORIGINS = [{
    "label":"Humanitarian Data Exchange (HDX)",
    "url":"https://data.hdx.rwlabs.org/dataset/new?title={name}&dataset_date={date}&notes={abstract}&caveats={caveats}",
    "css_class":"hdx"
}]
#SOCIAL_ORIGINS.extend(CKAN_ORIGINS)

# Enable Licenses User Interface
# Regardless of selection, license field stil exists as a field in the Resourcebase model.
# Detail Display: above, below, never
# Metadata Options: verbose, light, never
LICENSES = {
    'ENABLED': True,
    'DETAIL': 'above',
    'METADATA': 'verbose',
}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Require users to authenticate before using Geonode
LOCKDOWN_GEONODE = False

# Add additional paths (as regular expressions) that don't require
# authentication.
AUTH_EXEMPT_URLS = ()

if LOCKDOWN_GEONODE:
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
        ('geonode.security.middleware.LoginRequiredMiddleware',)


# A tuple of hosts the proxy can send requests to.
PROXY_ALLOWED_HOSTS = ()

# The proxy to use when making cross origin requests.
PROXY_URL = '/proxy/?url=' if DEBUG else None

# Haystack Search Backend Configuration.  To enable, first install the following:
# - pip install django-haystack
# - pip install pyelasticsearch
# Set HAYSTACK_SEARCH to True
# Run "python manage.py rebuild_index"
HAYSTACK_SEARCH = False
# Avoid permissions prefiltering
SKIP_PERMS_FILTER = False
# Update facet counts from Haystack
HAYSTACK_FACET_COUNTS = False
# HAYSTACK_CONNECTIONS = {
#    'default': {
#        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
#        'URL': 'http://127.0.0.1:9200/',
#        'INDEX_NAME': 'geonode',
#        },
#    }
# HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
# HAYSTACK_SEARCH_RESULTS_PER_PAGE = 20

# Available download formats
DOWNLOAD_FORMATS_METADATA = [
    'Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'ISO',
]
DOWNLOAD_FORMATS_VECTOR = [
    'JPEG', 'PDF', 'PNG', 'Zipped Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
    'Excel', 'GeoJSON', 'KML', 'View in Google Earth', 'Tiles',
]
DOWNLOAD_FORMATS_RASTER = [
    'JPEG',
    'PDF',
    'PNG',
    'ArcGrid',
    'GeoTIFF',
    'Gtopo30',
    'ImageMosaic',
    'KML',
    'View in Google Earth',
    'Tiles',
]

ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE = False

TASTYPIE_DEFAULT_FORMATS = ['json']

# gravatar settings
AUTO_GENERATE_AVATAR_SIZES = (20, 32, 80, 100, 140, 200)

# notification settings
NOTIFICATION_LANGUAGE_MODULE = "account.Account"

# Number of results per page listed in the GeoNode search pages
CLIENT_RESULTS_LIMIT = 100

# Number of items returned by the apis 0 equals no limit
API_LIMIT_PER_PAGE = 0

LEAFLET_CONFIG = {
    'TILES': [
        # Find tiles at:
        # http://leaflet-extras.github.io/leaflet-providers/preview/

        # Stamen toner lite.
        ('Watercolor',
         'http://{s}.tile.stamen.com/watercolor/{z}/{x}/{y}.png',
         'Map tiles by <a href="http://stamen.com">Stamen Design</a>, \
         <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; \
         <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, \
         <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'),
        ('Toner Lite',
         'http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}.png',
         'Map tiles by <a href="http://stamen.com">Stamen Design</a>, \
         <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; \
         <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, \
         <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'),
    ],
    'PLUGINS': {
        'esri-leaflet': {
            'js': 'lib/js/esri-leaflet.js',
            'auto-include': True,
        },
        'leaflet-fullscreen': {
            'css': 'lib/css/leaflet.fullscreen.css',
            'js': 'lib/js/Leaflet.fullscreen.min.js',
            'auto-include': True,
        },
    }
}

# option to enable/disable resource unpublishing for administrators
RESOURCE_PUBLISHING = False

CACHES = {
    # DUMMY CACHE FOR DEVELOPMENT
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },
    # MEMCACHED EXAMPLE
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
    #     'LOCATION': '127.0.0.1:11211',
    #     },
    # FILECACHE EXAMPLE
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    #     'LOCATION': '/tmp/django_cache',
    #     }
}

LAYER_PREVIEW_LIBRARY = 'geoext'

SERVICE_UPDATE_INTERVAL = 0

# Queue non-blocking notifications.
NOTIFICATION_QUEUE_ALL = False

BROKER_URL = "django://"
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
CELERY_IGNORE_RESULT = True
CELERY_SEND_EVENTS = False
CELERY_RESULT_BACKEND = None
CELERY_TASK_RESULT_EXPIRES = 1
CELERY_DISABLE_RATE_LIMITS = True
CELERY_DEFAULT_QUEUE = "default"
CELERY_DEFAULT_EXCHANGE = "default"
CELERY_DEFAULT_EXCHANGE_TYPE = "direct"
CELERY_DEFAULT_ROUTING_KEY = "default"
CELERY_CREATE_MISSING_QUEUES = True
CELERY_IMPORTS = (
    'geonode.tasks.deletion',
    'geonode.tasks.update',
    'geonode.tasks.email'
)


CELERY_QUEUES = [
    Queue('default', routing_key='default'),
    Queue('cleanup', routing_key='cleanup'),
    Queue('update', routing_key='update'),
    Queue('email', routing_key='email'),
]

import djcelery
djcelery.setup_loader()

# Load more settings from a file called local_settings.py if it exists
try:
    from local_settings import *  # noqa
except ImportError:
    pass


#for windows users check if they didn't set GEOS and GDAL in local_settings.py
#maybe they set it as a windows environment
if os.name == 'nt':
    if not "GEOS_LIBRARY_PATH" in locals() or not "GDAL_LIBRARY_PATH" in locals():
        if os.environ.get("GEOS_LIBRARY_PATH", None) \
            and os.environ.get("GDAL_LIBRARY_PATH", None):
            GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH') 
            GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH')
        else:
            #maybe it will be found regardless if not it will throw 500 error
            from django.contrib.gis.geos import GEOSGeometry


# define the urls after the settings are overridden
if 'geonode.geoserver' in INSTALLED_APPS:
    LOCAL_GEOSERVER = {
        "source": {
            "ptype": "gxp_wmscsource",
            "url": OGC_SERVER['default']['PUBLIC_LOCATION'] + "wms",
            "restUrl": "/gs/rest"
        }
    }
    baselayers = MAP_BASELAYERS
    MAP_BASELAYERS = [LOCAL_GEOSERVER]
    MAP_BASELAYERS.extend(baselayers)
