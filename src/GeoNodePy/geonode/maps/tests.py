from django.test import TestCase
from geonode.maps.models import Map
from django.test.client import Client
from geonode.maps.views import build_map_config, DEFAULT_MAP_CONFIG
import json
import os

class MapTest(TestCase):

    fixtures = ['test_data.json', 'map_data.json']
    GEOSERVER = False

    def setUp(self):
        # If Geoserver and GeoNetwork are not running
        # avoid running tests that call those views.
        if "GEOSERVER" in os.environ.keys():
            self.GEOSERVER = True

    default_abstract = "This is a demonstration of GeoNode, an application \
for assembling and publishing web based maps.  After adding layers to the map, \
use the &#39;Save Map&#39; button above to contribute your map to the GeoNode \
community." 

    default_title = "GeoNode Default Map"

    def test_map2json(self):
        ''' Make some assertions about the data structure produced for serialization
            to a JSON map configuration '''
        map = Map.objects.get(id=1)
        cfg = build_map_config(map)
        self.assertEquals(cfg['about']['abstract'], MapTest.default_abstract)
        self.assertEquals(cfg['about']['title'], MapTest.default_title)
        layernames = [x['name'] for x in cfg['map']['layers']]
        self.assertEquals(layernames, ['base:CA', 'base:nic_admin'])

    def test_mapdetails(self): 
        ''' Test accessing the detail view of a map '''
        map = Map.objects.get(id="1") 
        c = Client() 
        response = c.get("/maps/%s" % map.id)
        self.assertEquals(response.status_code,200) 

    def test_DescribeData(self):
          ''' Test accessing the description of a layer '''

          c = Client()
          response = c.get('/data/base:CA?describe')
          # Since we are not authenticated, we should not be able to access it
          self.failUnlessEqual(response.status_code, 403)
          # but if we log in ...
          c.login(username='bobby', password='bob')
          # ... all should be good
          if self.GEOSERVER:
              response = c.get('/data/base:CA?describe')
              self.failUnlessEqual(response.status_code, 200)
          else:
              # If Geoserver is not running, this should give a runtime error
              try:
                  c.get('/data/base:CA?describe')
              except RuntimeError:
                  pass

