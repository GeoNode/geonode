# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

import os
from geonode.settings import *

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(PROJECT_ROOT, "uploaded"))

STATIC_ROOT = os.getenv('STATIC_ROOT',
                        os.path.join(PROJECT_ROOT, "static_root")
                        )

# SECRET_KEY = '************************'

SITEURL = "http://localhost:8000"

ALLOWED_HOSTS = ['localhost', 'geonode.example.com']

# TIME_ZONE = 'Europe/Paris'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'upload_test',
        'USER': 'geonode',
        'PASSWORD': 'geonode',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

GEOSERVER_LOCATION = os.getenv(
    'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
)

GEOSERVER_PUBLIC_LOCATION = os.getenv(
    #    'GEOSERVER_PUBLIC_LOCATION', '{}/geoserver/'.format(SITEURL)
    'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
)

OGC_SERVER_DEFAULT_USER = os.getenv(
    'GEOSERVER_ADMIN_USER', 'admin'
)

OGC_SERVER_DEFAULT_PASSWORD = os.getenv(
    'GEOSERVER_ADMIN_PASSWORD', 'geoserver'
)

# OGC (WMS/WFS/WCS) Server Settings
OGC_SERVER = {
    'default': {
        'BACKEND': 'geonode.geoserver',
        'LOCATION': GEOSERVER_LOCATION,
        'LOGIN_ENDPOINT': 'j_spring_oauth2_geonode_login',
        'LOGOUT_ENDPOINT': 'j_spring_oauth2_geonode_logout',
        # PUBLIC_LOCATION needs to be kept like this because in dev mode
        # the proxy won't work and the integration tests will fail
        # the entire block has to be overridden in the local_settings
        'PUBLIC_LOCATION': GEOSERVER_PUBLIC_LOCATION,
        'USER': OGC_SERVER_DEFAULT_USER,
        'PASSWORD': OGC_SERVER_DEFAULT_PASSWORD,
        'MAPFISH_PRINT_ENABLED': True,
        'PRINT_NG_ENABLED': True,
        'GEONODE_SECURITY_ENABLED': True,
        'GEOFENCE_SECURITY_ENABLED': True,
        'GEOGIG_ENABLED': False,
        'WMST_ENABLED': False,
        'BACKEND_WRITE_ENABLED': True,
        'WPS_ENABLED': False,
        'LOG_FILE': '%s/geoserver/data/logs/geoserver.log' % os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir)),
        # Set to dictionary identifier of database containing spatial data in
        # DATABASES dictionary to enable
        'DATASTORE': 'default',
        'PG_GEOGIG': False,
        'TIMEOUT': 10  # number of seconds to allow for HTTP requests
    }
}

