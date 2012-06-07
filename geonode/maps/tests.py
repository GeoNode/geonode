# -*- coding: utf-8 -*-
from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, AnonymousUser
from django.utils import simplejson as json
from django.core.files.uploadedfile import SimpleUploadedFile

import geonode.maps.models
import geonode.maps.views

from geonode.layers.models import Layer
from geonode.layers.forms import JSONField, LayerUploadForm
from geonode.maps.models import Map
from geonode.maps.utils import get_valid_user, GeoNodeException

from mock import Mock, patch

import os
import base64
import math

_gs_resource = Mock()
_gs_resource.native_bbox = [1, 2, 3, 4]

Layer.objects.geonetwork = Mock()
Layer.objects.gs_catalog = Mock()

Layer.objects.gs_catalog.get_resource.return_value = _gs_resource

geonode.maps.models.get_csw = Mock()
geonode.maps.models.get_csw.return_value.records.get.return_value.identification.keywords = []

_csw_resource = Mock()
_csw_resource.protocol = "WWW:LINK-1.0-http--link"
_csw_resource.url = "http://example.com/"
_csw_resource.description = "example link"
geonode.maps.models.get_csw.return_value.records.get.return_value.distribution.online = [_csw_resource]
from geonode.maps.utils import forward_mercator, inverse_mercator

DUMMY_RESULT ={'rows': [], 'total':0, 'query_info': {'start':0, 'limit': 0, 'q':''}}

geonode.maps.views._metadata_search = Mock()
geonode.maps.views._metadata_search.return_value = DUMMY_RESULT

geonode.maps.views.get_csw = Mock()
geonode.maps.views.get_csw.return_value.getrecordbyid.return_value = None
geonode.maps.views.get_csw.return_value.records.values.return_value = [None]
geonode.maps.views._extract_links = Mock()
geonode.maps.views._extract_links.return_value = {}

