from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "geonode.settings")

from geonode.layers.models import Layer
osm_layers = Layer.objects.filter(workspace='osm')
cnt = 1
total = len(osm_layers)
for l in osm_layers:
    print '#' * 40
    print '%s/%s Layer Name: %s' % (cnt, total, l.name)
    l.abstract = '''This layer is acquired from OpenStreetMap (OSM) and is not a product of the DREAM/PHIL-LiDAR 1 Program.

LiPAD uses basemaps from OSM.

(c) OpenStreetMap contributors

https://www.openstreetmap.org/copyright'''
    l.save()
    cnt += 1
    print 'OK'
