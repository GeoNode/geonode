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

# Django settings for the GeoNode project.
import ast
import os
import re
import sys
from datetime import timedelta
from distutils.util import strtobool
from urlparse import urlparse, urlunparse, urljoin

import django
import dj_database_url
#
# General Django development settings
#
from django.conf.global_settings import DATETIME_INPUT_FORMATS
from geonode import get_version
from kombu import Queue, Exchange


# GeoNode Version
VERSION = get_version()

# Defines the directory that contains the settings file as the PROJECT_ROOT
# It is used for relative settings elsewhere.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Setting debug to true makes Django serve static media and
# present pretty error pages.
DEBUG = strtobool(os.getenv('DEBUG', 'True'))

# Set to True to load non-minified versions of (static) client dependencies
# Requires to set-up Node and tools that are required for static development
# otherwise it will raise errors for the missing non-minified dependencies
DEBUG_STATIC = strtobool(os.getenv('DEBUG_STATIC', 'False'))

# Define email service on GeoNode
EMAIL_ENABLE = strtobool(os.getenv('EMAIL_ENABLE', 'False'))

if EMAIL_ENABLE:
    EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND',
                              default='django.core.mail.backends.smtp.EmailBackend')
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 25
    EMAIL_HOST_USER = ''
    EMAIL_HOST_PASSWORD = ''
    EMAIL_USE_TLS = False
    DEFAULT_FROM_EMAIL = 'GeoNode <no-reply@geonode.org>'
else:
    EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND',
                              default='django.core.mail.backends.console.EmailBackend')

# This is needed for integration tests, they require
# geonode to be listening for GeoServer auth requests.
if django.VERSION[0] == 1 and django.VERSION[1] >= 11 and django.VERSION[2] >= 2:
    pass
else:
    DJANGO_LIVE_TEST_SERVER_ADDRESS = 'localhost:8000'

try:
    # try to parse python notation, default in dockerized env
    ALLOWED_HOSTS = ast.literal_eval(os.getenv('ALLOWED_HOSTS'))
except ValueError:
    # fallback to regular list of values separated with misc chars
    ALLOWED_HOSTS = ['localhost', 'django', 'geonode'] if os.getenv('ALLOWED_HOSTS') is None \
        else re.split(r' *[,|:|;] *', os.getenv('ALLOWED_HOSTS'))

# AUTH_IP_WHITELIST property limits access to users/groups REST endpoints
# to only whitelisted IP addresses.
#
# Empty list means 'allow all'
#
# If you need to limit 'api' REST calls to only some specific IPs
# fill the list like below:
#
# AUTH_IP_WHITELIST = ['192.168.1.158', '192.168.1.159']
AUTH_IP_WHITELIST = []

# Make this unique, and don't share it with anybody.
_DEFAULT_SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'
SECRET_KEY = os.getenv('SECRET_KEY', _DEFAULT_SECRET_KEY)

DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///{path}'.format(
        path=os.path.join(PROJECT_ROOT, 'development.db')
    )
)

# DATABASE_URL = 'postgresql://test_geonode:test_geonode@localhost:5432/geonode'

# Defines settings for development

# since GeoDjango is in use, you should use gis-enabled engine, for example:
# 'ENGINE': 'django.contrib.gis.db.backends.postgis'
# see https://docs.djangoproject.com/en/1.8/ref/contrib/gis/db-api/#module-django.contrib.gis.db.backends for
# detailed list of supported backends and notes.
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
}

if os.getenv('DEFAULT_BACKEND_DATASTORE'):
    GEODATABASE_URL = os.getenv('GEODATABASE_URL',
                                'postgis://\
geonode_data:geonode_data@localhost:5432/geonode_data')
    DATABASES[os.getenv('DEFAULT_BACKEND_DATASTORE')] = dj_database_url.parse(
        GEODATABASE_URL, conn_max_age=600
    )

MANAGERS = ADMINS = os.getenv('ADMINS', [])

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = os.getenv('TIME_ZONE', "UTC")

SITE_ID = int(os.getenv('SITE_ID', '1'))

USE_TZ = True
USE_I18N = strtobool(os.getenv('USE_I18N', 'True'))
USE_L10N = strtobool(os.getenv('USE_I18N', 'True'))

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', "en")


_DEFAULT_LANGUAGES = (
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
    ('pt-br', 'Portuguese (Brazil)'),
    ('ru', 'Russian'),
    ('vi', 'Vietnamese'),
    ('ko', '한국어'),
    ('am', 'Amharic'),
    ('km', 'Khmer'),
    ('pl', 'Polish'),
    ('sv', 'Swedish'),
    ('th', 'ไทย'),
    ('uk', 'Ukranian'),
    ('si', 'Sinhala'),
    ('ta', 'Tamil'),
    ('tl', 'Tagalog'),
)

LANGUAGES = os.getenv('LANGUAGES', _DEFAULT_LANGUAGES)

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


AUTH_USER_MODEL = os.getenv('AUTH_USER_MODEL', 'people.Profile')

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.SHA1PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    # 'django.contrib.auth.hashers.Argon2PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    # 'django.contrib.auth.hashers.BCryptPasswordHasher',
]

MODELTRANSLATION_LANGUAGES = ['en', ]

MODELTRANSLATION_DEFAULT_LANGUAGE = 'en'

MODELTRANSLATION_FALLBACK_LANGUAGES = ('en',)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(PROJECT_ROOT, "uploaded"))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = os.getenv('MEDIA_URL', "/uploaded/")
LOCAL_MEDIA_URL = os.getenv('LOCAL_MEDIA_URL', "/uploaded/")

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.getenv('STATIC_ROOT',
                        os.path.join(PROJECT_ROOT, "static_root")
                        )

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = os.getenv('STATIC_URL', "/static/")

# Additional directories which hold static files
_DEFAULT_STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "static"),
]

STATICFILES_DIRS = os.getenv('STATICFILES_DIRS', _DEFAULT_STATICFILES_DIRS)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    #    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Location of translation files
_DEFAULT_LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, "locale"),
)

LOCALE_PATHS = os.getenv('LOCALE_PATHS', _DEFAULT_LOCALE_PATHS)

# Location of url mappings
ROOT_URLCONF = os.getenv('ROOT_URLCONF', 'geonode.urls')

