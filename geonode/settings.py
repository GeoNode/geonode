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
import os
import re
import ast
import sys
import subprocess
import dj_database_url
from schema import Optional
from datetime import timedelta
from distutils.util import strtobool  # noqa
from urllib.parse import urlparse, urljoin

#
# General Django development settings
#
from django.conf.global_settings import DATETIME_INPUT_FORMATS
from geonode import get_version
from kombu import Queue, Exchange
from kombu.serialization import register

from . import serializer

SILENCED_SYSTEM_CHECKS = [
    '1_8.W001',
    'fields.W340',
    'auth.W004',
    'urls.W002',
    'drf_spectacular.W001',
    'drf_spectacular.W002'
]

# GeoNode Version
VERSION = get_version()

DEFAULT_CHARSET = "utf-8"

# Defines the directory that contains the settings file as the PROJECT_ROOT
# It is used for relative settings elsewhere.
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# Setting debug to true makes Django serve static media and
# present pretty error pages.
DEBUG = ast.literal_eval(os.getenv('DEBUG', 'True'))

# Set to True to load non-minified versions of (static) client dependencies
# Requires to set-up Node and tools that are required for static development
# otherwise it will raise errors for the missing non-minified dependencies
DEBUG_STATIC = ast.literal_eval(os.getenv('DEBUG_STATIC', 'False'))

FORCE_SCRIPT_NAME = os.getenv('FORCE_SCRIPT_NAME', '')

# Define email service on GeoNode
EMAIL_ENABLE = ast.literal_eval(os.getenv('EMAIL_ENABLE', 'False'))

if EMAIL_ENABLE:
    EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND',
                              default='django.core.mail.backends.smtp.EmailBackend')
    EMAIL_HOST = os.getenv('DJANGO_EMAIL_HOST', 'localhost')
    EMAIL_PORT = os.getenv('DJANGO_EMAIL_PORT', 25)
    EMAIL_HOST_USER = os.getenv('DJANGO_EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('DJANGO_EMAIL_HOST_PASSWORD', '')
    EMAIL_USE_TLS = ast.literal_eval(os.getenv('DJANGO_EMAIL_USE_TLS', 'False'))
    EMAIL_USE_SSL = ast.literal_eval(os.getenv('DJANGO_EMAIL_USE_SSL', 'False'))
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'GeoNode <no-reply@geonode.org>')
else:
    EMAIL_BACKEND = os.getenv('DJANGO_EMAIL_BACKEND',
                              default='django.core.mail.backends.console.EmailBackend')

# Make this unique, and don't share it with anybody.
_DEFAULT_SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'
SECRET_KEY = os.getenv('SECRET_KEY', _DEFAULT_SECRET_KEY)

SITE_HOST_SCHEMA = os.getenv('SITE_HOST_SCHEMA', 'http')
SITE_HOST_NAME = os.getenv('SITE_HOST_NAME', 'localhost')
SITE_HOST_PORT = os.getenv('SITE_HOST_PORT', 8000)
_default_siteurl = f"{SITE_HOST_SCHEMA}://{SITE_HOST_NAME}:{SITE_HOST_PORT}/" \
                   if SITE_HOST_PORT else f"{SITE_HOST_SCHEMA}://{SITE_HOST_NAME}/"
SITEURL = os.getenv('SITEURL', _default_siteurl)

# we need hostname for deployed
_surl = urlparse(SITEURL)
HOSTNAME = _surl.hostname

# add trailing slash to site url. geoserver url will be relative to this
if not SITEURL.endswith('/'):
    SITEURL = f'{SITEURL}/'

_DB_PATH = os.path.join(PROJECT_ROOT, 'development.db')
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    f'spatialite:///{_DB_PATH}'
)

if DATABASE_URL.startswith("spatialite"):
    try:
        spatialite_proc = subprocess.run(["spatialite", "-version"], stdout=subprocess.PIPE)
        spatialite_version = int(spatialite_proc.stdout.decode()[0])
        if spatialite_version < 5:
            # To workaround Shapely/Spatialite interaction bug for Spatialite < 5
            from shapely import speedups
            speedups.enable()
    except FileNotFoundError as ex:
        print(ex)

# DATABASE_URL = 'postgresql://test_geonode:test_geonode@localhost:5432/geonode'

# Defines settings for development

# since GeoDjango is in use, you should use gis-enabled engine, for example:
# 'ENGINE': 'django.contrib.gis.db.backends.postgis'
# see https://docs.djangoproject.com/en/1.8/ref/contrib/gis/db-api/#module-django.contrib.gis.db.backends for
# detailed list of supported backends and notes.
GEONODE_DB_CONN_MAX_AGE = int(os.getenv('GEONODE_DB_CONN_MAX_AGE', 0))
GEONODE_DB_CONN_TOUT = int(os.getenv('GEONODE_DB_CONN_TOUT', 5))

_db_conf = dj_database_url.parse(
    DATABASE_URL,
    conn_max_age=GEONODE_DB_CONN_MAX_AGE)

if 'CONN_TOUT' in _db_conf:
    _db_conf['CONN_TOUT'] = GEONODE_DB_CONN_TOUT
if 'postgresql' in DATABASE_URL or 'postgis' in DATABASE_URL:
    if 'OPTIONS' not in _db_conf:
        _db_conf['OPTIONS'] = {}
    _db_conf['OPTIONS'].update({
        'connect_timeout': GEONODE_DB_CONN_TOUT,
    })

DATABASES = {
    'default': _db_conf
}

if os.getenv('DEFAULT_BACKEND_DATASTORE'):
    GEODATABASE_URL = os.getenv('GEODATABASE_URL',
                                'postgis://\
geonode_data:geonode_data@localhost:5432/geonode_data')
    DATABASES[os.getenv('DEFAULT_BACKEND_DATASTORE')] = dj_database_url.parse(
        GEODATABASE_URL, conn_max_age=GEONODE_DB_CONN_MAX_AGE
    )
    _geo_db = DATABASES[os.getenv('DEFAULT_BACKEND_DATASTORE')]
    if 'CONN_TOUT' in DATABASES['default']:
        _geo_db['CONN_TOUT'] = DATABASES['default']['CONN_TOUT']
    if 'postgresql' in GEODATABASE_URL or 'postgis' in GEODATABASE_URL:
        _geo_db['OPTIONS'] = DATABASES['default']['OPTIONS'] if 'OPTIONS' in DATABASES['default'] else {}
        _geo_db['OPTIONS'].update({
            'connect_timeout': GEONODE_DB_CONN_TOUT,
        })

    DATABASES[os.getenv('DEFAULT_BACKEND_DATASTORE')] = _geo_db

# If set to 'True' it will refresh/regenrate all resource links everytime a 'migrate' will be performed
UPDATE_RESOURCE_LINKS_AT_MIGRATE = ast.literal_eval(os.getenv('UPDATE_RESOURCE_LINKS_AT_MIGRATE', 'False'))

MANAGERS = ADMINS = os.getenv('ADMINS', [])

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = os.getenv('TIME_ZONE', "UTC")

SITE_ID = int(os.getenv('SITE_ID', '1'))

USE_TZ = True
USE_I18N = ast.literal_eval(os.getenv('USE_I18N', 'True'))
USE_L10N = ast.literal_eval(os.getenv('USE_I18N', 'True'))

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', "en")

_DEFAULT_LANGUAGES = """(
    ('af', 'Afrikaans'),
    ('sq', 'Albanian'),
    ('am', 'Amharic'),
    ('ar', 'Arabic'),
    ('id', 'Bahasa Indonesia'),
    ('bn', 'Bengali'),
    ('de', 'Deutsch'),
    ('en', 'English'),
    ('es', 'Español'),
    ('fr', 'Français'),
    ('it', 'Italiano'),
    ('km', 'Khmer'),
    ('nl', 'Nederlands'),
    ('ne', 'Nepali'),
    ('fa', 'Persian'),
    ('pl', 'Polish'),
    ('pt', 'Portuguese'),
    ('pt-br', 'Portuguese (Brazil)'),
    ('ru', 'Russian'),
    ('si', 'Sinhala'),
    ('sw', 'Swahili'),
    ('sv', 'Swedish'),
    ('tl', 'Tagalog'),
    ('ta', 'Tamil'),
    ('uk', 'Ukranian'),
    ('vi', 'Vietnamese'),
    ('el', 'Ελληνικά'),
    ('th', 'ไทย'),
    ('zh-cn', '中文'),
    ('ja', '日本語'),
    ('ko', '한국어'),
    ('sk', 'Slovensky'),
)"""

LANGUAGES = ast.literal_eval(os.getenv('LANGUAGES', _DEFAULT_LANGUAGES))

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
        'name_local': 'tamil',
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

# Location of translation files
_DEFAULT_LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, "locale"),
)

LOCALE_PATHS = os.getenv('LOCALE_PATHS', _DEFAULT_LOCALE_PATHS)

# Location of url mappings
ROOT_URLCONF = os.getenv('ROOT_URLCONF', 'geonode.urls')

# ########################################################################### #
# MEDIA / STATICS STORAGES SETTINGS
# ########################################################################### #

STATICFILES_LOCATION = 'static'
MEDIAFILES_LOCATION = 'uploaded'
THUMBNAIL_LOCATION = 'thumbs'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.getenv('MEDIA_ROOT', os.path.join(PROJECT_ROOT, MEDIAFILES_LOCATION))

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = os.getenv('MEDIA_URL', f'{FORCE_SCRIPT_NAME}/{MEDIAFILES_LOCATION}/')
LOCAL_MEDIA_URL = os.getenv('LOCAL_MEDIA_URL', f'{FORCE_SCRIPT_NAME}/{MEDIAFILES_LOCATION}/')

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.getenv('STATIC_ROOT',
                        os.path.join(PROJECT_ROOT, 'static_root')
                        )

# Cache Bustin Settings: enable WhiteNoise compression and caching support
# ref: http://whitenoise.evans.io/en/stable/django.html#add-compression-and-caching-support
CACHE_BUSTING_STATIC_ENABLED = ast.literal_eval(os.environ.get('CACHE_BUSTING_STATIC_ENABLED', 'False'))

# Optionally Use a Content-Delivery Network
# ref: http://whitenoise.evans.io/en/stable/django.html#use-a-content-delivery-network
STATIC_HOST = os.environ.get('STATIC_URL', '')

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
if FORCE_SCRIPT_NAME:
    STATIC_URL = f"{STATIC_HOST}/{FORCE_SCRIPT_NAME}/{STATICFILES_LOCATION}/"
