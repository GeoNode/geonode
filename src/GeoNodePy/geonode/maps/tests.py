from django.test import TestCase
from geonode.maps.models import Map, Layer
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
        '''/maps/1 -> Test accessing the detail view of a map'''
        map = Map.objects.get(id="1") 
        c = Client() 
        response = c.get("/maps/%s" % map.id)
        self.assertEquals(response.status_code,200) 

    def test_data(self):
          '''/data/ -> Test accessing the data page'''
          c = Client()
          response = c.get('/data/')
          self.failUnlessEqual(response.status_code, 200)

    def test_search(self):
          '''/data/search/ -> Test accessing the data search page'''
          c = Client()
          response = c.get('/data/search/')
          self.failUnlessEqual(response.status_code, 200)

    def test_search_api(self):
         '''/data/search/api -> Test accessing the data search api JSON'''
         if self.GEOSERVER:
             c = Client()
             response = c.get('/data/search/api')
             self.failUnlessEqual(response.status_code, 200)


    def test_search_detail(self):
        '''/data/search/detail -> Test accessing the data search detail for a layer'''
        if self.GEOSERVER:
            layer = Layer.objects.all()[0]
            c = Client()
            response = c.get('/data/search/detail', {'uuid':layer.uuid})
            self.failUnlessEqual(response.status_code, 200)

    def test_describe_data(self):
          '''/data/base:CA?describe -> Test accessing the description of a layer '''

          c = Client()
          response = c.get('/data/base:CA?describe')
          # Since we are not authenticated, we should not be able to access it
          self.failUnlessEqual(response.status_code, 302)
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