GEONODE_CORE_APPS = (
    # GeoNode internal apps
    'geonode.api',
    'geonode.base',
    'geonode.layers',
    'geonode.maps',
    'geonode.documents',
    'geonode.security',
    'geonode.catalogue',
)

GEONODE_INTERNAL_APPS = (
    # GeoNode internal apps
    'geonode.people',
    'geonode.client',
    'geonode.themes',
    'geonode.proxy',
    'geonode.social',
    'geonode.groups',
    'geonode.services',

    # QGIS Server Apps
    # Only enable this if using QGIS Server
    # 'geonode.qgis_server',

    # GeoServer Apps
    # Geoserver needs to come last because
    # it's signals may rely on other apps' signals.
    'geonode.geoserver',
    'geonode.upload',
    'geonode.tasks',
    'geonode.messaging',
)

GEONODE_CONTRIB_APPS = (
    # GeoNode Contrib Apps
    # 'geonode.contrib.dynamic',
    # 'geonode.contrib.exif',
    # 'geonode.contrib.favorite',
    # 'geonode.contrib.geogig',
    # 'geonode.contrib.geosites',
    # 'geonode.contrib.nlp',
    # 'geonode.contrib.slack',
    # 'geonode.contrib.createlayer',
    # 'geonode.contrib.datastore_shards',
    'geonode.contrib.metadataxsl',
    'geonode.contrib.api_basemaps',
    'geonode.contrib.ows_api',
)

# Uncomment the following line to enable contrib apps
GEONODE_APPS = GEONODE_CORE_APPS + GEONODE_INTERNAL_APPS + GEONODE_CONTRIB_APPS

INSTALLED_APPS = (

    'modeltranslation',

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

    # Utility
    'dj_pagination',
    'taggit',
    'treebeard',
    'geoexplorer',
    'leaflet',
    'bootstrap3_datetime',
    'django_extensions',
    'django_basic_auth',
    'autocomplete_light',
    'mptt',
    # 'crispy_forms',

    # 'djkombu',
    # 'djcelery',
    # 'kombu.transport.django',

    'storages',
    'floppyforms',

    # Theme
    "pinax_theme_bootstrap",
    'django_forms_bootstrap',

    # Social
    'avatar',
    'dialogos',
    # 'pinax.comments',
    'agon_ratings',
    # 'pinax.ratings',
    'announcements',
    'actstream',
    'user_messages',
    'tastypie',
    'polymorphic',
    'guardian',
    'oauth2_provider',
    'corsheaders',

    'invitations',

    # login with external providers
    'allauth',
    'allauth.account',
    'allauth.socialaccount',

    # Django REST Framework
    'rest_framework',

    # GeoNode
    'geonode',
) + GEONODE_APPS

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

# Documents application
ALLOWED_DOCUMENT_TYPES = [
    'doc', 'docx', 'gif', 'jpg', 'jpeg', 'ods', 'odt', 'odp', 'pdf', 'png',
    'ppt', 'pptx', 'rar', 'sld', 'tif', 'tiff', 'txt', 'xls', 'xlsx', 'xml',
    'zip', 'gz', 'qml'
]
MAX_DOCUMENT_SIZE = int(os.getenv('MAX_DOCUMENT_SIZE ', '2'))  # MB

# DOCUMENT_TYPE_MAP and DOCUMENT_MIMETYPE_MAP update enumerations in
# documents/enumerations.py and should only
# need to be uncommented if adding other types
# to settings.ALLOWED_DOCUMENT_TYPES

# DOCUMENT_TYPE_MAP = {}
# DOCUMENT_MIMETYPE_MAP = {}

UNOCONV_ENABLE = strtobool(os.getenv('UNOCONV_ENABLE', 'False'))

if UNOCONV_ENABLE:
    UNOCONV_EXECUTABLE = os.getenv('UNOCONV_EXECUTABLE', '/usr/bin/unoconv')
    UNOCONV_TIMEOUT = int(os.getenv('UNOCONV_TIMEOUT', 30))  # seconds

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
        'console': {
            'level': 'INFO',
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
            "handlers": ["console"], "level": "INFO", },
        "geonode.qgis_server": {
            "handlers": ["console"], "level": "ERROR", },
        "gsconfig.catalog": {
            "handlers": ["console"], "level": "ERROR", },
        "owslib": {
            "handlers": ["console"], "level": "ERROR", },
        "pycsw": {
            "handlers": ["console"], "level": "ERROR", },
        "celery": {
            "handlers": ["console"], "level": "ERROR", },
    },
}

#
# Customizations to built in Django settings required by GeoNode
#

# Django automatically includes the "templates" dir in all the INSTALLED_APPS.
TEMPLATES = [
    {
        'NAME': 'GeoNode Project Templates',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
                # 'django.core.context_processors.debug',
                # 'django.core.context_processors.i18n',
                # 'django.core.context_processors.tz',
                # 'django.core.context_processors.media',
                # 'django.core.context_processors.static',
                # 'django.core.context_processors.request',
                'geonode.context_processors.resource_urls',
                'geonode.geoserver.context_processors.geoserver_urls',
                'geonode.themes.context_processors.custom_theme'
            ],
            # Either remove APP_DIRS or remove the 'loaders' option.
            # 'loaders': [
            #      'django.template.loaders.filesystem.Loader',
            #      'django.template.loaders.app_directories.Loader',
            # ],
            'debug': DEBUG,
        },
    },
]

MIDDLEWARE_CLASSES = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'dj_pagination.middleware.PaginationMiddleware',
    # The setting below makes it possible to serve different languages per
    # user depending on things like headers in HTTP requests.
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Security settings
    'django.middleware.security.SecurityMiddleware',

    # This middleware allows to print private layers for the users that have
    # the permissions to view them.
    # It sets temporary the involved layers as public before restoring the
    # permissions.
    # Beware that for few seconds the involved layers are public there could be
    # risks.
    # 'geonode.middleware.PrintProxyMiddleware',

    # If you use SessionAuthenticationMiddleware, be sure it appears before OAuth2TokenMiddleware.
    # SessionAuthenticationMiddleware is NOT required for using
    # django-oauth-toolkit.
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
)

