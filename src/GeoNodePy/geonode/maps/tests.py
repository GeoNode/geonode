from django.test import TestCase
from geonode.maps.models import Map
from geonode.maps.views import build_map_config

class MapTest(TestCase):
    fixtures = ['testdata.json']

    default_abstract = "This is a demonstration of GeoNode, an application \
for assembling and publishing web based maps.  After adding layers to the map, \
use the 'Save Map' button above to contribute your map to the GeoNode \
community." 

    default_title = "GeoNode Default Map"

    def test_map_json(self):
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
