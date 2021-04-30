# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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
from urllib.parse import urlparse, urlunparse
from geonode.settings import *

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(PROJECT_ROOT, "uploaded"))

STATIC_ROOT = os.getenv('STATIC_ROOT',
                        os.path.join(PROJECT_ROOT, "static_root")
                        )

SECRET_KEY = 'qM-??jCGzC46L$wd'

SITEURL = "http://localhost:8000/"

# we need hostname for deployed
_surl = urlparse(SITEURL)
HOSTNAME = _surl.hostname

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith('/'):
    SITEURL = f'{SITEURL}/'

ALLOWED_HOSTS = ['localhost', 'geonode', 'django', 'geonode.example.com']

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend'
)

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

SESSION_EXPIRED_CONTROL_ENABLED = False
# if 'geonode.security.middleware.SessionControlMiddleware' in MIDDLEWARE:
#     _middleware = list(MIDDLEWARE)
#     _middleware.remove('geonode.security.middleware.SessionControlMiddleware')
#     MIDDLEWARE = tuple(_middleware)

# Django ParallelTestSuite
TEST_RUNNER = 'geonode.tests.suite.runner.GeoNodeBaseSuiteDiscoverRunner'
TEST_RUNNER_KEEPDB = os.environ.get('TEST_RUNNER_KEEPDB', 1)
TEST_RUNNER_PARALLEL = os.environ.get('TEST_RUNNER_PARALLEL', 1)

# Backend
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'upload_test',
        'USER': 'geonode',
        'PASSWORD': 'geonode',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 0,
        'CONN_TOUT': 5,
        'OPTIONS': {
            'connect_timeout': 5
        }
    },
    'datastore': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'upload_test',
        'USER': 'geonode',
        'PASSWORD': 'geonode',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 0,
        'CONN_TOUT': 5,
        'OPTIONS': {
            'connect_timeout': 5
        }
    }
}

GEOSERVER_LOCATION = os.getenv(
    'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
)

GEOSERVER_PUBLIC_HOST = os.getenv(
    'GEOSERVER_PUBLIC_HOST', SITE_HOST_NAME
)

GEOSERVER_PUBLIC_PORT = os.getenv(
    'GEOSERVER_PUBLIC_PORT', 8080
)

_default_public_location = f'http://{GEOSERVER_PUBLIC_HOST}:{GEOSERVER_PUBLIC_PORT}/geoserver/' if GEOSERVER_PUBLIC_PORT else f'http://{GEOSERVER_PUBLIC_HOST}/geoserver/'

GEOSERVER_WEB_UI_LOCATION = os.getenv(
    'GEOSERVER_WEB_UI_LOCATION', GEOSERVER_LOCATION
)

GEOSERVER_PUBLIC_LOCATION = os.getenv(
    'GEOSERVER_PUBLIC_LOCATION', _default_public_location
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
        'WEB_UI_LOCATION': GEOSERVER_WEB_UI_LOCATION,
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
        'WMST_ENABLED': False,
        'BACKEND_WRITE_ENABLED': True,
        'WPS_ENABLED': False,
        'LOG_FILE': f'{os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))}/geoserver/data/logs/geoserver.log',
        # Set to dictionary identifier of database containing spatial data in DATABASES dictionary to enable
        'DATASTORE': 'datastore',
        'TIMEOUT': int(os.getenv('OGC_REQUEST_TIMEOUT', '60')),
        'MAX_RETRIES': int(os.getenv('OGC_REQUEST_MAX_RETRIES', '0')),
        'BACKOFF_FACTOR': float(os.getenv('OGC_REQUEST_BACKOFF_FACTOR', '0.0')),
        'POOL_MAXSIZE': int(os.getenv('OGC_REQUEST_POOL_MAXSIZE', '10')),
        'POOL_CONNECTIONS': int(os.getenv('OGC_REQUEST_POOL_CONNECTIONS', '10')),
    }
}

