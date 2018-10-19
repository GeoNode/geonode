import os, hashlib
from geonode.settings import *



##################################
# Geoserver fix admin password
##################################

OGC_SERVER['default']['USER'] = open('/run/secrets/admin_username','r').read().strip()
OGC_SERVER['default']['PASSWORD'] = open('/run/secrets/admin_password','r').read().strip()

##################################
# Misc / debug / hack
##################################

# Celery
INSTALLED_APPS += ('django_celery_monitor','django_celery_results',) # TODO : add django-celery-monitor to core geonode
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_IGNORE_RESULT = False
CELERY_BROKER_URL = 'amqp://rabbitmq:5672'
CELERY_RESULT_BACKEND = 'django-db'

# We randomize the secret key (based on admin login)
SECRET_KEY = hashlib.sha512(open('/run/secrets/admin_username','r').read().strip() + open('/run/secrets/admin_password','r').read().strip()).hexdigest()

# We define ALLOWED_HOSTS
ALLOWED_HOSTS = ['nginx','127.0.0.1'] # We need this for internal api calls from geoserver and for healthchecks
if os.getenv('HTTPS_HOST'):
    ALLOWED_HOSTS.append( os.getenv('HTTPS_HOST') )
if os.getenv('HTTP_HOST'):
    ALLOWED_HOSTS.append( os.getenv('HTTP_HOST') )

# We define SITE_URL
if os.getenv('HTTPS_HOST'):
    SITEURL = 'https://{url}{port}/'.format(
        url=os.getenv('HTTPS_HOST'),
        port=':'+os.getenv('HTTPS_PORT') if os.getenv('HTTPS_PORT') != '443' else '',
    )
elif os.getenv('HTTP_HOST'):
    SITEURL = 'http://{url}{port}/'.format(
        url=os.getenv('HTTP_HOST'),
        port=':'+os.getenv('HTTP_PORT') if os.getenv('HTTP_PORT') != '80' else '',
    )
else:
    raise Exception("Misconfiguration error. You need to set at least one of HTTPS_HOST or HTTP_HOST")

# Manually replace SITEURL whereever it is used in geonode's settings.py (those settings are a mess...)
GEOSERVER_LOCATION = 'http://nginx/geoserver/'
GEOSERVER_PUBLIC_LOCATION = SITEURL + 'geoserver/'
GEOSERVER_URL = GEOSERVER_PUBLIC_LOCATION
OGC_SERVER['default']['LOCATION'] = GEOSERVER_LOCATION
OGC_SERVER['default']['PUBLIC_LOCATION'] = GEOSERVER_PUBLIC_LOCATION
CATALOGUE['default']['URL'] = '%scatalogue/csw' % SITEURL
PYCSW['CONFIGURATION']['metadata:main']['provider_url'] = SITEURL
PUBLIC_GEOSERVER["source"]["url"] = GEOSERVER_PUBLIC_LOCATION + "ows"

# We use django's default cache (geonode settings use dummy cache, which doesn't cache at all)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
