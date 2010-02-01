from django.test import TestCase
from geonode.maps.models import Map
from django.test.client import Client
from geonode.maps.views import build_map_config, DEFAULT_MAP_CONFIG
import json

class MapTest(TestCase):
    fixtures = ['testdata.json']

    default_abstract = "This is a demonstration of GeoNode, an application \
for assembling and publishing web based maps.  After adding layers to the map, \
use the &#39;Save Map&#39; button above to contribute your map to the GeoNode \
community." 

    default_title = "GeoNode Default Map"

    def test_map2json(self):
        """
        Make some assertions about the data structure produced for
        serialization to a JSON map configuration
        """
        map = Map.objects.get(id=1)
        cfg = build_map_config(map)
        self.assertEquals(cfg['about']['abstract'], MapTest.default_abstract)
        self.assertEquals(cfg['about']['title'], MapTest.default_title)
        layernames = [x['name'] for x in cfg['map']['layers']]
        self.assertEquals(layernames, ['base:CA', 'base:nic_admin'])

    def test_json2map(self):
        from geonode.maps.views import read_json_map

        self.assertEquals(Map.objects.count(), 3)
        map = read_json_map(json.dumps(DEFAULT_MAP_CONFIG))
        self.assertEquals(Map.objects.count(), 4)

        # just testing that the map was created, no assertion needed since 
        # get() throws an exception if nothing matches
        Map.objects.get(id=map.id)

    def test_mapdetails(self): 
        map = Map.objects.get(id="1") 
        c = Client() 
        response = c.get("/maps/detail/%s" % map.id)
        self.assertEquals(response.status_code,200) 