# Security stuff
MIDDLEWARE_CLASSES += ('django.middleware.security.SecurityMiddleware',)
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# Replacement of default authentication backend in order to support
# permissions per object.
AUTHENTICATION_BACKENDS = (
    'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

OAUTH2_PROVIDER = {
    'SCOPES': {
        'read': 'Read scope',
        'write': 'Write scope',
        'groups': 'Access to your groups'
    },

    'CLIENT_ID_GENERATOR_CLASS': 'oauth2_provider.generators.ClientIdGenerator',
}
# authorized exempt urls needed for oauth when GeoNode is set to lockdown
AUTH_EXEMPT_URLS = ('/api/o/*', '/api/roles', '/api/adminRole', '/api/users',)

ANONYMOUS_USER_ID = os.getenv('ANONYMOUS_USER_ID', '-1')
GUARDIAN_GET_INIT_ANONYMOUS_USER = os.getenv(
    'GUARDIAN_GET_INIT_ANONYMOUS_USER',
    'geonode.people.models.get_anonymous_user_instance'
)

# Whether the uplaoded resources should be public and downloadable by default
# or not
DEFAULT_ANONYMOUS_VIEW_PERMISSION = strtobool(
    os.getenv('DEFAULT_ANONYMOUS_VIEW_PERMISSION', 'True')
)
DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION = strtobool(
    os.getenv('DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION', 'True')
)

#
# Settings for default search size
#
DEFAULT_SEARCH_SIZE = int(os.getenv('DEFAULT_SEARCH_SIZE', '10'))


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
    'FETCH_RELATIONS': True,
    'USE_PREFETCH': False,
    'USE_JSONFIELD': True,
    'GFK_FETCH_DEPTH': 1,
}


# Email for users to contact admins.
THEME_ACCOUNT_CONTACT_EMAIL = os.getenv(
    'THEME_ACCOUNT_CONTACT_EMAIL', 'admin@example.com'
)

#
# Test Settings
#

on_travis = ast.literal_eval(os.environ.get('ON_TRAVIS', 'False'))
integration_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTEGRATION', 'False'))

# Setting a custom test runner to avoid running the tests for
# some problematic 3rd party apps
# Default Nose Test Suite
TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
TEST_RUNNER_KEEPDB = 0
TEST_RUNNER_PARALLEL = 0

# GeoNode test suite
# TEST_RUNNER = 'geonode.tests.suite.runner.DjangoParallelTestSuiteRunner'
# TEST_RUNNER_WORKER_MAX = 3
# TEST_RUNNER_WORKER_COUNT = 'auto'
# TEST_RUNNER_NOT_THREAD_SAFE = None
# TEST_RUNNER_PARENT_TIMEOUT = 10
# TEST_RUNNER_WORKER_TIMEOUT = 10

TEST = 'test' in sys.argv
INTEGRATION = 'geonode.tests.integration' in sys.argv

# Arguments for the test runner
NOSE_ARGS = [
    '--nocapture',
    '--detailed-errors',
]

#
# GeoNode specific settings
#
SITEURL = os.getenv('SITEURL', "http://localhost:8000/")

# we need hostname for deployed
_surl = urlparse(SITEURL)
HOSTNAME = _surl.hostname

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith('/'):
    SITEURL = '{}/'.format(SITEURL)

# Login and logout urls override
LOGIN_URL = os.getenv('LOGIN_URL', '/account/login/')
LOGOUT_URL = os.getenv('LOGOUT_URL', '/account/logout/')

LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGIN_REDIRECT_URL = os.getenv('LOGIN_REDIRECT_URL', SITEURL)
ACCOUNT_LOGOUT_REDIRECT_URL =  os.getenv('LOGOUT_REDIRECT_URL', SITEURL)

# Backend
DEFAULT_WORKSPACE = os.getenv('DEFAULT_WORKSPACE', 'geonode')
CASCADE_WORKSPACE = os.getenv('CASCADE_WORKSPACE', 'geonode')

OGP_URL = os.getenv('OGP_URL', "http://geodata.tufts.edu/solr/select")

# Topic Categories list should not be modified (they are ISO). In case you
# absolutely need it set to True this variable
MODIFY_TOPICCATEGORY = strtobool(os.getenv('MODIFY_TOPICCATEGORY', 'False'))

MISSING_THUMBNAIL = os.getenv(
    'MISSING_THUMBNAIL', 'geonode/img/missing_thumb.png'
)

# Search Snippet Cache Time in Seconds
CACHE_TIME = int(os.getenv('CACHE_TIME', '0'))

GEOSERVER_LOCATION = os.getenv(
    'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
)

GEOSERVER_PUBLIC_LOCATION = os.getenv(
    #  'GEOSERVER_PUBLIC_LOCATION', urljoin(SITEURL, '/geoserver')
    'GEOSERVER_PUBLIC_LOCATION', GEOSERVER_LOCATION
)

OGC_SERVER_DEFAULT_USER = os.getenv(
    'GEOSERVER_ADMIN_USER', 'admin'
)

OGC_SERVER_DEFAULT_PASSWORD = os.getenv(
    'GEOSERVER_ADMIN_PASSWORD', 'geoserver'
)

GEOFENCE_SECURITY_ENABLED = False if TEST and not INTEGRATION else True

# OGC (WMS/WFS/WCS) Server Settings
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
        'GEOFENCE_SECURITY_ENABLED': GEOFENCE_SECURITY_ENABLED,
        'GEOFENCE_URL': os.getenv('GEOFENCE_URL', 'internal:/'),
        'GEOGIG_ENABLED': False,
        'WMST_ENABLED': False,
        'BACKEND_WRITE_ENABLED': True,
        'WPS_ENABLED': False,
        'LOG_FILE': '%s/geoserver/data/logs/geoserver.log'
        % os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir)),
        # Set to name of database in DATABASES dictionary to enable
        # 'datastore',
        'DATASTORE': os.getenv('DEFAULT_BACKEND_DATASTORE',''),
        'PG_GEOGIG': False,
        # 'CACHE': ".cache"  # local cache file to for HTTP requests
        'TIMEOUT': int(os.getenv('OGC_REQUEST_TIMEOUT', '60'))  # number of seconds to allow for HTTP requests
    }
}