# If you want to enable Mosaics use the following configuration
UPLOADER = {
    # 'BACKEND': 'geonode.rest',
    'BACKEND': 'geonode.importer',
    'OPTIONS': {
        'TIME_ENABLED': True,
        'MOSAIC_ENABLED': False,
        'GEOGIG_ENABLED': False,
    },
    'SUPPORTED_CRS': [
        'EPSG:4326',
        'EPSG:3785',
        'EPSG:3857',
        'EPSG:900913',
        'EPSG:32647',
        'EPSG:32736'
    ]
}

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
        'URL': '%s/catalogue/csw' % SITEURL,
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
        # 'server': {
        #    'maxrecords': '10',
        #    'pretty_print': 'true',
        #    'federatedcatalogues': 'http://catalog.data.gov/csw'
        # },
        'metadata:main': {
            'identification_title': 'GeoNode Catalogue',
            'identification_abstract': 'GeoNode is an open source platform' \
            ' that facilitates the creation, sharing, and collaborative use' \
            ' of geospatial data',
            'identification_keywords': 'sdi, catalogue, discovery, metadata,' \
            ' GeoNode',
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
            'contact_instructions': 'During hours of service. Off on ' \
            'weekends.',
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

# default map projection
# Note: If set to EPSG:4326, then only EPSG:4326 basemaps will work.
DEFAULT_MAP_CRS = "EPSG:900913"

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (0, 0)

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 0

# Default preview library
LAYER_PREVIEW_LIBRARY = 'geoext'
#LAYER_PREVIEW_LIBRARY = 'leaflet'
# LEAFLET_CONFIG = {
#    'TILES': [
#        # Find tiles at:
#        # http://leaflet-extras.github.io/leaflet-providers/preview/
#
#        # Map Quest
#        ('Map Quest',
#         'http://otile4.mqcdn.com/tiles/1.0.0/osm/{z}/{x}/{y}.png',
#         'Tiles Courtesy of <a href="http://www.mapquest.com/">MapQuest</a> '
#         '&mdash; Map data &copy; '
#         '<a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'),
#        # Stamen toner lite.
#        # ('Watercolor',
#        #  'http://{s}.tile.stamen.com/watercolor/{z}/{x}/{y}.png',
#        #  'Map tiles by <a href="http://stamen.com">Stamen Design</a>, \
#        #  <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; \
#        #  <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, \
#        #  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'),
#        # ('Toner Lite',
#        #  'http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}.png',
#        #  'Map tiles by <a href="http://stamen.com">Stamen Design</a>, \
#        #  <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; \
#        #  <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, \
#        #  <a href="http://creativecommons.org/licenses/by-sa/2.0/">CC-BY-SA</a>'),
#    ],
#    'PLUGINS': {
#        'esri-leaflet': {
#            'js': 'lib/js/esri-leaflet.js',
#            'auto-include': True,
#        },
#        'leaflet-fullscreen': {
#            'css': 'lib/css/leaflet.fullscreen.css',
#            'js': 'lib/js/Leaflet.fullscreen.min.js',
#            'auto-include': True,
#        },
#    },
#    'SRID': 3857,
#    'RESET_VIEW': False
#}

ALT_OSM_BASEMAPS = os.environ.get('ALT_OSM_BASEMAPS', False)
CARTODB_BASEMAPS = os.environ.get('CARTODB_BASEMAPS', False)
STAMEN_BASEMAPS = os.environ.get('STAMEN_BASEMAPS', False)
THUNDERFOREST_BASEMAPS = os.environ.get('THUNDERFOREST_BASEMAPS', False)
MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN', None)
BING_API_KEY = os.environ.get('BING_API_KEY', None)

MAP_BASELAYERS = [{
    "source": {"ptype": "gxp_olsource"},
    "type": "OpenLayers.Layer",
    "args": ["No background"],
    "name": "background",
    "visibility": False,
    "fixed": True,
    "group":"background"
},
    # {
    #     "source": {"ptype": "gxp_olsource"},
    #     "type": "OpenLayers.Layer.XYZ",
    #     "title": "TEST TILE",
    #     "args": ["TEST_TILE", "http://test_tiles/tiles/${z}/${x}/${y}.png"],
    #     "name": "background",
    #     "attribution": "&copy; TEST TILE",
    #     "visibility": False,
    #     "fixed": True,
    #     "group":"background"
    # },
    {
    "source": {"ptype": "gxp_osmsource"},
    "type": "OpenLayers.Layer.OSM",
    "name": "mapnik",
    "visibility": True,
    "fixed": True,
    "group": "background"
}]

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

# Use kombu broker by default
# REDIS_URL = 'redis://localhost:6379/1'
# BROKER_URL = REDIS_URL
# CELERY_RESULT_BACKEND = REDIS_URL
CELERYD_HIJACK_ROOT_LOGGER = True
CELERYD_CONCURENCY = 1
# Set this to False to run real async tasks
CELERY_ALWAYS_EAGER = True
CELERYD_LOG_FILE = None
CELERY_REDIRECT_STDOUTS = True
CELERYD_LOG_LEVEL = 1

# Haystack Search Backend Configuration. To enable,
# first install the following:
# - pip install django-haystack
# - pip install elasticsearch==2.4.0
# - pip install woosh
# - pip install pyelasticsearch
# Set HAYSTACK_SEARCH to True
# Run "python manage.py rebuild_index"
# HAYSTACK_SEARCH = False
# Avoid permissions prefiltering
SKIP_PERMS_FILTER = False
# Update facet counts from Haystack
HAYSTACK_FACET_COUNTS = True
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
        'URL': 'http://127.0.0.1:9200/',
        'INDEX_NAME': 'haystack',
    },
    #    'db': {
    #        'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
    #        'EXCLUDED_INDEXES': ['thirdpartyapp.search_indexes.BarIndex'],
    #        }
}
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
# HAYSTACK_SEARCH_RESULTS_PER_PAGE = 20

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                      '%(thread)d %(message)s'
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
            'level': 'DEBUG',
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
            "handlers": ["console"], "level": "DEBUG", },
        "gsconfig.catalog": {
            "handlers": ["console"], "level": "DEBUG", },
        "owslib": {
            "handlers": ["console"], "level": "DEBUG", },
        "pycsw": {
            "handlers": ["console"], "level": "ERROR", },
    },
}

CORS_ORIGIN_ALLOW_ALL = True

GEOIP_PATH = "/usr/local/share/GeoIP"

MONITORING_ENABLED = False
# add following lines to your local settings to enable monitoring
if MONITORING_ENABLED:
    INSTALLED_APPS += ('geonode.contrib.monitoring',)
    MIDDLEWARE_CLASSES += ('geonode.contrib.monitoring.middleware.MonitoringMiddleware',)
    MONITORING_CONFIG = None
    MONITORING_SERVICE_NAME = 'local-geonode'
