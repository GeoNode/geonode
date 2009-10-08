# Django settings for GeoNode project.
from utils import path_extrapolate
from django.utils.translation import ugettext as _

DEBUG = True
SITENAME = "CAPRA GeoNode"
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'development.db'
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
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'myv-y4#7j-d*p-__@j#*3z@!y24fz8%^z2v6atuy4bo9vqr1_a'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ROOT_URLCONF = 'geonode.urls'

TEMPLATE_DIRS = path_extrapolate('geonode/templates'), \
                path_extrapolate('django/contrib/admin/templates', 'django'),
               
GEOSERVER_BASE_URL = "http://capra.opengeo.org/geoserver/"
GOOGLE_API_KEY = "ABQIAAAAkofooZxTfcCv9Wi3zzGTVxTnme5EwnLVtEDGnh-lFVzRJhbdQhQgAhB1eT_2muZtc0dl-ZSWrtzmrw"

# NAVBAR expects a dict of dicts or a path to an ini file
#NAVBAR = path_extrapolate('geonode/core/templatetags/navbar.ini')
# @@ i18n replace 'text' w/ simply an i18n message?
NAVBAR = \
{'community': {'id': '%sLink',
               'item_class': '',
               'link_class': '',
               'text': 'Contributed Maps',
               'url': 'geonode.views.community'},
 'curated': {'id': '%sLink',
             'item_class': '',
             'link_class': '',
             'text': 'CAPRA Maps',
             'url': 'geonode.views.curated'},
 'data': {'id': '%sLink',
          'item_class': '',
          'link_class': '',
          'text': 'Data',
          'url': "geonode.views.static page='data'"},
 'developer': {'id': '%sLink',
               'item_class': '',
               'link_class': '',
               'text': 'For Developers',
               'url': "geonode.views.static page='developer'"},
 'help': {'id': '%sLink',
          'item_class': '',
          'link_class': '',
          'text': 'Help',
          'url': "geonode.views.static page='help'"},
 'index': {'id': '%sLink',
           'item_class': '',
           'link_class': '',
           'text': 'Featured Map',
           'url': 'geonode.views.index'},
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
          'visible': 'data\nindex\ncurated\ncommunity\ndeveloper\nhelp'}}


# Determines whether the minified or the "raw" JavaScript files are included.
# Only applies in development mode. (That is, when DEBUG==True)
#MINIFIED_RESOURCES = False
MINIFIED_RESOURCES = False

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'geonode.core',
    'geonode.maps',
    'geonode.layers',
    'geonode.proxy',

)

if DEBUG:
    if MINIFIED_RESOURCES: 
        MEDIA_LOCATIONS = {
            "ext_base": "http://extjs.cachefly.net/ext-2.2.1/",
            "ol_theme": "/static/theme/ol/style.css",
            "ol_script":"/static/script/OpenLayers.js",
            "gx_themes":"/static/theme/gx/",
            "gx_script":"/static/script/GeoExt.js",
            "app_themes": "/static/theme/app/",
            "app_script":"/static/script/GeoNode.js",
            "ux_script":"/static/script/ux.js",
        }                
    else:
        MEDIA_LOCATIONS = {
            "ext_base": "http://extjs.cachefly.net/ext-2.2.1/",
            "ol_theme": "/static/externals/openlayers/theme/default/style.css",
            "ol_script":"/static/externals/openlayers/lib/OpenLayers.js",
            "gx_themes":"/static/externals/geoext/resources/",
            "gx_script":"/static/externals/geoext/lib/GeoExt.js",
            "app_themes": "/static/src/theme/app/",
            "app_script":"/static/src/script/app/loader.js",
            "ux_script":"/static/src/script/ux/RowExpander.js",
        }
else:
    MEDIA_LOCATIONS = { } # TODO: Set up production mappings