USE_GEOSERVER = 'geonode.geoserver' in INSTALLED_APPS and OGC_SERVER['default']['BACKEND'] == 'geonode.geoserver'

# Uploader Settings
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000
UPLOADER = {
    'BACKEND': os.getenv('DEFAULT_BACKEND_UPLOADER', 'geonode.rest'),
    # 'BACKEND': 'geonode.importer',
    'OPTIONS': {
        'TIME_ENABLED': strtobool(os.getenv('TIME_ENABLED', 'False')),
        'MOSAIC_ENABLED': strtobool(os.getenv('MOSAIC_ENABLED', 'False')),
        'GEOGIG_ENABLED': strtobool(os.getenv('GEOGIG_ENABLED', 'False')),
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
        'URL': urljoin(SITEURL, '/catalogue/csw'),
        # 'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
        # 'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',

        # login credentials (for GeoNetwork)
        # 'USER': 'admin',
        # 'PASSWORD': 'admin',

        # 'ALTERNATES_ONLY': True,
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
        'server': {
            'home': '.',
            'url': CATALOGUE['default']['URL'],
            'encoding': 'UTF-8',
            'language': LANGUAGE_CODE,
            'maxrecords': '20',
            'pretty_print': 'true',
            # 'domainquerytype': 'range',
            'domaincounts': 'true',
            'profiles': 'apiso,ebrim',
        },
        'manager': {
            # authentication/authorization is handled by Django
            'transactions': 'false',
            'allowed_ips': '*',
            # 'csw_harvest_pagesize': '10',
        },
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
DEFAULT_MAP_CRS = "EPSG:3857"

DEFAULT_LAYER_FORMAT = "image/png"

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (0, 0)

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = 0

ALT_OSM_BASEMAPS = ast.literal_eval(os.environ.get('ALT_OSM_BASEMAPS', 'False'))
CARTODB_BASEMAPS = ast.literal_eval(os.environ.get('CARTODB_BASEMAPS', 'False'))
STAMEN_BASEMAPS = ast.literal_eval(os.environ.get('STAMEN_BASEMAPS', 'False'))
THUNDERFOREST_BASEMAPS = ast.literal_eval(os.environ.get('THUNDERFOREST_BASEMAPS', 'False'))
MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN', None)
BING_API_KEY = os.environ.get('BING_API_KEY', None)
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', None)

# handle timestamps like 2017-05-30 16:04:00.719 UTC
if django.VERSION[0] == 1 and django.VERSION[1] >= 9:
    _DATETIME_INPUT_FORMATS = ['%Y-%m-%d %H:%M:%S.%f %Z', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S%Z']
else:
    _DATETIME_INPUT_FORMATS = ('%Y-%m-%d %H:%M:%S.%f %Z', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S%Z')
DATETIME_INPUT_FORMATS = DATETIME_INPUT_FORMATS + _DATETIME_INPUT_FORMATS

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

DISPLAY_SOCIAL = strtobool(os.getenv('DISPLAY_SOCIAL', 'True'))
DISPLAY_COMMENTS = strtobool(os.getenv('DISPLAY_COMMENTS', 'True'))
DISPLAY_RATINGS = strtobool(os.getenv('DISPLAY_RATINGS', 'True'))
DISPLAY_WMS_LINKS = strtobool(os.getenv('DISPLAY_WMS_LINKS', 'True'))

SOCIAL_ORIGINS = [{
    "label": "Email",
    "url": "mailto:?subject={name}&body={url}",
    "css_class": "email"
}, {
    "label": "Facebook",
    "url": "http://www.facebook.com/sharer.php?u={url}",
    "css_class": "fb"
}, {
    "label": "Twitter",
    "url": "https://twitter.com/share?url={url}&hashtags={hashtags}",
    "css_class": "tw"
}, {
    "label": "Google +",
    "url": "https://plus.google.com/share?url={url}",
    "css_class": "gp"
}]

# CKAN Query String Parameters names pulled from
# http://tinyurl.com/og2jofn
CKAN_ORIGINS = [{
    "label": "Humanitarian Data Exchange (HDX)",
    "url": "https://data.hdx.rwlabs.org/dataset/new?title={name}&"
    "dataset_date={date}&notes={abstract}&caveats={caveats}",
    "css_class": "hdx"
}]
# SOCIAL_ORIGINS.extend(CKAN_ORIGINS)

# Setting TWITTER_CARD to True will enable Twitter Cards
# https://dev.twitter.com/cards/getting-started
# Be sure to replace @GeoNode with your organization or site's twitter handle.
TWITTER_CARD = strtobool(os.getenv('TWITTER_CARD', 'True'))
TWITTER_SITE = '@GeoNode'
TWITTER_HASHTAGS = ['geonode']

OPENGRAPH_ENABLED = strtobool(os.getenv('OPENGRAPH_ENABLED', 'True'))

# Enable Licenses User Interface
# Regardless of selection, license field stil exists as a field in the
# Resourcebase model.
# Detail Display: above, below, never
# Metadata Options: verbose, light, never
LICENSES = {
    'ENABLED': True,
    'DETAIL': 'above',
    'METADATA': 'verbose',
}

SRID = {
    'DETAIL': 'never',
}

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'

# Require users to authenticate before using Geonode
LOCKDOWN_GEONODE = strtobool(os.getenv('LOCKDOWN_GEONODE', 'False'))

# Add additional paths (as regular expressions) that don't require
# authentication.
AUTH_EXEMPT_URLS = ()

# A tuple of hosts the proxy can send requests to.
PROXY_ALLOWED_HOSTS = ()

# The proxy to use when making cross origin requests.
PROXY_URL = '/proxy/?url=' if DEBUG else None

# Haystack Search Backend Configuration. To enable,
# first install the following:
# - pip install django-haystack
# - pip install pyelasticsearch
# Set HAYSTACK_SEARCH to True
# Run "python manage.py rebuild_index"
HAYSTACK_SEARCH = strtobool(os.getenv('HAYSTACK_SEARCH', 'False'))
# Avoid permissions prefiltering
SKIP_PERMS_FILTER = strtobool(os.getenv('SKIP_PERMS_FILTER', 'False'))
# Update facet counts from Haystack
HAYSTACK_FACET_COUNTS = strtobool(os.getenv('HAYSTACK_FACET_COUNTS', 'True'))
if HAYSTACK_SEARCH:
    if 'haystack' not in INSTALLED_APPS:
        INSTALLED_APPS += ('haystack', )
    HAYSTACK_CONNECTIONS = {
       'default': {
           'ENGINE': 'haystack.backends.elasticsearch2_backend.Elasticsearch2SearchEngine',
           'URL': os.getenv('HAYSTACK_ENGINE_URL', 'http://127.0.0.1:9200/'),
           'INDEX_NAME': os.getenv('HAYSTACK_ENGINE_INDEX_NAME', 'haystack'),
           },
       }
    HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'
    HAYSTACK_SEARCH_RESULTS_PER_PAGE = int(os.getenv('HAYSTACK_SEARCH_RESULTS_PER_PAGE', '200'))

# Available download formats
DOWNLOAD_FORMATS_METADATA = [
    'Atom', 'DIF', 'Dublin Core', 'ebRIM', 'FGDC', 'ISO',
]
DOWNLOAD_FORMATS_VECTOR = [
    'JPEG', 'PDF', 'PNG', 'Zipped Shapefile', 'GML 2.0', 'GML 3.1.1', 'CSV',
    'Excel', 'GeoJSON', 'KML', 'View in Google Earth', 'Tiles',
    'QGIS layer file (.qlr)',
    'QGIS project file (.qgs)',
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
    'GML',
    'GZIP',
    'QGIS layer file (.qlr)',
    'QGIS project file (.qgs)',
    'Zipped All Files'
]

ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE = strtobool(
    os.getenv('ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE', 'False'))

TASTYPIE_DEFAULT_FORMATS = ['json']

# gravatar settings
AUTO_GENERATE_AVATAR_SIZES = (
    20, 30, 32, 40, 50, 65, 70, 80, 100, 140, 200, 240
)

# Number of results per page listed in the GeoNode search pages
CLIENT_RESULTS_LIMIT = int(os.getenv('CLIENT_RESULTS_LIMIT', '20'))

# Number of items returned by the apis 0 equals no limit
API_LIMIT_PER_PAGE = int(os.getenv('API_LIMIT_PER_PAGE', '200'))
API_INCLUDE_REGIONS_COUNT = strtobool(
    os.getenv('API_INCLUDE_REGIONS_COUNT', 'False'))

LEAFLET_CONFIG = {
    'TILES': [
        # Find tiles at:
        # http://leaflet-extras.github.io/leaflet-providers/preview/

        # Stamen toner lite.
        ('Watercolor',
         'http://{s}.tile.stamen.com/watercolor/{z}/{x}/{y}.png',
         'Map tiles by <a href="http://stamen.com">Stamen Design</a>, \
         <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> \
         &mdash; Map data &copy; \
         <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, \
         <a href="http://creativecommons.org/licenses/by-sa/2.0/"> \
         CC-BY-SA</a>'),
        ('Toner Lite',
         'http://{s}.tile.stamen.com/toner-lite/{z}/{x}/{y}.png',
         'Map tiles by <a href="http://stamen.com">Stamen Design</a>, \
         <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> \
         &mdash; Map data &copy; \
         <a href="http://openstreetmap.org">OpenStreetMap</a> contributors, \
         <a href="http://creativecommons.org/licenses/by-sa/2.0/"> \
         CC-BY-SA</a>'),
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
        'leaflet-opacity': {
            'css': 'lib/css/Control.Opacity.css',
            'js': 'lib/js/Control.Opacity.js',
            'auto-include': True,
        },
        'leaflet-navbar': {
            'css': 'lib/css/Leaflet.NavBar.css',
            'js': 'lib/js/Leaflet.NavBar.js',
            'auto-include': True,
        },
        'leaflet-measure': {
            'css': 'lib/css/leaflet-measure.css',
            'js': 'lib/js/leaflet-measure.js',
            'auto-include': True,
        },
    },
    'SRID': 3857,
    'RESET_VIEW': False
}

if not DEBUG_STATIC:
    # if not DEBUG_STATIC, use minified css and js
    LEAFLET_CONFIG['PLUGINS'] = {
        'leaflet-plugins': {
            'js': 'lib/js/leaflet-plugins.min.js',
            'css': 'lib/css/leaflet-plugins.min.css',
            'auto-include': True,
        }
    }

# option to enable/disable resource unpublishing for administrators
RESOURCE_PUBLISHING = False

# Settings for EXIF contrib app
EXIF_ENABLED = False

# Settings for NLP contrib app
NLP_ENABLED = False
NLP_LOCATION_THRESHOLD = 1.0
NLP_LIBRARY_PATH = os.getenv('NLP_LIBRARY_PATH', "/opt/MITIE/mitielib")
NLP_MODEL_PATH = os.getenv(
    'NLP_MODEL_PATH', "/opt/MITIE/MITIE-models/english/ner_model.dat")

# Settings for Slack contrib app
SLACK_ENABLED = False
SLACK_WEBHOOK_URLS = [
    "https://hooks.slack.com/services/T000/B000/XX"
]

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

GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY = 'geoext'  # DEPRECATED use HOOKSET instead
GEONODE_CLIENT_HOOKSET = "geonode.client.hooksets.GeoExtHookSet"

# To enable the REACT based Client enable those
"""
if 'geonode-client' not in INSTALLED_APPS:
    INSTALLED_APPS += ('geonode-client', )
GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY = 'react'  # DEPRECATED use HOOKSET instead
GEONODE_CLIENT_HOOKSET = "geonode.client.hooksets.ReactHookSet"
"""

# To enable the Leaflet based Client enable those
"""
GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY = 'leaflet'  # DEPRECATED use HOOKSET instead
GEONODE_CLIENT_HOOKSET = "geonode.client.hooksets.LeafletHookSet"
"""

# To enable the MapLoom based Client enable those
"""
GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY = 'maploom'  # DEPRECATED use HOOKSET instead
GEONODE_CLIENT_HOOKSET = "geonode.client.hooksets.MaploomHookSet"
CORS_ORIGIN_WHITELIST = (
    HOSTNAME
)
"""

# To enable the WorldMap based Client enable those
"""
GEONODE_CLIENT_HOOKSET = "geonode.client.hooksets.WorldMapHookSet"
CORS_ORIGIN_WHITELIST = (
    HOSTNAME
)
"""

SERVICE_UPDATE_INTERVAL = 0

SEARCH_FILTERS = {
    'TEXT_ENABLED': True,
    'TYPE_ENABLED': True,
    'CATEGORIES_ENABLED': True,
    'OWNERS_ENABLED': True,
    'KEYWORDS_ENABLED': True,
    'H_KEYWORDS_ENABLED': True,
    'T_KEYWORDS_ENABLED': True,
    'DATE_ENABLED': True,
    'REGION_ENABLED': True,
    'EXTENT_ENABLED': True,
}

# Make Free-Text Kaywords writable from users or read-only
# - if True only admins can edit free-text kwds from admin dashboard
FREETEXT_KEYWORDS_READONLY = False

# notification settings
NOTIFICATION_ENABLED = True or TEST
#PINAX_NOTIFICATIONS_LANGUAGE_MODEL = "people.Profile"

# notifications backends
_EMAIL_BACKEND = "pinax.notifications.backends.email.EmailBackend"
PINAX_NOTIFICATIONS_BACKENDS = [
    ("email", _EMAIL_BACKEND),
]
PINAX_NOTIFICATIONS_HOOKSET = "pinax.notifications.hooks.DefaultHookSet"

# Queue non-blocking notifications.
PINAX_NOTIFICATIONS_QUEUE_ALL = False
PINAX_NOTIFICATIONS_LOCK_WAIT_TIMEOUT = -1

# explicitly define NOTIFICATION_LOCK_LOCATION
# NOTIFICATION_LOCK_LOCATION = <path>

# pinax.notifications
# or notification
NOTIFICATIONS_MODULE = 'pinax.notifications'

# set to true to have multiple recipients in /message/create/
USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS = False

if NOTIFICATION_ENABLED:
    if NOTIFICATIONS_MODULE not in INSTALLED_APPS:
        INSTALLED_APPS += (NOTIFICATIONS_MODULE, )

# async signals can be the same as broker url
# but they should have separate setting anyway
# use amqp://localhost for local rabbitmq server
"""
    sudo apt-get install -y erlang
    sudo apt-get install rabbitmq-server

    sudo update-rc.d rabbitmq-server enable

    sudo rabbitmqctl stop_app
    sudo rabbitmqctl reset
    sudo rabbitmqctl start_app

    sudo rabbitmqctl list_queues
"""
# Disabling the heartbeat because workers seems often disabled in flower,
# thanks to http://stackoverflow.com/a/14831904/654755
BROKER_HEARTBEAT = 0

# Avoid long running and retried tasks to be run over-and-over again.
BROKER_TRANSPORT_OPTIONS = {
    'fanout_prefix': True,
    'fanout_patterns': True,
    'socket_timeout': 60,
    'visibility_timeout': 86400
}

ASYNC_SIGNALS = ast.literal_eval(os.environ.get('ASYNC_SIGNALS', 'False'))
RABBITMQ_SIGNALS_BROKER_URL = 'amqp://localhost:5672'
REDIS_SIGNALS_BROKER_URL = 'redis://localhost:6379/0'
LOCAL_SIGNALS_BROKER_URL = 'memory://'

if ASYNC_SIGNALS:
    _BROKER_URL = os.environ.get('BROKER_URL', RABBITMQ_SIGNALS_BROKER_URL)
    # _BROKER_URL =  = os.environ.get('BROKER_URL', REDIS_SIGNALS_BROKER_URL)

    CELERY_RESULT_BACKEND = _BROKER_URL
else:
    _BROKER_URL = LOCAL_SIGNALS_BROKER_URL

# Note:BROKER_URL is deprecated in favour of CELERY_BROKER_URL
CELERY_BROKER_URL = _BROKER_URL

CELERY_RESULT_PERSISTENT = False

# Allow to recover from any unknown crash.
CELERY_ACKS_LATE = True

# Set this to False in order to run async
CELERY_TASK_ALWAYS_EAGER = False if ASYNC_SIGNALS else True
CELERY_TASK_IGNORE_RESULT = True

# I use these to debug kombu crashes; we get a more informative message.
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Set Tasks Queues
# CELERY_TASK_DEFAULT_QUEUE = "default"
# CELERY_TASK_DEFAULT_EXCHANGE = "default"
# CELERY_TASK_DEFAULT_EXCHANGE_TYPE = "direct"
# CELERY_TASK_DEFAULT_ROUTING_KEY = "default"
CELERY_TASK_CREATE_MISSING_QUEUES = True
GEONODE_EXCHANGE = Exchange("default", type="direct", durable=True)
GEOSERVER_EXCHANGE = Exchange("geonode", type="topic", durable=False)
CELERY_TASK_QUEUES = (
    Queue('default', GEONODE_EXCHANGE, routing_key='default'),
    Queue('geonode', GEONODE_EXCHANGE, routing_key='geonode'),
    Queue('update', GEONODE_EXCHANGE, routing_key='update'),
    Queue('cleanup', GEONODE_EXCHANGE, routing_key='cleanup'),
    Queue('email', GEONODE_EXCHANGE, routing_key='email'),
)

if USE_GEOSERVER:
    CELERY_TASK_QUEUES += (
        Queue("broadcast", GEOSERVER_EXCHANGE, routing_key="#"),
        Queue("email.events", GEOSERVER_EXCHANGE, routing_key="email"),
        Queue("all.geoserver", GEOSERVER_EXCHANGE, routing_key="geoserver.#"),
        Queue("geoserver.catalog", GEOSERVER_EXCHANGE, routing_key="geoserver.catalog"),
        Queue("geoserver.data", GEOSERVER_EXCHANGE, routing_key="geoserver.catalog"),
        Queue("geoserver.events", GEOSERVER_EXCHANGE, routing_key="geonode.geoserver"),
        Queue("notifications.events", GEOSERVER_EXCHANGE, routing_key="notifications"),
        Queue("geonode.layer.viewer", GEOSERVER_EXCHANGE, routing_key="geonode.viewer"),
    )

# from celery.schedules import crontab
# EXAMPLES
# CELERY_BEAT_SCHEDULE = {
#     ...
#     'update_feeds': {
#         'task': 'arena.social.tasks.Update',
#         'schedule': crontab(minute='*/6'),
#     },
#     ...
#     'send-summary-every-hour': {
#        'task': 'summary',
#         # There are 4 ways we can handle time, read further
#        'schedule': 3600.0,
#         # If you're using any arguments
#        'args': (‘We don’t need any’,),
#     },
#     # Executes every Friday at 4pm
#     'send-notification-on-friday-afternoon': {
#          'task': 'my_app.tasks.send_notification',
#          'schedule': crontab(hour=16, day_of_week=5),
#     },
# }

# Half a day is enough
CELERY_TASK_RESULT_EXPIRES = 43200

# Sometimes, Ask asks us to enable this to debug issues.
# BTW, it will save some CPU cycles.
CELERY_DISABLE_RATE_LIMITS = False
CELERY_SEND_TASK_EVENTS = True
CELERY_WORKER_DISABLE_RATE_LIMITS = False
CELERY_WORKER_SEND_TASK_EVENTS = True

# Allow our remote workers to get tasks faster if they have a
# slow internet connection (yes Gurney, I'm thinking of you).
CELERY_MESSAGE_COMPRESSION = 'gzip'

# The default beiing 5000, we need more than this.
CELERY_MAX_CACHED_RESULTS = 32768

# NOTE: I don't know if this is compatible with upstart.
CELERYD_POOL_RESTARTS = True

CELERY_TRACK_STARTED = True
CELERY_SEND_TASK_SENT_EVENT = True

# Disabled by default and I like it, because we use Sentry for this.
#CELERY_SEND_TASK_ERROR_EMAILS = False

# AWS S3 Settings

S3_STATIC_ENABLED = ast.literal_eval(os.environ.get('S3_STATIC_ENABLED', 'False'))
S3_MEDIA_ENABLED = ast.literal_eval(os.environ.get('S3_MEDIA_ENABLED', 'False'))

# Required to run Sync Media to S3
AWS_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')

AWS_STORAGE_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', '')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
AWS_S3_BUCKET_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME

AWS_QUERYSTRING_AUTH = False

if S3_STATIC_ENABLED:
    STATICFILES_LOCATION = 'static'
    STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    STATIC_URL = "https://%s/%s/" % (AWS_S3_BUCKET_DOMAIN,
                                     STATICFILES_LOCATION)

if S3_MEDIA_ENABLED:
    MEDIAFILES_LOCATION = 'media'
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
    MEDIA_URL = "https://%s/%s/" % (AWS_S3_BUCKET_DOMAIN, MEDIAFILES_LOCATION)


# Load additonal basemaps, see geonode/contrib/api_basemap/README.md
try:
    from geonode.contrib.api_basemaps import *  # flake8: noqa
except ImportError:
    pass

# Require users to authenticate before using Geonode
if LOCKDOWN_GEONODE:
    MIDDLEWARE_CLASSES = MIDDLEWARE_CLASSES + \
        ('geonode.security.middleware.LoginRequiredMiddleware',)

# for windows users check if they didn't set GEOS and GDAL in local_settings.py
# maybe they set it as a windows environment
if os.name == 'nt':
    if "GEOS_LIBRARY_PATH" not in locals() \
            or "GDAL_LIBRARY_PATH" not in locals():
        if os.environ.get("GEOS_LIBRARY_PATH", None) \
                and os.environ.get("GDAL_LIBRARY_PATH", None):
            GEOS_LIBRARY_PATH = os.environ.get('GEOS_LIBRARY_PATH')
            GDAL_LIBRARY_PATH = os.environ.get('GDAL_LIBRARY_PATH')
        else:
            # maybe it will be found regardless if not it will throw 500 error
            from django.contrib.gis.geos import GEOSGeometry  # flake8: noqa


# define the urls after the settings are overridden
if USE_GEOSERVER:
    PUBLIC_GEOSERVER = {
        "source": {
            "title": "GeoServer - Public Layers",
            "attribution": "&copy; %s" % SITEURL,
            "ptype": "gxp_wmscsource",
            "url": OGC_SERVER['default']['PUBLIC_LOCATION'] + "ows",
            "restUrl": "/gs/rest"
        }
    }
    LOCAL_GEOSERVER = {
        "source": {
            "title": "GeoServer - Private Layers",
            "attribution": "&copy; %s" % SITEURL,
            "ptype": "gxp_wmscsource",
            "url": "/gs/ows",
            "restUrl": "/gs/rest"
        }
    }
    baselayers = MAP_BASELAYERS
    # MAP_BASELAYERS = [PUBLIC_GEOSERVER, LOCAL_GEOSERVER]
    MAP_BASELAYERS = [PUBLIC_GEOSERVER]
    MAP_BASELAYERS.extend(baselayers)

# Keywords thesauri
# e.g. THESAURI = [{'name':'inspire_themes', 'required':True, 'filter':True}, {'name':'inspire_concepts', 'filter':True}, ]
# Required: (boolean, optional, default false) mandatory while editing metadata (not implemented yet)
# Filter: (boolean, optional, default false) a filter option on that thesaurus will appear in the main search page
# THESAURI = [{'name':'inspire_themes', 'required':False, 'filter':True}]
THESAURI = []

# use when geonode.contrib.risks is in installed apps.
RISKS = {'DEFAULT_LOCATION': None,
         'PDF_GENERATOR': {'NAME': 'wkhtml2pdf',
                           'BIN': '/usr/bin/wkhtml2pdf',
                           'ARGS': []}}

# Each uploaded Layer must be approved by an Admin before becoming visible
ADMIN_MODERATE_UPLOADS = False

# add following lines to your local settings to enable monitoring
MONITORING_ENABLED = ast.literal_eval(os.environ.get('MONITORING_ENABLED', 'False'))
MONITORING_HOST_NAME = os.getenv("MONITORING_HOST_NAME", HOSTNAME)
MONITORING_SERVICE_NAME = 'geonode'

# how long monitoring data should be stored
MONITORING_DATA_TTL = timedelta(days=7)

# this will disable csrf check for notification config views,
# use with caution - for dev purpose only
MONITORING_DISABLE_CSRF = False

if MONITORING_ENABLED:
    if 'geonode.contrib.monitoring' not in INSTALLED_APPS:
        INSTALLED_APPS += ('geonode.contrib.monitoring',)
    if 'geonode.contrib.monitoring.middleware.MonitoringMiddleware' not in MIDDLEWARE_CLASSES:
        MIDDLEWARE_CLASSES += \
            ('geonode.contrib.monitoring.middleware.MonitoringMiddleware',)

GEOIP_PATH = os.path.join(PROJECT_ROOT, 'GeoIPCities.dat')
# If this option is enabled, Resources belonging to a Group won't be
# visible by others
GROUP_PRIVATE_RESOURCES = False

# If this option is enabled, Groups will become strictly Mandatory on
# Metadata Wizard
GROUP_MANDATORY_RESOURCES = False

# A boolean which specifies wether to display the email in user's profile
SHOW_PROFILE_EMAIL = False

# Enables cross origin requests for geonode-client
MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS = strtobool(os.getenv(
    'MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS',
    'False'
))

ACCOUNT_OPEN_SIGNUP = True
ACCOUNT_APPROVAL_REQUIRED = strtobool(
    os.getenv('ACCOUNT_APPROVAL_REQUIRED', 'False')
)
ACCOUNT_ADAPTER = 'geonode.people.adapters.LocalAccountAdapter'
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_ADAPTER = 'geonode.people.adapters.SocialAccountAdapter'

SOCIALACCOUNT_AUTO_SIGNUP = False

# Uncomment this to enable Linkedin and Facebook login
# INSTALLED_APPS += (
#    'allauth.socialaccount.providers.linkedin_oauth2',
#    'allauth.socialaccount.providers.facebook',
# )

SOCIALACCOUNT_PROVIDERS = {
    'linkedin_oauth2': {
        'SCOPE': [
            'r_emailaddress',
            'r_basicprofile',
        ],
        'PROFILE_FIELDS': [
            'emailAddress',
            'firstName',
            'headline',
            'id',
            'industry',
            'lastName',
            'pictureUrl',
            'positions',
            'publicProfileUrl',
            'location',
            'specialties',
            'summary',
        ]
    },
    'facebook': {
        'METHOD': 'oauth2',
        'SCOPE': [
            'email',
            'public_profile',
        ],
        'FIELDS': [
            'id',
            'email',
            'name',
            'first_name',
            'last_name',
            'verified',
            'locale',
            'timezone',
            'link',
            'gender',
        ]
    },
}

SOCIALACCOUNT_PROFILE_EXTRACTORS = {
    "facebook": "geonode.people.profileextractors.FacebookExtractor",
    "linkedin_oauth2": "geonode.people.profileextractors.LinkedInExtractor",
}

INVITATIONS_ADAPTER = ACCOUNT_ADAPTER

# Choose thumbnail generator -- this is the default generator
THUMBNAIL_GENERATOR = "geonode.layers.utils.create_gs_thumbnail_geonode"
THUMBNAIL_GENERATOR_DEFAULT_BG = r"http://a.tile.openstreetmap.org/{z}/{x}/{y}.png"

GEOTIFF_IO_ENABLED = strtobool(
    os.getenv('GEOTIFF_IO_ENABLED', 'False')
)

# if your public geoserver location does not use HTTPS,
# you must set GEOTIFF_IO_BASE_URL to use http://
# for example, http://app.geotiff.io
GEOTIFF_IO_BASE_URL = os.getenv(
    'GEOTIFF_IO_BASE_URL', 'https://app.geotiff.io'
)

# WorldMap settings
USE_WORLDMAP = strtobool(os.getenv('USE_WORLDMAP', 'False'))

if USE_WORLDMAP:
    # WorldMap requirest PostgreSQL and PostGIS
    PG_HOST = os.getenv('PG_HOST', 'localhost')
    PG_USERNAME = os.getenv('PG_USERNAME', 'worldmap')
    PG_PASSWORD = os.getenv('PG_PASSWORD', 'worldmap')
    PG_WORLDMAP_DJANGO_DB = os.getenv('PG_WORLDMAP_DJANGO_DB', 'geonode')
    PG_WORLDMAP_UPLOADS_DB = os.getenv('PG_WORLDMAP_UPLOADS_DB', 'geonode_data')
    DATABASES = {
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': PG_WORLDMAP_DJANGO_DB,
            'USER': PG_USERNAME,
            'PASSWORD': PG_PASSWORD,
            'HOST': PG_HOST,
            'PORT': '5432',
            'CONN_TOUT': 900,
        },
        # vector datastore for uploads
        'datastore': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            # 'ENGINE': '', # Empty ENGINE name disables
            'NAME': PG_WORLDMAP_UPLOADS_DB,
            'USER': PG_USERNAME,
            'PASSWORD': PG_PASSWORD,
            'HOST': PG_HOST,
            'PORT': '5432',
            'CONN_TOUT': 900,
        }
    }
    GEONODE_CLIENT_LOCATION = '/static/worldmap_client/'
    GAZETTEER_DB_ALIAS = 'default'
    INSTALLED_APPS += (
            'geoexplorer-worldmap',
            'geonode.contrib.worldmap.gazetteer',
            'geonode.contrib.worldmap.wm_extra',
            'geonode.contrib.createlayer',
        )
    GAZETTEER_FULLTEXTSEARCH = False
    WM_COPYRIGHT_URL = "http://gis.harvard.edu/"
    WM_COPYRIGHT_TEXT = "Center for Geographic Analysis"
    USE_GAZETTEER = True
    DEFAULT_MAP_ABSTRACT = """
        <h3>The Harvard WorldMap Project</h3>
        <p>WorldMap is an open source web mapping system that is currently
        under construction. It is built to assist academic research and
        teaching as well as the general public and supports discovery,
        investigation, analysis, visualization, communication and archiving
        of multi-disciplinary, multi-source and multi-format data,
        organized spatially and temporally.</p>
    """
    # these are optionals
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'your-key-here')
    USE_HYPERMAP = strtobool(os.getenv('USE_HYPERMAP', 'False'))
    HYPERMAP_REGISTRY_URL = os.getenv('HYPERMAP_REGISTRY_URL', 'http://localhost:8001')
    SOLR_URL = os.getenv('SOLR_URL', 'http://localhost:8983/solr/hypermap/select/')
    MAPPROXY_URL = os.getenv('MAPPROXY_URL', 'http://localhost:8001')