class MapsTest(TestCase):
    """Tests geonode.maps app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    fixtures = ['test_data.json', 'map_data.json']

    default_abstract = "This is a demonstration of GeoNode, an application \
for assembling and publishing web based maps.  After adding layers to the map, \
use the Save Map button above to contribute your map to the GeoNode \
community." 

    default_title = "GeoNode Default Map"

    # This is a valid map viewer config, based on the sample data provided
    # by andreas in issue 566. -dwins
    viewer_config = """
    {
      "defaultSourceType": "gx_wmssource",
      "about": {
          "title": "Title",
          "abstract": "Abstract"
      },
      "sources": {
        "capra": {
          "url":"http://localhost:8001/geoserver/wms"
        }
      },
      "map": {
        "projection":"EPSG:900913",
        "units":"m",
        "maxResolution":156543.0339,
        "maxExtent":[-20037508.34,-20037508.34,20037508.34,20037508.34],
        "center":[-9428760.8688778,1436891.8972581],
        "layers":[{
          "source":"capra",
          "buffer":0,
          "wms":"capra",
          "name":"base:nic_admin"
        }],
        "keywords":["saving", "keywords"],
        "zoom":7
      }
    }
    """

    viewer_config_alternative = """
    {
      "defaultSourceType": "gx_wmssource",
      "about": {
          "title": "Title2",
          "abstract": "Abstract2"
      },
      "sources": {
        "capra": {
          "url":"http://localhost:8001/geoserver/wms"
        }
      },
      "map": {
        "projection":"EPSG:900913",
        "units":"m",
        "maxResolution":156543.0339,
        "maxExtent":[-20037508.34,-20037508.34,20037508.34,20037508.34],
        "center":[-9428760.8688778,1436891.8972581],
        "layers":[{
          "source":"capra",
          "buffer":0,
          "wms":"capra",
          "name":"base:nic_admin"
        }],
        "zoom":7
      }
    }
    """

    def test_map_json(self):
        c = Client()

        # Test that saving a map when not logged in gives 401
        response = c.put("/maps/1/data",data=MapTest.viewer_config,content_type="text/json")
        self.assertEqual(response.status_code,401)

        c.login(username="bobby", password="bob")
        response = c.put("/maps/1/data",data=MapTest.viewer_config_alternative,content_type="text/json")
        self.assertEqual(response.status_code,204)

        map_obj = Map.objects.get(id=1)
        self.assertEquals(map_obj.title, "Title2")
        self.assertEquals(map_obj.abstract, "Abstract2")
        self.assertEquals(map_obj.layer_set.all().count(), 1)

    def test_map_save(self):
        """POST /maps -> Test saving a new map"""

        c = Client()

        # Test that saving a map when not logged in gives 401
        response = c.post("/maps/",data=MapTest.viewer_config,content_type="text/json")
        self.assertEqual(response.status_code,401)

        # Test successful new map creation
        c.login(username="bobby", password="bob")
        response = c.post("/maps/",data=MapTest.viewer_config,content_type="text/json")
        self.assertEquals(response.status_code,201)
        map_id = int(response['Location'].split('/')[-1])
        c.logout()

        self.assertEquals(map_id,2)
        map_obj = Map.objects.get(id=map_id)
        self.assertEquals(map_obj.title, "Title")
        self.assertEquals(map_obj.abstract, "Abstract")
        self.assertEquals(map_obj.layer_set.all().count(), 1)
        self.assertEquals(map_obj.keyword_list(), ["keywords", "saving"])

        # Test an invalid map creation request
        c.login(username="bobby", password="bob")
        response = c.post("/maps/",data="not a valid viewer config",content_type="text/json")
        self.assertEquals(response.status_code,400)
        c.logout()

    def test_map_fetch(self):
        """/maps/[id]/data -> Test fetching a map in JSON"""
        map_obj = Map.objects.get(id="1")
        c = Client()
        response = c.get("/maps/%s/data" % map_obj.id)
        self.assertEquals(response.status_code, 200)
        cfg = json.loads(response.content)
        self.assertEquals(cfg["about"]["abstract"], self.default_abstract) 
        self.assertEquals(cfg["about"]["title"], self.default_title) 
        self.assertEquals(len(cfg["map"]["layers"]), 5) 

    def test_map_to_json(self):
        """ Make some assertions about the data structure produced for serialization
            to a JSON map configuration"""
        map_obj = Map.objects.get(id=1)
        cfg = map_obj.viewer_json()
        self.assertEquals(cfg['about']['abstract'], MapTest.default_abstract)
        self.assertEquals(cfg['about']['title'], MapTest.default_title)
        def is_wms_layer(x):
            return cfg['sources'][x['source']]['ptype'] == 'gxp_wmscsource'
        layernames = [x['name'] for x in cfg['map']['layers'] if is_wms_layer(x)]
        self.assertEquals(layernames, ['base:CA',])

    def test_newmap_to_json(self):
        """ Make some assertions about the data structure produced for serialization
            to a new JSON map configuration"""
        response = Client().get("/maps/new/data")
        cfg = json.loads(response.content)
        self.assertEquals(cfg['defaultSourceType'], "gxp_wmscsource")

    def test_map_details(self): 
        """/maps/1 -> Test accessing the detail view of a map"""
        map_obj = Map.objects.get(id=1) 
        c = Client() 
        response = c.get("/maps/%s" % map_obj.id)
        self.assertEquals(response.status_code,200) 

    def test_new_map_without_layers(self):
        # TODO: Should this test have asserts in it?
        client = Client()
        client.get("/maps/new")

    def test_new_map_with_layer(self):
        # TODO: Should this test have some assertions in it?
        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_gs:
            mock_gs.get_resource.return_value.latlon_bbox = ["0", "1", "0", "1"]
            client = Client()
            layer = Layer.objects.all()[0]
            client.get("/maps/new?layer=" + layer.typename)

    def test_new_map_with_empty_bbox_layer(self):
        # TODO: Should this test have assertions in it?
        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_gs:
            mock_gs.get_resource.return_value.latlon_bbox = ["0", "0", "0", "0"]
            client = Client()
            layer = Layer.objects.all()[0]
            client.get("/maps/new?layer=" + layer.typename)
