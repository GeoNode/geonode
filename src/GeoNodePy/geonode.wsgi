import site, os, sys

site.addsitedir('/var/www/worldmap/wsgi/worldmap/lib/python2.6/site-packages')
site.addsitedir('/var/www/worldmap/wsgi/worldmap/src')
site.addsitedir('/var/www/worldmap/wsgi/worldmap/src/GeoNodePy')
site.addsitedir('/var/www/worldmap/wsgi/worldmap/src/avatar')
site.addsitedir('/var/www/worldmap/wsgi/worldmap/src/owslib')
site.addsitedir('/var/www/worldmap/wsgi/worldmap/src/gsconfig.py/src')


os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()

sys.stdout = sys.stderr

