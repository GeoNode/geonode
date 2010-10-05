import os, sys
sys.path.append('/home/matt/installs/geonode/lib/python2.6/site-packages')
sys.path.append('/home/matt/installs/geonode/src')
sys.path.append('/home/matt/installs/geonode/src/GeoNodePy')
sys.path.append('/home/matt/installs/geonode/src/GeoNodePy/geonode')
sys.path.append('/home/matt/installs/geonode/src/avatar')
sys.path.append('/home/matt/installs/geonode/src/owslib')
sys.path.append('/home/matt/installs/geonode/src/gsconfig.py/src')

#sys.path.append('/home/matt/dev/python/pinax-env/geopinax')

os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'

import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

sys.stdout = sys.stderr