# If you want to enable Mosaics use the following configuration
UPLOADER = {
    # 'BACKEND': 'geonode.rest',
    'BACKEND': 'geonode.importer',
    'OPTIONS': {
        'TIME_ENABLED': True,
        'MOSAIC_ENABLED': False,
    },
    'SUPPORTED_CRS': [
        'EPSG:4326',
        'EPSG:3785',
        'EPSG:3857',
        'EPSG:32647',
        'EPSG:32736'
    ],
    'SUPPORTED_EXT': [
        '.shp',
        '.csv',
        '.kml',
        '.kmz',
        '.json',
        '.geojson',
        '.tif',
        '.tiff',
        '.geotiff',
        '.gml',
        '.xml'
    ]
}

# Settings for MONITORING plugin
MONITORING_ENABLED = ast.literal_eval(os.environ.get('MONITORING_ENABLED', 'False'))
USER_ANALYTICS_ENABLED = ast.literal_eval(
    os.getenv('USER_ANALYTICS_ENABLED', os.environ.get('MONITORING_ENABLED', 'False')))
USER_ANALYTICS_GZIP = ast.literal_eval(os.getenv('USER_ANALYTICS_GZIP',
                                                 os.environ.get('MONITORING_ENABLED', 'False')))

MONITORING_CONFIG = os.getenv("MONITORING_CONFIG", None)
MONITORING_HOST_NAME = os.getenv("MONITORING_HOST_NAME", HOSTNAME)
MONITORING_SERVICE_NAME = os.getenv("MONITORING_SERVICE_NAME", 'local-geonode')

# how long monitoring data should be stored
MONITORING_DATA_TTL = timedelta(days=int(os.getenv("MONITORING_DATA_TTL", 7)))

# this will disable csrf check for notification config views,
# use with caution - for dev purpose only
MONITORING_DISABLE_CSRF = ast.literal_eval(os.environ.get('MONITORING_DISABLE_CSRF', 'False'))

if MONITORING_ENABLED:
    if 'geonode.monitoring' not in INSTALLED_APPS:
        INSTALLED_APPS += ('geonode.monitoring',)
    if 'geonode.monitoring.middleware.MonitoringMiddleware' not in MIDDLEWARE:
        MIDDLEWARE += \
            ('geonode.monitoring.middleware.MonitoringMiddleware',)

    # skip certain paths to not to mud stats too much
    MONITORING_SKIP_PATHS = ('/api/o/',
                             '/monitoring/',
                             '/admin',
                             '/jsi18n',
                             STATIC_URL,
                             MEDIA_URL,
                             re.compile('^/[a-z]{2}/admin/'),
                             )

    # configure aggregation of past data to control data resolution
    # list of data age, aggregation, in reverse order
    # for current data, 1 minute resolution
    # for data older than 1 day, 1-hour resolution
    # for data older than 2 weeks, 1 day resolution
    MONITORING_DATA_AGGREGATION = (
        (timedelta(seconds=0), timedelta(minutes=1),),
        (timedelta(days=1), timedelta(minutes=60),),
        (timedelta(days=14), timedelta(days=1),),
    )

    CELERY_BEAT_SCHEDULE['collect_metrics'] = {
        'task': 'geonode.monitoring.tasks.collect_metrics',
        'schedule': 60.0,
    }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
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
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    "loggers": {
        "django": {
            "handlers": ["console"], "level": "ERROR", },
        "geonode": {
            "handlers": ["console"], "level": "ERROR", },
        "geonode.qgis_server": {
            "handlers": ["console"], "level": "ERROR", },
        "geoserver-restconfig.catalog": {
            "handlers": ["console"], "level": "ERROR", },
        "owslib": {
            "handlers": ["console"], "level": "ERROR", },
        "pycsw": {
            "handlers": ["console"], "level": "ERROR", },
        "celery": {
            'handlers': ["console"], 'level': 'ERROR', },
    },
}