else:
    STATIC_URL = f"{STATIC_HOST}/{STATICFILES_LOCATION}/"

# Additional directories which hold static files
_DEFAULT_STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, STATICFILES_LOCATION),
]

STATICFILES_DIRS = os.getenv('STATICFILES_DIRS', _DEFAULT_STATICFILES_DIRS)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    # 'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

CACHES = {
    # DUMMY CACHE FOR DEVELOPMENT
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    },

    # MEMCACHED EXAMPLE
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
    #     'LOCATION': '127.0.0.1:11211',
    # },

    # FILECACHE EXAMPLE
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
    #     'LOCATION': '/tmp/django_cache',
    # },

    # DATABASE EXAMPLE -> python manage.py createcachetable
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
    #     'LOCATION': 'my_cache_table',
    # },

    # LOCAL-MEMORY CACHING
    # 'default': {
    #     'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    #     'LOCATION': 'geonode-cache',
    #     'TIMEOUT': 10,
    #     'OPTIONS': {
    #         'MAX_ENTRIES': 10000
    #     }
    # },

    'resources': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'TIMEOUT': 600,
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}

# Whitenoise Settings - ref.: http://whitenoise.evans.io/en/stable/django.html
WHITENOISE_MANIFEST_STRICT = ast.literal_eval(os.getenv('WHITENOISE_MANIFEST_STRICT', 'False'))
COMPRESS_STATIC_FILES = ast.literal_eval(os.getenv('COMPRESS_STATIC_FILES', 'False'))

MEMCACHED_ENABLED = ast.literal_eval(os.getenv('MEMCACHED_ENABLED', 'False'))
MEMCACHED_BACKEND = os.getenv('MEMCACHED_BACKEND', 'django.core.cache.backends.memcached.PyMemcacheCache')
MEMCACHED_LOCATION = os.getenv('MEMCACHED_LOCATION', '127.0.0.1:11211')
MEMCACHED_LOCK_EXPIRE = int(os.getenv('MEMCACHED_LOCK_EXPIRE', 3600))
MEMCACHED_LOCK_TIMEOUT = int(os.getenv('MEMCACHED_LOCK_TIMEOUT', 10))

if MEMCACHED_ENABLED:
    CACHES['default'] = {
        'BACKEND': MEMCACHED_BACKEND,
        'LOCATION': MEMCACHED_LOCATION,
    }

# Define the STATICFILES_STORAGE accordingly
if not DEBUG and CACHE_BUSTING_STATIC_ENABLED:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
elif COMPRESS_STATIC_FILES:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.StaticFilesStorage'

GEONODE_CORE_APPS = (
    # GeoNode internal apps
    'geonode.api',
    'geonode.base',
    'geonode.br',
    'geonode.layers',
    'geonode.maps',
    'geonode.geoapps',
    'geonode.documents',
    'geonode.security',
    'geonode.catalogue',
    'geonode.catalogue.metadataxsl',
    'geonode.harvesting',
)

# GeoNode Apps
GEONODE_APPS_ENABLE = ast.literal_eval(os.getenv("GEONODE_APPS_ENABLE", "True"))
GEONODE_APPS_NAME = os.getenv("GEONODE_APPS_NAME", "Apps")
GEONODE_APPS_NAV_MENU_ENABLE = ast.literal_eval(os.getenv("GEONODE_APPS_NAV_MENU_ENABLE", "True"))

GEONODE_INTERNAL_APPS = (
    # GeoNode internal apps
    'geonode.people',
    'geonode.client',
    'geonode.themes',
    'geonode.proxy',
    'geonode.social',
    'geonode.groups',
    'geonode.services',
    'geonode.management_commands_http',

    'geonode.resource',
    'geonode.resource.processing',
    'geonode.storage',

    # GeoServer Apps
    # Geoserver needs to come last because
    # it's signals may rely on other apps' signals.
    'geonode.geoserver',
    'geonode.geoserver.processing',
    'geonode.upload',
    'geonode.tasks',
    'geonode.messaging',
    'geonode.favorite',
    'geonode.monitoring'
)

GEONODE_CONTRIB_APPS = (
    # GeoNode Contrib Apps
)

# Uncomment the following line to enable contrib apps
GEONODE_APPS = GEONODE_CORE_APPS + GEONODE_INTERNAL_APPS + GEONODE_CONTRIB_APPS

INSTALLED_APPS = (

    # Boostrap admin theme
    # 'django_admin_bootstrapped.bootstrap3',
    # 'django_admin_bootstrapped',

    # Apps bundled with Django
    'modeltranslation',
    'dal',
    'dal_select2',
    'grappelli',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.sitemaps',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.gis',
    'sequences.apps.SequencesConfig',

    # Utility
    'dj_pagination',
    'taggit',
    'treebeard',
    'bootstrap3_datetime',
    'django_filters',
    'mptt',
    'storages',
    'floppyforms',
    'tinymce',
    'widget_tweaks',
    'django_celery_results',
    'markdownify',
    'django_user_agents',

    # REST APIs
    'rest_framework',
    'rest_framework_gis',
    'dynamic_rest',
    'drf_spectacular',

    # Theme
    'django_select2',
    'django_forms_bootstrap',

    # Social
    'avatar',
    'pinax.ratings',
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

    # GeoNode
    'geonode',
)

markdown_white_listed_tags = [
    'a', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7', 'ul', 'li', 'span', 'blockquote', 'strong', 'code'
]

MARKDOWNIFY = {
    "default": {
        "WHITELIST_TAGS": os.getenv('MARKDOWNIFY_WHITELIST_TAGS', markdown_white_listed_tags)
    }
}

MARKDOWNIFY_STRIP = os.getenv('MARKDOWNIFY_STRIP', False)

INSTALLED_APPS += GEONODE_APPS

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'oauth2_provider.contrib.rest_framework.OAuth2Authentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'dynamic_rest.renderers.DynamicBrowsableAPIRenderer',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'geonode.base.api.exceptions.geonode_exception_handler'
}
REST_FRAMEWORK_EXTENSIONS = {
    'DEFAULT_PARENT_LOOKUP_KWARG_NAME_PREFIX': '',
}

REST_API_DEFAULT_PAGE = os.getenv('REST_API_DEFAULT_PAGE', 1)
REST_API_DEFAULT_PAGE_SIZE = os.getenv('REST_API_DEFAULT_PAGE_SIZE', 10)
REST_API_DEFAULT_PAGE_QUERY_PARAM = os.getenv('REST_API_DEFAULT_PAGE_QUERY_PARAM', 'page_size')

DYNAMIC_REST = {
    # DEBUG: enable/disable internal debugging
    'DEBUG': False,

    # ENABLE_BROWSABLE_API: enable/disable the browsable API.
    # It can be useful to disable it in production.
    'ENABLE_BROWSABLE_API': True,

    # ENABLE_LINKS: enable/disable relationship links
    'ENABLE_LINKS': False,

    # ENABLE_SERIALIZER_CACHE: enable/disable caching of related serializers
    'ENABLE_SERIALIZER_CACHE': False,

    # ENABLE_SERIALIZER_OPTIMIZATIONS: enable/disable representation speedups
    'ENABLE_SERIALIZER_OPTIMIZATIONS': True,

    # DEFER_MANY_RELATIONS: automatically defer many-relations, unless
    # `deferred=False` is explicitly set on the field.
    'DEFER_MANY_RELATIONS': False,

    # MAX_PAGE_SIZE: global setting for max page size.
    # Can be overriden at the viewset level.
    'MAX_PAGE_SIZE': None,

    # PAGE_QUERY_PARAM: global setting for the pagination query parameter.
    # Can be overriden at the viewset level.
    'PAGE_QUERY_PARAM': 'page',

    # PAGE_SIZE: global setting for page size.
    # Can be overriden at the viewset level.
    'PAGE_SIZE': None,

    # PAGE_SIZE_QUERY_PARAM: global setting for the page size query parameter.
    # Can be overriden at the viewset level.
    'PAGE_SIZE_QUERY_PARAM': 'per_page',

    # ADDITIONAL_PRIMARY_RESOURCE_PREFIX: String to prefix additional
    # instances of the primary resource when sideloading.
    'ADDITIONAL_PRIMARY_RESOURCE_PREFIX': '+',

    # Enables host-relative links.  Only compatible with resources registered
    # through the dynamic router.  If a resource doesn't have a canonical
    # path registered, links will default back to being resource-relative urls
    'ENABLE_HOST_RELATIVE_LINKS': True
}

GRAPPELLI_ADMIN_TITLE = os.getenv('GRAPPELLI_ADMIN_TITLE', 'GeoNode')

# Documents application
try:
    # try to parse python notation, default in dockerized env
    ALLOWED_DOCUMENT_TYPES = ast.literal_eval(os.getenv('ALLOWED_DOCUMENT_TYPES'))
except ValueError:
    # fallback to regular list of values separated with misc chars
    ALLOWED_DOCUMENT_TYPES = [
        'txt', 'log', 'doc', 'docx', 'ods', 'odt', 'sld', 'qml', 'xls', 'xlsx', 'xml',
        'bm', 'bmp', 'dwg', 'dxf', 'fif', 'gif', 'jpg', 'jpe', 'jpeg', 'png', 'tif',
        'tiff', 'pbm', 'odp', 'ppt', 'pptx', 'pdf', 'tar', 'tgz', 'rar', 'gz', '7z',
        'zip', 'aif', 'aifc', 'aiff', 'au', 'mp3', 'mpga', 'wav', 'afl', 'avi', 'avs',
        'fli', 'mp2', 'mp4', 'mpg', 'ogg', 'webm', '3gp', 'flv', 'vdo', 'glb', 'pcd', 'gltf'
    ] if os.getenv('ALLOWED_DOCUMENT_TYPES') is None \
        else re.split(r' *[,|:;] *', os.getenv('ALLOWED_DOCUMENT_TYPES'))

MAX_DOCUMENT_SIZE = int(os.getenv('MAX_DOCUMENT_SIZE ', '2'))  # MB

# DOCUMENT_TYPE_MAP and DOCUMENT_MIMETYPE_MAP update enumerations in
# documents/enumerations.py and should only
# need to be uncommented if adding other types
# to settings.ALLOWED_DOCUMENT_TYPES

# DOCUMENT_TYPE_MAP = {}
# DOCUMENT_MIMETYPE_MAP = {}

