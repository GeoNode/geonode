import site, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