UNOCONV_ENABLE = ast.literal_eval(os.getenv('UNOCONV_ENABLE', 'False'))

if UNOCONV_ENABLE:
    UNOCONV_EXECUTABLE = os.getenv('UNOCONV_EXECUTABLE', '/usr/bin/unoconv')
    UNOCONV_TIMEOUT = int(os.getenv('UNOCONV_TIMEOUT', 30))  # seconds

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

#
# Test Settings
#
on_travis = ast.literal_eval(os.environ.get('ON_TRAVIS', 'False'))
core_tests = ast.literal_eval(os.environ.get('TEST_RUN_CORE', 'False'))
internal_apps_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTERNAL_APPS', 'False'))
integration_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTEGRATION', 'False'))
integration_server_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTEGRATION_SERVER', 'False'))
integration_upload_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTEGRATION_UPLOAD', 'False'))
integration_monitoring_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTEGRATION_MONITORING', 'False'))
integration_csw_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTEGRATION_CSW', 'False'))
integration_bdd_tests = ast.literal_eval(os.environ.get('TEST_RUN_INTEGRATION_BDD', 'False'))
selenium_tests = ast.literal_eval(os.environ.get('TEST_RUN_SELENIUM', 'False'))

# Django 1.11 ParallelTestSuite
# TEST_RUNNER = 'geonode.tests.suite.runner.GeoNodeBaseSuiteDiscoverRunner'
TEST_RUNNER_KEEPDB = os.environ.get('TEST_RUNNER_KEEPDB', 0)
TEST_RUNNER_PARALLEL = os.environ.get('TEST_RUNNER_PARALLEL', 1)

# GeoNode test suite
# TEST_RUNNER = 'geonode.tests.suite.runner.DjangoParallelTestSuiteRunner'
# TEST_RUNNER_WORKER_MAX = 3
# TEST_RUNNER_WORKER_COUNT = 'auto'
# TEST_RUNNER_NOT_THREAD_SAFE = None
# TEST_RUNNER_PARENT_TIMEOUT = 10
# TEST_RUNNER_WORKER_TIMEOUT = 10

TEST = 'test' in sys.argv
INTEGRATION = 'geonode.tests.integration' in sys.argv

#
# Customizations to built in Django settings required by GeoNode
#

# Django automatically includes the "templates" dir in all the INSTALLED_APPS.
CONTEXT_PROCESSORS = [
    'django.template.context_processors.debug',
    'django.template.context_processors.i18n',
    'django.template.context_processors.tz',
    'django.template.context_processors.request',
    'django.template.context_processors.media',
    'django.template.context_processors.static',
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.contrib.auth.context_processors.auth',
    'geonode.context_processors.resource_urls',
    'geonode.themes.context_processors.custom_theme'
]
if 'geonode.geoserver' in INSTALLED_APPS:
    CONTEXT_PROCESSORS += ['geonode.geoserver.context_processors.geoserver_urls', ]

TEMPLATES = [
    {
        'NAME': 'GeoNode Project Templates',
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(PROJECT_ROOT, "templates")],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': CONTEXT_PROCESSORS,
            # Either remove APP_DIRS or remove the 'loaders' option.
            # 'loaders': [
            #      'django.template.loaders.filesystem.Loader',
            #      'django.template.loaders.app_directories.Loader',
            # ],
            'debug': DEBUG,
        },
    },
]

MIDDLEWARE = (
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.sites.middleware.CurrentSiteMiddleware',
    'dj_pagination.middleware.PaginationMiddleware',
    # The setting below makes it possible to serve different languages per
    # user depending on things like headers in HTTP requests.
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ref to: http://whitenoise.evans.io/en/stable/django.html#enable-whitenoise
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
    'geonode.base.middleware.MaintenanceMiddleware',
    'geonode.base.middleware.ReadOnlyMiddleware'  # a Middleware enabling Read Only mode of Geonode
)

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

# Security stuff
SESSION_EXPIRED_CONTROL_ENABLED = ast.literal_eval(os.environ.get('SESSION_EXPIRED_CONTROL_ENABLED', 'True'))

if SESSION_EXPIRED_CONTROL_ENABLED:
    # This middleware checks for ACCESS_TOKEN validity and if expired forces
    # user logout
    MIDDLEWARE += \
        ('geonode.security.middleware.SessionControlMiddleware',)

SESSION_COOKIE_SECURE = ast.literal_eval(os.environ.get('SESSION_COOKIE_SECURE', 'False'))
CSRF_COOKIE_SECURE = ast.literal_eval(os.environ.get('CSRF_COOKIE_SECURE', 'False'))
CSRF_COOKIE_HTTPONLY = ast.literal_eval(os.environ.get('CSRF_COOKIE_HTTPONLY', 'False'))
CORS_ALLOW_ALL_ORIGINS = ast.literal_eval(os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'False'))
X_FRAME_OPTIONS = os.environ.get('X_FRAME_OPTIONS', 'DENY')
SECURE_CONTENT_TYPE_NOSNIFF = ast.literal_eval(os.environ.get('SECURE_CONTENT_TYPE_NOSNIFF', 'True'))
SECURE_BROWSER_XSS_FILTER = ast.literal_eval(os.environ.get('SECURE_BROWSER_XSS_FILTER', 'True'))
SECURE_SSL_REDIRECT = ast.literal_eval(os.environ.get('SECURE_SSL_REDIRECT', 'False'))
SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '3600'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = ast.literal_eval(os.environ.get('SECURE_HSTS_INCLUDE_SUBDOMAINS', 'True'))

# Replacement of the default authentication backend in order to support
# permissions per object.
AUTHENTICATION_BACKENDS = (
    # 'oauth2_provider.backends.OAuth2Backend',
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

if 'announcements' in INSTALLED_APPS:
    AUTHENTICATION_BACKENDS += (
        'announcements.auth_backends.AnnouncementPermissionsBackend',
    )

OAUTH2_PROVIDER = {
    'SCOPES': {
        'openid': 'Default to OpenID',
        'read': 'Read scope',
        'write': 'Write scope',
        'groups': 'Access to your groups'
    },

    'CLIENT_ID_GENERATOR_CLASS': 'oauth2_provider.generators.ClientIdGenerator',
    'OAUTH2_SERVER_CLASS': 'geonode.security.oauth2_servers.OIDCServer',
    # 'OAUTH2_VALIDATOR_CLASS': 'geonode.security.oauth2_validators.OIDCValidator',

    # OpenID Connect
    "OIDC_ENABLED": True,
    "OIDC_ISS_ENDPOINT": SITEURL,
    "OIDC_USERINFO_ENDPOINT": f"{SITEURL}api/o/v4/tokeninfo/",
    "OIDC_RSA_PRIVATE_KEY": """-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQCIThjbTwpYu4Lwqp8oA7PqD6Ij/GwpLFJuPbWVaeCDaX6T7mh8
mJMIEgl/VIZasLH8SwU5mZ4sPeiqk7NgJq1XDo97q5mlFoNVHMCH38KQzSIBWtbq
WnEEnQdiqBbCmmIebLd4OcfpbIVUI89cnCq7U0M1ie0KOopWSHWOP6/35QIDAQAB
AoGBAIdwmtBotM5A3LaJxAY9z6uXhzSc4Vj0OqBiXymtgDL0Q5t4/Yg5D3ioe5lz
guFgzCr23KVEmOA7UBMXGtlC9V+iizVSbF4g2GqPLBKk+IYcAhfbSCg5rbbtQ5m2
PZxKZlJOQnjFLeh4sxitd84GfX16RfAhsvIiaN4d4CG+RAlhAkEA1Vitep0aHKmA
KRIGvZrgfH7uEZh2rRsCoo9lTxCT8ocCU964iEUxNH050yKdqYzVnNyFysY7wFgL
gsVzPROE6QJBAKOOWj9mN7uxhjRv2L4iYJ/rZaloVA49KBZEhvI+PgC5kAIrNVaS
n1kbJtFg54IS8HsYIP4YxONLqmDuhZL2rZ0CQQDId9wCo85eclMPxHV7AiXANdDj
zbxt6jxunYlXYr9yG7RvNI921HVo2eZU42j8YW5zR6+cGusYUGL4jSo8kLPJAkAG
SLPi97Rwe7OiVCHJvFxmCI9RYPbJzUO7B0sAB7AuKvMDglF8UAnbTJXDOavrbXrb
3+N0n9MAwKl9K+zp5pxpAkBSEUlYA0kDUqRgfuAXrrO/JYErGzE0UpaHxq5gCvTf
g+gp5fQ4nmDrSNHjakzQCX2mKMsx/GLWZzoIDd7ECV9f
-----END RSA PRIVATE KEY-----"""
}
OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2_provider.Application"
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = "oauth2_provider.AccessToken"
OAUTH2_PROVIDER_ID_TOKEN_MODEL = "oauth2_provider.IDToken"
OAUTH2_PROVIDER_GRANT_MODEL = "oauth2_provider.Grant"
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = "oauth2_provider.RefreshToken"

OAUTH2_DEFAULT_BACKEND_CLIENT_NAME = os.environ.get('OAUTH2_DEFAULT_BACKEND_CLIENT_NAME', 'GeoServer')

# In order to protect oauth2 REST endpoints, used by GeoServer to fetch user roles and
# infos, you should set this key and configure the "geonode REST role service"
# accordingly. Keep it secret!
# WARNING: If not set, the endpoint can be accessed by users without authorization.
OAUTH2_API_KEY = os.environ.get('OAUTH2_API_KEY', None)

# 1 day expiration time by default
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv('ACCESS_TOKEN_EXPIRE_SECONDS', '86400'))

# Require users to authenticate before using Geonode
LOCKDOWN_GEONODE = ast.literal_eval(os.getenv('LOCKDOWN_GEONODE', 'False'))

# Add additional paths (as regular expressions) that don't require
# authentication.
# - authorized exempt urls needed for oauth when GeoNode is set to lockdown
AUTH_EXEMPT_URLS = (
    f'{FORCE_SCRIPT_NAME}/o/*',
    f'{FORCE_SCRIPT_NAME}/gs/*',
    f'{FORCE_SCRIPT_NAME}/account/*',
    f'{FORCE_SCRIPT_NAME}/static/*',
    f'{FORCE_SCRIPT_NAME}/api/o/*',
    f'{FORCE_SCRIPT_NAME}/api/roles',
    f'{FORCE_SCRIPT_NAME}/api/adminRole',
    f'{FORCE_SCRIPT_NAME}/api/users',
    f'{FORCE_SCRIPT_NAME}/api/datasets',
    f'{FORCE_SCRIPT_NAME}/monitoring',
    r'^/i18n/setlang/?$',
)

ANONYMOUS_USER_ID = os.getenv('ANONYMOUS_USER_ID', '-1')
GUARDIAN_GET_INIT_ANONYMOUS_USER = os.getenv(
    'GUARDIAN_GET_INIT_ANONYMOUS_USER',
    'geonode.people.models.get_anonymous_user_instance'
)

# Whether the uplaoded resources should be public and downloadable by default
# or not
DEFAULT_ANONYMOUS_VIEW_PERMISSION = ast.literal_eval(
    os.getenv('DEFAULT_ANONYMOUS_VIEW_PERMISSION', 'True')
)
DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION = ast.literal_eval(
    os.getenv('DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION', 'True')
)

#
# Settings for default search size
#
DEFAULT_SEARCH_SIZE = int(os.getenv('DEFAULT_SEARCH_SIZE', '10'))


#
# Settings for third party apps
#

# Pinax Ratings
PINAX_RATINGS_CATEGORY_CHOICES = {
    "maps.Map": {
        "map": "How good is this map?"
    },
    "layers.Dataset": {
        "dataset": "How good is this dataset?"
    },
    "documents.Document": {
        "document": "How good is this document?"
    },
    "geoapps.GeoApp": {
        "geoapp": "How good is this geoapp?"
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
# GeoNode specific settings
#
# per-deployment settings should go here

# Login and logout urls override
LOGIN_URL = os.getenv('LOGIN_URL', f'{SITEURL}account/login/')
LOGOUT_URL = os.getenv('LOGOUT_URL', f'{SITEURL}account/logout/')

ACCOUNT_LOGIN_REDIRECT_URL = os.getenv('LOGIN_REDIRECT_URL', SITEURL)
ACCOUNT_LOGOUT_REDIRECT_URL = os.getenv('LOGOUT_REDIRECT_URL', SITEURL)

# Backend
DEFAULT_WORKSPACE = os.getenv('DEFAULT_WORKSPACE', 'geonode')
CASCADE_WORKSPACE = os.getenv('CASCADE_WORKSPACE', 'geonode')

OGP_URL = os.getenv('OGP_URL', "http://geodata.tufts.edu/solr/select")

# Topic Categories list should not be modified (they are ISO). In case you
# absolutely need it set to True this variable
MODIFY_TOPICCATEGORY = ast.literal_eval(os.getenv('MODIFY_TOPICCATEGORY', 'True'))

# If this option is enabled, Topic Categories will become strictly Mandatory on
# Metadata Wizard
TOPICCATEGORY_MANDATORY = ast.literal_eval(os.environ.get('TOPICCATEGORY_MANDATORY', 'False'))

MISSING_THUMBNAIL = os.getenv(
    'MISSING_THUMBNAIL', 'geonode/img/missing_thumb.png'
)

GEOSERVER_LOCATION = os.getenv(
    'GEOSERVER_LOCATION', 'http://localhost:8080/geoserver/'
)

# add trailing slash to geoserver location url.
if not GEOSERVER_LOCATION.endswith('/'):
    GEOSERVER_LOCATION = f'{GEOSERVER_LOCATION}/'

GEOSERVER_PUBLIC_SCHEMA = os.getenv(
    'GEOSERVER_PUBLIC_SCHEMA', SITE_HOST_SCHEMA
)

GEOSERVER_PUBLIC_HOST = os.getenv(
    'GEOSERVER_PUBLIC_HOST', SITE_HOST_NAME
)

GEOSERVER_PUBLIC_PORT = os.getenv(
    'GEOSERVER_PUBLIC_PORT', 8080
)

if GEOSERVER_PUBLIC_PORT:
    _default_public_location = f'{GEOSERVER_PUBLIC_SCHEMA}://{GEOSERVER_PUBLIC_HOST}:{GEOSERVER_PUBLIC_PORT}/geoserver/'
else:
    _default_public_location = f'{GEOSERVER_PUBLIC_SCHEMA}://{GEOSERVER_PUBLIC_HOST}/geoserver/'

GEOSERVER_PUBLIC_LOCATION = os.getenv(
    'GEOSERVER_PUBLIC_LOCATION', _default_public_location
)

GEOSERVER_WEB_UI_LOCATION = os.getenv(
    'GEOSERVER_WEB_UI_LOCATION', GEOSERVER_PUBLIC_LOCATION
)

OGC_SERVER_DEFAULT_USER = os.getenv(
    'GEOSERVER_ADMIN_USER', 'admin'
)

OGC_SERVER_DEFAULT_PASSWORD = os.getenv(
    'GEOSERVER_ADMIN_PASSWORD', 'geoserver'
)

GEOFENCE_SECURITY_ENABLED = False if TEST and not INTEGRATION \
    else ast.literal_eval(os.getenv('GEOFENCE_SECURITY_ENABLED', 'True'))

# OGC (WMS/WFS/WCS) Server Settings
# OGC (WMS/WFS/WCS) Server Settings
OGC_SERVER = {
    'default': {
        'BACKEND': os.getenv('BACKEND', 'geonode.geoserver'),
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
        'MAPFISH_PRINT_ENABLED': ast.literal_eval(os.getenv('MAPFISH_PRINT_ENABLED', 'True')),
        'PRINT_NG_ENABLED': ast.literal_eval(os.getenv('PRINT_NG_ENABLED', 'True')),
        'GEONODE_SECURITY_ENABLED': ast.literal_eval(os.getenv('GEONODE_SECURITY_ENABLED', 'True')),
        'GEOFENCE_SECURITY_ENABLED': GEOFENCE_SECURITY_ENABLED,
        'GEOFENCE_URL': os.getenv('GEOFENCE_URL', 'internal:/'),
        'WMST_ENABLED': ast.literal_eval(os.getenv('WMST_ENABLED', 'False')),
        'BACKEND_WRITE_ENABLED': ast.literal_eval(os.getenv('BACKEND_WRITE_ENABLED', 'True')),
        'WPS_ENABLED': ast.literal_eval(os.getenv('WPS_ENABLED', 'False')),
        'LOG_FILE': f'{os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))}/geoserver/data/logs/geoserver.log',
        # Set to name of database in DATABASES dictionary to enable
        # 'datastore',
        'DATASTORE': os.getenv('DEFAULT_BACKEND_DATASTORE', ''),
        'TIMEOUT': int(os.getenv('OGC_REQUEST_TIMEOUT', '60')),
        'MAX_RETRIES': int(os.getenv('OGC_REQUEST_MAX_RETRIES', '3')),
        'BACKOFF_FACTOR': float(os.getenv('OGC_REQUEST_BACKOFF_FACTOR', '0.3')),
        'POOL_MAXSIZE': int(os.getenv('OGC_REQUEST_POOL_MAXSIZE', '10')),
        'POOL_CONNECTIONS': int(os.getenv('OGC_REQUEST_POOL_CONNECTIONS', '10')),
    }
}

USE_GEOSERVER = 'geonode.geoserver' in INSTALLED_APPS and OGC_SERVER['default']['BACKEND'] == 'geonode.geoserver'

# Uploader Settings
DATA_UPLOAD_MAX_NUMBER_FIELDS = 100000
"""
    DEFAULT_BACKEND_UPLOADER = {'geonode.importer'}
"""
UPLOADER = {
    'BACKEND': os.getenv('DEFAULT_BACKEND_UPLOADER', 'geonode.importer'),
    'OPTIONS': {
        'TIME_ENABLED': ast.literal_eval(os.getenv('TIME_ENABLED', 'False')),
        'MOSAIC_ENABLED': ast.literal_eval(os.getenv('MOSAIC_ENABLED', 'False')),
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

EPSG_CODE_MATCHES = {
    'EPSG:4326': '(4326) WGS 84',
    'EPSG:900913': '(900913) Google Maps Global Mercator',
    'EPSG:3857': '(3857) WGS 84 / Pseudo-Mercator',
    'EPSG:3785': '(3785 DEPRECATED) Popular Visualisation CRS / Mercator',
    'EPSG:32647': '(32647) WGS 84 / UTM zone 47N',
    'EPSG:32736': '(32736) WGS 84 / UTM zone 36S'
}

# CSW settings
CATALOGUE = {
    'default': {
        # The underlying CSW implementation
        # default is pycsw in local mode (tied directly to GeoNode Django DB)
        'ENGINE': os.getenv('CATALOGUE_ENGINE', 'geonode.catalogue.backends.pycsw_local'),
        # pycsw in non-local mode
        # 'ENGINE': 'geonode.catalogue.backends.pycsw_http',
        # deegree and others
        # 'ENGINE': 'geonode.catalogue.backends.generic',
        # The FULLY QUALIFIED base url to the CSW instance for this GeoNode
        'URL': os.getenv('CATALOGUE_URL', urljoin(SITEURL, '/catalogue/csw')),
        # 'URL': 'http://localhost:8080/geonetwork/srv/en/csw',
        # 'URL': 'http://localhost:8080/deegree-csw-demo-3.0.4/services',
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

_DATETIME_INPUT_FORMATS = ['%Y-%m-%d %H:%M:%S.%f %Z', '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%dT%H:%M:%S%Z']
DATETIME_INPUT_FORMATS = DATETIME_INPUT_FORMATS + _DATETIME_INPUT_FORMATS

DISPLAY_SOCIAL = ast.literal_eval(os.getenv('DISPLAY_SOCIAL', 'True'))
DISPLAY_RATINGS = ast.literal_eval(os.getenv('DISPLAY_RATINGS', 'True'))
DISPLAY_WMS_LINKS = ast.literal_eval(os.getenv('DISPLAY_WMS_LINKS', 'True'))

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
TWITTER_CARD = ast.literal_eval(os.getenv('TWITTER_CARD', 'True'))
TWITTER_SITE = '@GeoNode'
TWITTER_HASHTAGS = ['geonode']

OPENGRAPH_ENABLED = ast.literal_eval(os.getenv('OPENGRAPH_ENABLED', 'True'))

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

try:
    # try to parse python notation, default in dockerized env
    ALLOWED_HOSTS = ast.literal_eval(os.getenv('ALLOWED_HOSTS'))
except ValueError:
    # fallback to regular list of values separated with misc chars
    ALLOWED_HOSTS = [HOSTNAME, 'localhost', 'django', 'geonode'] if os.getenv('ALLOWED_HOSTS') is None \
        else re.split(r' *[,|:;] *', os.getenv('ALLOWED_HOSTS'))

# AUTH_IP_WHITELIST property limits access to users/groups REST endpoints
# to only whitelisted IP addresses.
#
# Empty list means 'allow all'
#
# If you need to limit 'api' REST calls to only some specific IPs
# fill the list like below:
#
# AUTH_IP_WHITELIST = ['192.168.1.158', '192.168.1.159']
AUTH_IP_WHITELIST = [HOSTNAME, 'localhost', 'django', 'geonode'] if os.getenv('AUTH_IP_WHITELIST') is None \
    else re.split(r' *[,|:;] *', os.getenv('AUTH_IP_WHITELIST'))


# ADMIN_IP_WHITELIST property limits access as admin
# to only whitelisted IP addresses.
#
# Empty list means 'allow all'
#
# If you need to limit admin access to some specific IPs
# fill the list like below:
#
# ADMIN_IP_WHITELIST = ['192.168.1.158', '192.168.1.159']
ADMIN_IP_WHITELIST = [] if os.getenv('ADMIN_IP_WHITELIST') is None \
    else re.split(r' *[,|:;] *', os.getenv('ADMIN_IP_WHITELIST'))
if len(ADMIN_IP_WHITELIST) > 0:
    AUTHENTICATION_BACKENDS = ('geonode.security.backends.AdminRestrictedAccessBackend',) + AUTHENTICATION_BACKENDS
    MIDDLEWARE += ('geonode.security.middleware.AdminAllowedMiddleware',)

# A tuple of hosts the proxy can send requests to.
try:
    # try to parse python notation, default in dockerized env
    PROXY_ALLOWED_HOSTS = ast.literal_eval(os.getenv('PROXY_ALLOWED_HOSTS'))
except ValueError:
    # fallback to regular list of values separated with misc chars
    PROXY_ALLOWED_HOSTS = [
        HOSTNAME, 'localhost', 'django', 'geonode',
        'spatialreference.org', 'nominatim.openstreetmap.org', 'dev.openlayers.org'] \
        if os.getenv('PROXY_ALLOWED_HOSTS') is None \
        else re.split(r' *[,|:;] *', os.getenv('PROXY_ALLOWED_HOSTS'))

# The proxy to use when making cross origin requests.
PROXY_URL = os.environ.get('PROXY_URL', '/proxy/?url=')

# Haystack Search Backend Configuration. To enable,
# first install the following:
# - pip install django-haystack
# - pip install pyelasticsearch
# Set HAYSTACK_SEARCH to True
# Run "python manage.py rebuild_index"
HAYSTACK_SEARCH = ast.literal_eval(os.getenv('HAYSTACK_SEARCH', 'False'))
# Avoid permissions prefiltering
SKIP_PERMS_FILTER = ast.literal_eval(os.getenv('SKIP_PERMS_FILTER', 'False'))
# Update facet counts from Haystack
HAYSTACK_FACET_COUNTS = ast.literal_eval(os.getenv('HAYSTACK_FACET_COUNTS', 'True'))
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
    'Zipped All Files'
]


DISPLAY_ORIGINAL_DATASET_LINK = ast.literal_eval(
    os.getenv('DISPLAY_ORIGINAL_DATASET_LINK', 'True'))

ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE = ast.literal_eval(
    os.getenv('ACCOUNT_NOTIFY_ON_PASSWORD_CHANGE', 'False'))

TASTYPIE_DEFAULT_FORMATS = ['json']

# gravatar settings
AUTO_GENERATE_AVATAR_SIZES = (
    20, 30, 32, 40, 50, 65, 70, 80, 100, 140, 200, 240
)
AVATAR_GRAVATAR_SSL = ast.literal_eval(os.getenv('AVATAR_GRAVATAR_SSL', 'False'))

AVATAR_DEFAULT_URL = os.getenv('AVATAR_DEFAULT_URL', '/geonode/img/avatar.png')

try:
    # try to parse python notation, default in dockerized env
    AVATAR_PROVIDERS = ast.literal_eval(os.getenv('AVATAR_PROVIDERS'))
except ValueError:
    # fallback to regular list of values separated with misc chars
    AVATAR_PROVIDERS = (
        'avatar.providers.PrimaryAvatarProvider',
        'avatar.providers.GravatarAvatarProvider',
        'avatar.providers.DefaultAvatarProvider'
    ) if os.getenv('AVATAR_PROVIDERS') is None \
        else re.split(r' *[,|:;] *', os.getenv('AVATAR_PROVIDERS'))

# Number of results per page listed in the GeoNode search pages
CLIENT_RESULTS_LIMIT = int(os.getenv('CLIENT_RESULTS_LIMIT', '5'))

# LOCKDOWN API endpoints to prevent unauthenticated access.
# If set to True, search won't deliver results and filtering ResourceBase-objects is not possible for anonymous users
API_LOCKDOWN = ast.literal_eval(
    os.getenv('API_LOCKDOWN', 'False'))

# Number of items returned by the apis 0 equals no limit
API_LIMIT_PER_PAGE = int(os.getenv('API_LIMIT_PER_PAGE', '200'))
API_INCLUDE_REGIONS_COUNT = ast.literal_eval(
    os.getenv('API_INCLUDE_REGIONS_COUNT', 'False'))

# Settings for EXIF plugin
EXIF_ENABLED = ast.literal_eval(os.getenv('EXIF_ENABLED', 'True'))

if EXIF_ENABLED:
    if 'geonode.documents.exif' not in INSTALLED_APPS:
        INSTALLED_APPS += ('geonode.documents.exif',)

# Settings for CREATE_LAYER plugin
CREATE_LAYER = ast.literal_eval(os.getenv('CREATE_LAYER', 'False'))

if CREATE_LAYER:
    if 'geonode.geoserver.createlayer' not in INSTALLED_APPS:
        INSTALLED_APPS += ('geonode.geoserver.createlayer',)

# Settings for RECAPTCHA plugin
RECAPTCHA_ENABLED = ast.literal_eval(os.environ.get('RECAPTCHA_ENABLED', 'False'))

if RECAPTCHA_ENABLED:
    if 'captcha' not in INSTALLED_APPS:
        INSTALLED_APPS += ('captcha',)
    ACCOUNT_SIGNUP_FORM_CLASS = os.getenv("ACCOUNT_SIGNUP_FORM_CLASS",
                                          'geonode.people.forms.AllauthReCaptchaSignupForm')
    """
     In order to generate reCaptcha keys, please see:
      - https://pypi.org/project/django-recaptcha/#installation
      - https://pypi.org/project/django-recaptcha/#local-development-and-functional-testing
    """
    RECAPTCHA_PUBLIC_KEY = os.getenv("RECAPTCHA_PUBLIC_KEY", 'geonode_RECAPTCHA_PUBLIC_KEY')
    RECAPTCHA_PRIVATE_KEY = os.getenv("RECAPTCHA_PRIVATE_KEY", 'geonode_RECAPTCHA_PRIVATE_KEY')

GEONODE_CATALOGUE_METADATA_XSL = ast.literal_eval(os.getenv('GEONODE_CATALOGUE_METADATA_XSL', 'True'))

# -- START Client Hooksets Setup

# GeoNode javascript client configuration

# default map projection
# Note: If set to EPSG:4326, then only EPSG:4326 basemaps will work.
DEFAULT_MAP_CRS = os.environ.get('DEFAULT_MAP_CRS', "EPSG:3857")

DEFAULT_LAYER_FORMAT = os.environ.get('DEFAULT_LAYER_FORMAT', "image/png")
DEFAULT_TILE_SIZE = os.environ.get('DEFAULT_TILE_SIZE', 512)

# Where should newly created maps be focused?
DEFAULT_MAP_CENTER = (
    ast.literal_eval(os.environ.get('DEFAULT_MAP_CENTER_X', '0')),
    ast.literal_eval(os.environ.get('DEFAULT_MAP_CENTER_Y', '0')))

# How tightly zoomed should newly created maps be?
# 0 = entire world;
# maximum zoom is between 12 and 15 (for Google Maps, coverage varies by area)
DEFAULT_MAP_ZOOM = int(os.environ.get('DEFAULT_MAP_ZOOM', 0))

MAPBOX_ACCESS_TOKEN = os.environ.get('MAPBOX_ACCESS_TOKEN', None)
BING_API_KEY = os.environ.get('BING_API_KEY', None)
GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY', None)

GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY = os.getenv('GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY', 'mapstore')

MAP_BASELAYERS = [{}]

"""
MapStore2 REACT based Client parameters
"""
if GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY == 'mapstore':
    GEONODE_CLIENT_HOOKSET = os.getenv('GEONODE_CLIENT_HOOKSET', 'geonode_mapstore_client.hooksets.MapStoreHookSet')

    if 'geonode_mapstore_client' not in INSTALLED_APPS:
        INSTALLED_APPS += (
            'geonode_mapstore_client',)

    def get_geonode_catalogue_service():
        if PYCSW:
            pycsw_config = PYCSW["CONFIGURATION"]
            if pycsw_config:
                pycsw_catalogue = {
                    f"{pycsw_config['metadata:main']['identification_title']}": {
                        "url": CATALOGUE['default']['URL'],
                        "type": "csw",
                        "title": pycsw_config['metadata:main']['identification_title'],
                        "autoload": True,
                        "layerOptions": {
                            "tileSize": DEFAULT_TILE_SIZE
                        }
                    }
                }
                return pycsw_catalogue
        return None

    GEONODE_CATALOGUE_SERVICE = get_geonode_catalogue_service()

    MAPSTORE_CATALOGUE_SERVICES = {}

    MAPSTORE_CATALOGUE_SELECTED_SERVICE = ""

    if GEONODE_CATALOGUE_SERVICE:
        MAPSTORE_CATALOGUE_SERVICES[list(list(GEONODE_CATALOGUE_SERVICE.keys()))[0]] = GEONODE_CATALOGUE_SERVICE[list(list(GEONODE_CATALOGUE_SERVICE.keys()))[0]]  # noqa
        MAPSTORE_CATALOGUE_SELECTED_SERVICE = list(list(GEONODE_CATALOGUE_SERVICE.keys()))[0]

    DEFAULT_MS2_BACKGROUNDS = [
        {
            "type": "osm",
            "title": "Open Street Map",
            "name": "mapnik",
            "source": "osm",
            "group": "background",
            "visibility": True
        }, {
            "type": "tileprovider",
            "title": "OpenTopoMap",
            "provider": "OpenTopoMap",
            "name": "OpenTopoMap",
            "source": "OpenTopoMap",
            "group": "background",
            "visibility": False
        }, {
            "type": "wms",
            "title": "Sentinel-2 cloudless - https://s2maps.eu",
            "format": "image/jpeg",
            "id": "s2cloudless",
            "name": "s2cloudless:s2cloudless",
            "url": "https://maps.geo-solutions.it/geoserver/wms",
            "group": "background",
            "thumbURL": f"{SITEURL}static/mapstorestyle/img/s2cloudless-s2cloudless.png",
            "visibility": False
        }, {
            "source": "ol",
            "group": "background",
            "id": "none",
            "name": "empty",
            "title": "Empty Background",
            "type": "empty",
            "visibility": False,
            "args": ["Empty Background", {"visibility": False}]
        }
    ]

    if MAPBOX_ACCESS_TOKEN:
        BASEMAP = {
            "type": "tileprovider",
            "title": "MapBox streets-v11",
            "provider": "MapBoxStyle",
            "name": "MapBox streets-v11",
            "accessToken": f"{MAPBOX_ACCESS_TOKEN}",
            "source": "streets-v11",
            "thumbURL": f"https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/256/6/33/23?access_token={MAPBOX_ACCESS_TOKEN}",  # noqa
            "group": "background",
            "visibility": True
        }
        DEFAULT_MS2_BACKGROUNDS = [BASEMAP, ] + DEFAULT_MS2_BACKGROUNDS

    if BING_API_KEY:
        BASEMAP = {
            "type": "bing",
            "title": "Bing Aerial",
            "name": "AerialWithLabels",
            "source": "bing",
            "group": "background",
            "apiKey": "{{apiKey}}",
            "visibility": False
        }
        DEFAULT_MS2_BACKGROUNDS = [BASEMAP, ] + DEFAULT_MS2_BACKGROUNDS

    MAPSTORE_BASELAYERS = DEFAULT_MS2_BACKGROUNDS
    # MAPSTORE_BASELAYERS_SOURCES allow to configure tilematrix sets for wmts layers
    MAPSTORE_BASELAYERS_SOURCES = os.environ.get('MAPSTORE_BASELAYERS_SOURCES', {})

    MAPSTORE_DEFAULT_LANGUAGES = """(
        ('de-de', 'Deutsch'),
        ('en-us', 'English'),
        ('es-es', 'Español'),
        ('fr-fr', 'Français'),
        ('it-it', 'Italiano'),
    )"""

    LANGUAGES = ast.literal_eval(os.getenv('LANGUAGES', MAPSTORE_DEFAULT_LANGUAGES))
    # The default mapstore client compiles the translations json files in the /static/mapstore directory
    # gn-translations are the custom translations for the client and ms-translations are the translations from the core framework
    MAPSTORE_TRANSLATIONS_PATH = os.environ.get('MAPSTORE_TRANSLATIONS_PATH', ['/static/mapstore/ms-translations', '/static/mapstore/gn-translations'])

    # list of projections available in the mapstore client
    # properties:
    # - code: epsg code of the projection
    # - def: definition of projection in Proj4js string
    # - extent: max extent in projected coordinates [minx, miny, maxx, maxy]
    # - worldExtent: max extent in WGS84 coordinates [minx, miny, maxx, maxy]
    # example:
    # MAPSTORE_PROJECTION_DEFS = [
    #   {
    #        "code": "EPSG:3395",
    #        "def": "+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs",
    #        "extent": [-20026376.39, -15496570.74, 20026376.39, 18764656.23 ],
    #        "worldExtent": [ -180.0, -80.0, 180.0, 84.0 ]
    #    }
    # ]
    MAPSTORE_PROJECTION_DEFS = []

    # list of rules to change the plugins configuration
    # allowed operation: add, remove and replace
    # example: remove Measure plugin from map_viewer page
    # MAPSTORE_PLUGINS_CONFIG_PATCH_RULES = [
    #     {
    #         "op": "remove",
    #         "jsonpath": "$.map_viewer..[?(@.name == 'Measure')]"
    #     }
    # ]
    # example: add SearchServicesConfig plugin to map_viewer page
    # MAPSTORE_PLUGINS_CONFIG_PATCH_RULES = [
    #     {
    #         "op": "add",
    #         "jsonpath": "/map_viewer/-",
    #         "value": {
    #             "name": "SearchServicesConfig"
    #         }
    #     }
    # ]
    # example: replace default configuration of Print plugin in map_viewer page
    # MAPSTORE_PLUGINS_CONFIG_PATCH_RULES = [
    #     {
    #         "op": "replace",
    #         "jsonpath": "$.map_viewer..[?(@.name == 'Print')].cfg",
    #         "value": {
    #             "useFixedScales": False
    #         }
    #     }
    # ]
    MAPSTORE_PLUGINS_CONFIG_PATCH_RULES = []

    # Extensions path to use in importing custom extensions into geonode
    MAPSTORE_EXTENSIONS_FOLDER_PATH = '/static/mapstore/extensions/'

    # Supported Dataset file types for uploading Datasets. This setting is being from from the client

# -- END Client Hooksets Setup

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
    'GROUPS_ENABLED': True,
    'GROUP_CATEGORIES_ENABLED': True,
}

# HTML WYSIWYG Editor (TINYMCE) Menu Bar Settings
TINYMCE_DEFAULT_CONFIG = {
    "theme": "silver",
    "height": 200,
    "plugins": 'preview paste searchreplace autolink directionality code visualblocks visualchars fullscreen image link media template codesample table charmap hr pagebreak nonbreaking insertdatetime advlist lists wordcount imagetools textpattern noneditable help charmap quickbars',  # noqa
    "imagetools_cors_hosts": ['picsum.photos'],
    "menubar": False,
    "statusbar": False,
    "toolbar": 'bold italic underline | formatselect removeformat | outdent indent |  numlist bullist | insertfile image media link codesample | preview',  # noqa
    "toolbar_sticky": "true",
    "autosave_ask_before_unload": "true",
    "autosave_interval": "30s",
    "autosave_prefix": "{path}{query}-{id}-",
    "autosave_restore_when_empty": "false",
    "autosave_retention": "2m",
    "image_advtab": "true",
    "content_css": '//www.tiny.cloud/css/codepen.min.css',
    "importcss_append": "true",
    "image_caption": "true",
    "quickbars_selection_toolbar": 'bold italic | quicklink h2 h3 blockquote quickimage quicktable',
    "noneditable_noneditable_class": "mceNonEditable",
    "toolbar_mode": 'sliding',
    "contextmenu": "link image imagetools table",
    "templates": [
        {
            "title": 'New Table',
            "description": 'creates a new table',
            "content": '<div class="mceTmpl"><table width="98%%"  border="0" cellspacing="0" cellpadding="0"><tr><th scope="col"> </th><th scope="col"> </th></tr><tr><td> </td><td> </td></tr></table></div>'  # noqa
        },
        {
            "title": 'Starting my story',
            "description": 'A cure for writers block',
            "content": 'Once upon a time...'
        },
        {
            "title": 'New list with dates',
            "description": 'New List with dates',
            "content": '<div class="mceTmpl"><span class="cdate">cdate</span><br /><span class="mdate">mdate</span><h2>My List</h2><ul><li></li><li></li></ul></div>'  # noqa
        }
    ],
    "template_cdate_format": '[Date Created (CDATE): %m/%d/%Y : %H:%M:%S]',
    "template_mdate_format": '[Date Modified (MDATE): %m/%d/%Y : %H:%M:%S]',
    "setup": 'function(editor) {editor.on("input", onInputChange)}'
}

# Make Free-Text Kaywords writable from users or read-only
# - if True only admins can edit free-text kwds from admin dashboard
FREETEXT_KEYWORDS_READONLY = ast.literal_eval(os.environ.get('FREETEXT_KEYWORDS_READONLY', 'False'))

# ########################################################################### #
# ASYNC SETTINGS
# ########################################################################### #
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

CELERY_LOADER = os.environ.get('CELERY_LOADER', 'geonode.loaders.GeoNodeCeleryTaksLoader')

ASYNC_SIGNALS = ast.literal_eval(os.environ.get('ASYNC_SIGNALS', 'False'))
RABBITMQ_SIGNALS_BROKER_URL = 'amqp://localhost:5672'
# REDIS_SIGNALS_BROKER_URL = 'redis://localhost:6379/0'
LOCAL_SIGNALS_BROKER_URL = 'memory://'

if ASYNC_SIGNALS:
    _BROKER_URL = RABBITMQ_SIGNALS_BROKER_URL
else:
    _BROKER_URL = LOCAL_SIGNALS_BROKER_URL
CELERY_RESULT_BACKEND = 'django-db'

CELERY_BROKER_URL = os.environ.get('BROKER_URL', _BROKER_URL)
CELERY_RESULT_PERSISTENT = ast.literal_eval(os.environ.get('CELERY_RESULT_PERSISTENT', 'False'))
CELERY_IGNORE_RESULT = ast.literal_eval(os.environ.get('CELERY_IGNORE_RESULT', 'False'))

# Allow to recover from any unknown crash.
CELERY_ACKS_LATE = ast.literal_eval(os.environ.get('CELERY_ACKS_LATE', 'True'))

# Add a ten-minutes timeout to all Celery tasks.
CELERYD_SOFT_TIME_LIMIT = 600

# Set this to False in order to run async
_EAGER_FLAG = 'False' if ASYNC_SIGNALS else 'True'
CELERY_TASK_ALWAYS_EAGER = ast.literal_eval(os.environ.get('CELERY_TASK_ALWAYS_EAGER', _EAGER_FLAG))
CELERY_TASK_EAGER_PROPAGATES = ast.literal_eval(os.environ.get('CELERY_TASK_EAGER_PROPAGATES', 'True'))
CELERY_TASK_IGNORE_RESULT = ast.literal_eval(os.environ.get('CELERY_TASK_IGNORE_RESULT', 'True'))

register('geonode_json', serializer.dumps, serializer.loads, content_type='application/json', content_encoding='utf-8')

# I use these to debug kombu crashes; we get a more informative message.
CELERY_TASK_SERIALIZER = os.environ.get('CELERY_TASK_SERIALIZER', 'geonode_json')
CELERY_RESULT_SERIALIZER = os.environ.get('CELERY_RESULT_SERIALIZER', 'geonode_json')
CELERY_ACCEPT_CONTENT = [CELERY_RESULT_SERIALIZER, ]

# Set Tasks Queues
# CELERY_TASK_DEFAULT_QUEUE = "default"
# CELERY_TASK_DEFAULT_EXCHANGE = "default"
# CELERY_TASK_DEFAULT_EXCHANGE_TYPE = "direct"
# CELERY_TASK_DEFAULT_ROUTING_KEY = "default"
CELERY_TASK_CREATE_MISSING_QUEUES = ast.literal_eval(os.environ.get('CELERY_TASK_CREATE_MISSING_QUEUES', 'True'))
GEONODE_EXCHANGE = Exchange("default", type="topic", durable=True)
CELERY_TASK_QUEUES = (
    Queue('default', GEONODE_EXCHANGE, routing_key='default', priority=0),
    Queue('geonode', GEONODE_EXCHANGE, routing_key='geonode', priority=0),
    Queue('update', GEONODE_EXCHANGE, routing_key='update', priority=0),
    Queue('upload', GEONODE_EXCHANGE, routing_key='upload', priority=0),
    Queue('cleanup', GEONODE_EXCHANGE, routing_key='cleanup', priority=0),
    Queue('email', GEONODE_EXCHANGE, routing_key='email', priority=0),
    Queue('security', GEONODE_EXCHANGE, routing_key='security', priority=0),
    Queue('management_commands_http', GEONODE_EXCHANGE, routing_key='management_commands_http', priority=0),
)

if USE_GEOSERVER:
    GEOSERVER_EXCHANGE = Exchange("geonode", type="topic", durable=True)
    CELERY_TASK_QUEUES += (
        Queue("broadcast", GEOSERVER_EXCHANGE, routing_key="#"),
        Queue("email.events", GEOSERVER_EXCHANGE, routing_key="geoserver.email"),
        Queue("all.geoserver", GEOSERVER_EXCHANGE, routing_key="geoserver.#"),
        Queue("geoserver.catalog", GEOSERVER_EXCHANGE, routing_key="geoserver.catalog"),
        Queue("geoserver.data", GEOSERVER_EXCHANGE, routing_key="geoserver.data"),
        Queue("geoserver.events", GEOSERVER_EXCHANGE, routing_key="geonode.geoserver"),
        Queue("notifications.events", GEOSERVER_EXCHANGE, routing_key="notifications"),
        Queue("geonode.layer.viewer", GEOSERVER_EXCHANGE, routing_key="geonode.viewer"),
    )

# from celery.schedules import crontab
# EXAMPLES
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

CELERY_BEAT_SCHEDULER = os.environ.get(
    'CELERY_BEAT_SCHEDULER', "celery.beat:PersistentScheduler")
CELERY_BEAT_SCHEDULE = {}

DELAYED_SECURITY_SIGNALS = ast.literal_eval(os.environ.get('DELAYED_SECURITY_SIGNALS', 'False'))
CELERY_ENABLE_UTC = ast.literal_eval(os.environ.get('CELERY_ENABLE_UTC', 'True'))
CELERY_TIMEZONE = TIME_ZONE

# Half a day is enough
CELERY_TASK_RESULT_EXPIRES = os.environ.get('CELERY_TASK_RESULT_EXPIRES', 43200)

# Sometimes, Ask asks us to enable this to debug issues.
# BTW, it will save some CPU cycles.
CELERY_DISABLE_RATE_LIMITS = ast.literal_eval(os.environ.get('CELERY_DISABLE_RATE_LIMITS', 'False'))
CELERY_SEND_TASK_EVENTS = ast.literal_eval(os.environ.get('CELERY_SEND_TASK_EVENTS', 'True'))
CELERY_WORKER_DISABLE_RATE_LIMITS = ast.literal_eval(os.environ.get('CELERY_WORKER_DISABLE_RATE_LIMITS', 'False'))
CELERY_WORKER_SEND_TASK_EVENTS = ast.literal_eval(os.environ.get('CELERY_WORKER_SEND_TASK_EVENTS', 'True'))

# Allow our remote workers to get tasks faster if they have a
# slow internet connection (yes Gurney, I'm thinking of you).
CELERY_MESSAGE_COMPRESSION = os.environ.get('CELERY_MESSAGE_COMPRESSION', 'gzip')

# The default beiing 5000, we need more than this.
CELERY_MAX_CACHED_RESULTS = os.environ.get('CELERY_MAX_CACHED_RESULTS', 32768)

# NOTE: I don't know if this is compatible with upstart.
CELERYD_POOL_RESTARTS = ast.literal_eval(os.environ.get('CELERYD_POOL_RESTARTS', 'True'))
CELERY_TRACK_STARTED = ast.literal_eval(os.environ.get('CELERY_TRACK_STARTED', 'True'))
CELERY_SEND_TASK_SENT_EVENT = ast.literal_eval(os.environ.get('CELERY_SEND_TASK_SENT_EVENT', 'True'))

# Disabled by default and I like it, because we use Sentry for this.
CELERY_SEND_TASK_ERROR_EMAILS = ast.literal_eval(os.environ.get('CELERY_SEND_TASK_ERROR_EMAILS', 'False'))

# ########################################################################### #
# NOTIFICATIONS SETTINGS
# ########################################################################### #
NOTIFICATION_ENABLED = ast.literal_eval(os.environ.get('NOTIFICATION_ENABLED', 'True')) or TEST
# PINAX_NOTIFICATIONS_LANGUAGE_MODEL = "people.Profile"

# notifications backends
NOTIFICATIONS_BACKEND = os.environ.get('NOTIFICATIONS_BACKEND', 'geonode.notifications_backend.EmailBackend')
PINAX_NOTIFICATIONS_BACKENDS = [
    ("email", NOTIFICATIONS_BACKEND, 0),
]
PINAX_NOTIFICATIONS_HOOKSET = "pinax.notifications.hooks.DefaultHookSet"

# Queue non-blocking notifications.
# Set this to False in order to run async
_QUEUE_ALL_FLAG = 'True' if ASYNC_SIGNALS else 'False'
PINAX_NOTIFICATIONS_QUEUE_ALL = ast.literal_eval(os.environ.get('NOTIFICATIONS_QUEUE_ALL', _QUEUE_ALL_FLAG))
PINAX_NOTIFICATIONS_LOCK_WAIT_TIMEOUT = os.environ.get('NOTIFICATIONS_LOCK_WAIT_TIMEOUT', 600)

# explicitly define NOTIFICATION_LOCK_LOCATION
# NOTIFICATION_LOCK_LOCATION = <path>

# pinax.notifications
# or notification
NOTIFICATIONS_MODULE = 'pinax.notifications'
ADMINS_ONLY_NOTICE_TYPES = ast.literal_eval(os.getenv('ADMINS_ONLY_NOTICE_TYPES', "['monitoring_alert',]"))

# set to true to have multiple recipients in /message/create/
USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS = ast.literal_eval(
    os.environ.get('USER_MESSAGES_ALLOW_MULTIPLE_RECIPIENTS', 'True'))

if NOTIFICATIONS_MODULE and NOTIFICATIONS_MODULE not in INSTALLED_APPS:
    INSTALLED_APPS += (NOTIFICATIONS_MODULE, )

# ########################################################################### #
# SECURITY SETTINGS
# ########################################################################### #

ENABLE_APIKEY_LOGIN = ast.literal_eval(os.getenv('ENABLE_APIKEY_LOGIN', 'False'))

if ENABLE_APIKEY_LOGIN:
    MIDDLEWARE += ('geonode.security.middleware.LoginFromApiKeyMiddleware',)

# Require users to authenticate before using Geonode
if LOCKDOWN_GEONODE:
    MIDDLEWARE += \
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
            from django.contrib.gis.geos import GEOSGeometry  # noqa

# Keywords thesauri
# e.g. THESAURUS = {'name':'inspire_themes', 'required':True, 'filter':True}
# Required: (boolean, optional, default false) mandatory while editing metadata (not implemented yet)
# Filter: (boolean, optional, default false) a filter option on that thesaurus will appear in the main search page
# THESAURUS = {'name': 'inspire_themes', 'required': True, 'filter': True}

# ######################################################## #
# Advanced Resource Publishing Worklow Settings - START    #
# ######################################################## #

# option to enable/disable resource unpublishing for administrators and members
RESOURCE_PUBLISHING = ast.literal_eval(os.getenv('RESOURCE_PUBLISHING', 'False'))

# Each uploaded Dataset must be approved by an Admin before becoming visible
ADMIN_MODERATE_UPLOADS = ast.literal_eval(os.environ.get('ADMIN_MODERATE_UPLOADS', 'False'))

# If this option is enabled, Resources belonging to a Group (with access private) won't be
# visible by others
GROUP_PRIVATE_RESOURCES = ast.literal_eval(os.environ.get('GROUP_PRIVATE_RESOURCES', 'False'))

# If this option is enabled, Groups will become strictly Mandatory on
# Metadata Wizard
GROUP_MANDATORY_RESOURCES = ast.literal_eval(os.environ.get('GROUP_MANDATORY_RESOURCES', 'False'))

# ######################################################## #
# Advanced Resource Publishing Worklow Settings - END      #
# ######################################################## #

# A boolean which specifies wether to display the email in user's profile
SHOW_PROFILE_EMAIL = ast.literal_eval(os.environ.get('SHOW_PROFILE_EMAIL', 'False'))

# Enables cross origin requests for geonode-client
MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS = ast.literal_eval(os.getenv(
    'MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS',
    'False'
))

ACCOUNT_OPEN_SIGNUP = ast.literal_eval(os.environ.get('ACCOUNT_OPEN_SIGNUP', 'True'))
ACCOUNT_APPROVAL_REQUIRED = ast.literal_eval(
    os.getenv('ACCOUNT_APPROVAL_REQUIRED', 'False')
)
ACCOUNT_ADAPTER = 'geonode.people.adapters.LocalAccountAdapter'
ACCOUNT_AUTHENTICATION_METHOD = os.environ.get('ACCOUNT_AUTHENTICATION_METHOD', 'username_email')
ACCOUNT_CONFIRM_EMAIL_ON_GET = ast.literal_eval(os.environ.get('ACCOUNT_CONFIRM_EMAIL_ON_GET', 'True'))
ACCOUNT_EMAIL_REQUIRED = ast.literal_eval(os.environ.get('ACCOUNT_EMAIL_REQUIRED', 'True'))
ACCOUNT_EMAIL_VERIFICATION = os.environ.get('ACCOUNT_EMAIL_VERIFICATION', 'none')

# Since django-allauth 0.43.0.
ACCOUNT_SIGNUP_REDIRECT_URL = os.environ.get('ACCOUNT_SIGNUP_REDIRECT_URL', os.getenv('SITEURL', _default_siteurl))
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = int(os.getenv('ACCOUNT_LOGIN_ATTEMPTS_LIMIT', '3'))
ACCOUNT_MAX_EMAIL_ADDRESSES = int(os.getenv('ACCOUNT_MAX_EMAIL_ADDRESSES', '2'))

SOCIALACCOUNT_ADAPTER = 'geonode.people.adapters.SocialAccountAdapter'
SOCIALACCOUNT_AUTO_SIGNUP = ast.literal_eval(os.environ.get('SOCIALACCOUNT_AUTO_SIGNUP', 'True'))
# This will hide or show local registration form in allauth view. True will show form
SOCIALACCOUNT_WITH_GEONODE_LOCAL_SINGUP = strtobool(os.environ.get('SOCIALACCOUNT_WITH_GEONODE_LOCAL_SINGUP', 'True'))

# Uncomment this to enable Linkedin and Facebook login
# INSTALLED_APPS += (
#    'allauth.socialaccount.providers.linkedin_oauth2',
#    'allauth.socialaccount.providers.facebook',
# )

SOCIALACCOUNT_PROVIDERS = {
    'linkedin_oauth2': {
        'SCOPE': [
            'r_emailaddress',
            'r_liteprofile',
        ],
        'PROFILE_FIELDS': [
            'id',
            'email-address',
            'first-name',
            'last-name',
            'picture-url',
            'public-profile-url',
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
THUMBNAIL_GENERATOR = os.environ.get(
    'THUMBNAIL_GENERATOR', 'geonode.thumbs.thumbnails.create_gs_thumbnail_geonode')

THUMBNAIL_SIZE = {
    'width': int(os.environ.get('THUMBNAIL_GENERATOR_DEFAULT_SIZE_WIDTH', 240)),
    'height': int(os.environ.get('THUMBNAIL_GENERATOR_DEFAULT_SIZE_HEIGHT', 200))
}

THUMBNAIL_BACKGROUND = {
    # class generating thumbnail's background
    # 'class': 'geonode.thumbs.background.WikiMediaTileBackground',
    'class': 'geonode.thumbs.background.OSMTileBackground',
    # 'class': 'geonode.thumbs.background.GenericXYZBackground',
    # initialization parameters for generator instance, valid only for generic classes
    'options': {
        # 'url': URL for the generic xyz / tms service
        # 'tms': False by default. Set to True if the service is TMS
        # 'tile_size': tile size for the generic xyz service, default is 256
    },
    # example options for a TMS service
    # 'class': 'geonode.thumbs.background.GenericXYZBackground',
    # 'options': {
    #    'url': 'http://maps.geosolutionsgroup.com/geoserver/gwc/service/tms/1.0.0/osm%3Aosm_simple_light@EPSG%3A900913@png/{z}/{x}/{y}.png',
    #    'tms': True
    # },
}

# define the urls after the settings are overridden
if USE_GEOSERVER:
    LOCAL_GXP_PTYPE = 'gxp_wmscsource'
    PUBLIC_GEOSERVER = {
        "source": {
            "title": "GeoServer - Public Layers",
            "attribution": f"&copy; {SITEURL}",
            "ptype": LOCAL_GXP_PTYPE,
            "url": f"{OGC_SERVER['default']['PUBLIC_LOCATION']}ows",
            "restUrl": "/gs/rest"
        }
    }
    LOCAL_GEOSERVER = {
        "source": {
            "title": "GeoServer - Private Layers",
            "attribution": f"&copy; {SITEURL}",
            "ptype": LOCAL_GXP_PTYPE,
            "url": "/gs/ows",
            "restUrl": "/gs/rest"
        }
    }
    baselayers = MAP_BASELAYERS
    MAP_BASELAYERS = [PUBLIC_GEOSERVER]
    MAP_BASELAYERS.extend(baselayers)

# Settings for MONITORING plugin
MONITORING_ENABLED = ast.literal_eval(os.environ.get('MONITORING_ENABLED', 'False'))

MONITORING_CONFIG = os.getenv("MONITORING_CONFIG", None)
MONITORING_HOST_NAME = os.getenv("MONITORING_HOST_NAME", HOSTNAME)
MONITORING_SERVICE_NAME = os.getenv("MONITORING_SERVICE_NAME", 'geonode')

# how long monitoring data should be stored
MONITORING_DATA_TTL = timedelta(days=int(os.getenv("MONITORING_DATA_TTL", 365)))

# this will disable csrf check for notification config views,
# use with caution - for dev purpose only
MONITORING_DISABLE_CSRF = ast.literal_eval(os.environ.get('MONITORING_DISABLE_CSRF', 'False'))

if MONITORING_ENABLED:
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

USER_ANALYTICS_ENABLED = ast.literal_eval(os.getenv('USER_ANALYTICS_ENABLED', 'False'))
USER_ANALYTICS_GZIP = ast.literal_eval(os.getenv('USER_ANALYTICS_GZIP', 'False'))

GEOIP_PATH = os.getenv('GEOIP_PATH', os.path.join(PROJECT_ROOT, 'GeoIPCities.dat'))
# This controls if tastypie search on resourches is performed only with titles
SEARCH_RESOURCES_EXTENDED = strtobool(os.getenv('SEARCH_RESOURCES_EXTENDED', 'True'))
# -- END Settings for MONITORING plugin

CATALOG_METADATA_TEMPLATE = os.getenv("CATALOG_METADATA_TEMPLATE", "catalogue/full_metadata.xml")

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
UI_DEFAULT_MANDATORY_FIELDS = [
    'id_resource-title',
    'id_resource-abstract',
    'id_resource-language',
    'id_resource-license',
    'id_resource-regions',
    'id_resource-date_type',
    'id_resource-date',
    'category_form',
    'id_resource-attribution',
    'id_resource-constraints_other',
    'id_resource-data_quality_statement',
    'id_resource-restriction_code_type'
]
UI_REQUIRED_FIELDS = ast.literal_eval(os.getenv('UI_REQUIRED_FIELDS ', '[]'))

UPLOAD_SESSION_EXPIRY_HOURS = os.getenv('UPLOAD_SESSION_EXPIRY_HOURS ', 24)

# If a command name is listed here, the command will be available to admins over http
# This list is used by the management_commands_http app
MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP = set([
    "ping_mngmt_commands_http",
    "updatelayers",
    "sync_geonode_datasets",
    "sync_geonode_maps",
    "importlayers",
    "set_all_datasets_metadata",
] + ast.literal_eval(os.getenv('MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP ', '[]')))


FILE_UPLOAD_HANDLERS = [
    'geonode.upload.uploadhandler.SizeRestrictedFileUploadHandler',
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]

DEFAULT_MAX_UPLOAD_SIZE = int(os.getenv('DEFAULT_MAX_UPLOAD_SIZE', 104857600))  # 100 MB
DEFAULT_BUFFER_CHUNK_SIZE = int(os.getenv('DEFAULT_BUFFER_CHUNK_SIZE', 64 * 1024))
DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER = int(os.getenv('DEFAULT_MAX_PARALLEL_UPLOADS_PER_USER', 5))

'''
Default schema used to store extra and dynamic metadata for the resource
'''

DEFAULT_EXTRA_METADATA_SCHEMA = {
    Optional("id"): int,
    "filter_header": object,
    "field_name": object,
    "field_label": object,
    "field_value": object,
}

'''
If present, will extend the available metadata schema used for store
new value for each resource. By default overrided the existing one.
The expected schema is the same as the default
'''
CUSTOM_METADATA_SCHEMA = os.getenv('CUSTOM_METADATA_SCHEMA ', {})

'''
Variable used to actually get the expected metadata schema for each resource_type.
In this way, each resource type can have a different metadata schema
'''

EXTRA_METADATA_SCHEMA = {**{
    "map": os.getenv('MAP_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
    "dataset": os.getenv('DATASET_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
    "document": os.getenv('DOCUMENT_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA),
    "geoapp": os.getenv('GEOAPP_EXTRA_METADATA_SCHEMA', DEFAULT_EXTRA_METADATA_SCHEMA)
}, **CUSTOM_METADATA_SCHEMA}


'''
Define the URLs patterns used by the SizeRestrictedFileUploadHandler
to evaluate if the file is greater than the limit size defined
'''

SIZE_RESTRICTED_FILE_UPLOAD_ELEGIBLE_URL_NAMES = ("data_upload", "uploads-upload", "document_upload",)

SUPPORTED_DATASET_FILE_TYPES = [
    {
        "id": "shp",
        "label": "ESRI Shapefile",
        "format": "vector",
        "ext": ["shp"],
        "requires": ["shp", "prj", "dbf", "shx"],
        "optional": ["xml", "sld"]
    },
    {
        "id": "tiff",
        "label": "GeoTIFF",
        "format": "raster",
        "ext": ["tiff", "tif"],
        "mimeType": ["image/tiff"],
        "optional": ["xml", "sld"]
    },
    {
        "id": "csv",
        "label": "Comma Separated Value (CSV)",
        "format": "vector",
        "ext": ["csv"],
        "mimeType": ["text/csv"],
        "optional": ["xml", "sld"]
    },
    {
        "id": "zip",
        "label": "Zip Archive",
        "format": "archive",
        "ext": ["zip"],
        "mimeType": ["application/zip"],
        "optional": ["xml", "sld"]
    },
    {
        "id": "xml",
        "label": "XML Metadata File",
        "format": "metadata",
        "ext": ["xml"],
        "mimeType": ["application/json"],
        "needsFiles": ["shp", "prj", "dbf", "shx", "csv", "tiff", "zip", "sld"]
    },
    {
        "id": "sld",
        "label": "Styled Layer Descriptor (SLD)",
        "format": "metadata",
        "ext": ["sld"],
        "mimeType": ["application/json"],
        "needsFiles": ["shp", "prj", "dbf", "shx", "csv", "tiff", "zip", "xml"]
    }
]
