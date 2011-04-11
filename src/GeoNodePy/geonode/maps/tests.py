from django.test import TestCase
from django.test.client import Client
from geonode.maps.models import Map, Layer
from geonode.maps.views import DEFAULT_MAP_CONFIG
from mock import Mock

import json, os
import geonode.maps.models

_gs_resource = Mock()
_gs_resource.native_bbox = [1, 2, 3, 4]
Layer.objects.geonetwork = Mock()
Layer.objects.gs_catalog = Mock()
Layer.objects.gs_catalog.get_resource.return_value = _gs_resource

geonode.maps.models.get_csw = Mock()
geonode.maps.models.get_csw.return_value.records.get.return_value.identification.keywords = { 'list': [] }
geonode.maps.models.get_csw.return_value.records.get.return_value.distribution.onlineresource.url = "http://example.com/"
geonode.maps.models.get_csw.return_value.records.get.return_value.distribution.onlineresource.description= "bogus data"

class MapTest(TestCase):

    fixtures = ['test_data.json', 'map_data.json']
    GEOSERVER = False

    def setUp(self):
        # If Geoserver and GeoNetwork are not running
        # avoid running tests that call those views.
        if "GEOSERVER" in os.environ:
            self.GEOSERVER = True

    default_abstract = "This is a demonstration of GeoNode, an application \
for assembling and publishing web based maps.  After adding layers to the map, \
use the Save Map button above to contribute your map to the GeoNode \
community." 

    default_title = "GeoNode Default Map"

    # maps/models.py tests

    # maps.models.Layer

    def test_layer_download_links(self):
        pass

    def test_layer_verify(self):
        pass

    def test_layer_maps(self):
        pass

    def test_layer_metadata(self):
        pass
    
    def test_layer_metadata_csw(self):
        pass

    def test_layer_attribute_names(self):
        pass

    def test_layer_display_type(self):
        pass

    def test_layer_delete_from_geoserver(self):
        pass

    def test_layer_delete_from_geonetwork(self):
        pass

    def test_layer_save_to_geonetwork(self):
        pass

    def test_layer_resource(self):
        pass

    def test_layer_get_metadata_links(self):
        pass

    def test_layer_set_metadata_links(self):
        pass

    def test_layer_get_default_style(self):
        pass
    
    def test_layer_set_default_style(self):
        pass

    def test_layer_get_styles(self):
        pass

    def test_layer_set_styles(self):
        pass

    def test_layer_service_type(self):
        pass

    def test_layer_publishing(self):
        pass

    def test_layer_poc_role(self):
        pass

    def test_layer_metadata_author_role(self):
        pass

    def test_layer_set_poc(self):
        pass

    def test_layer_get_poc(self):
        pass

    def test_layer_set_metadata_author(self):
        pass

    def test_layer_get_metadata_author(self):
        pass

    def test_layer_save_to_geoserver(self):
        pass

    def test_layer_populate_from_gs(self):
        pass

    def test_layer_autopopulate(self):
        pass

    def test_layer_populate_from_gn(self):
        pass

    def test_layer_keyword_list(self):
        pass

    def test_layer_set_bbox(self):
        pass

    def test_layer_get_absolute_url(self):
        pass

    def test_layer_set_default_permissions(self):
        pass

    # maps.models.Map

    def test_map_center(self):
        pass

    def test_map_layers(self):
        pass

    def test_map_local_layers(self):
        pass

    def test_map_json(self):
        pass

    def test_map_viewer_json(self):
        pass

    def test_map_update_from_viewer(self):
        pass

    def test_map_get_absolute_url(self):
        pass

    def test_map_set_default_permissions(self):
        pass

    # maps.models.MapLayerManager

    def test_mlm_from_viewer_config(self):
        pass
    
    # maps.models.MapLayer

    def test_map_layer_from_viewer_config(self):
        pass

    def test_map_layer_source_config(self):
        pass

    def test_map_layer_layer_config(self):
        pass

    def test_map_layer_local_link(self):
        pass

    # maps.models Util Methods

    def test_delete_layer(self):
        pass

    def test_post_save_layer(self):
        pass 

    # maps/views.py tests

    def test_project_center(self):
        pass

    def test_baselayer(self):
        pass

    def test_bbox_to_wkt(self):
        pass

    def test_view_js(self):
        pass

    def test_view(self):
        pass

    # Maps Tests

    def test_map_controller(self):
        pass

    def test_new_map(self):
        pass

    def test_map_save(self):
        """POST /maps -> Test saving a new map"""
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
            "zoom":7
          }
        }
        """

        # since django's test client doesn't support providing a JSON request
        # body, just test the model directly. 
        # the view's hooked up right, I promise.
        map = Map(zoom=7, center_x=0, center_y=0)
        map.save() # can't attach layers to a map whose pk isn't set yet
        map.update_from_viewer(json.loads(viewer_config))
        self.assertEquals(map.title, "Title")
        self.assertEquals(map.abstract, "Abstract")
        self.assertEquals(map.layer_set.all().count(), 1)

    def test_map_fetch(self):
        """/maps/[id]/data -> Test fetching a map in JSON"""
        map = Map.objects.get(id="1")
        c = Client()
        response = c.get("/maps/%s/data" % map.id)
        self.assertEquals(response.status_code, 200)
        cfg = json.loads(response.content)
        self.assertEquals(cfg["about"]["abstract"], self.default_abstract) 
        self.assertEquals(cfg["about"]["title"], self.default_title) 
        self.assertEquals(len(cfg["map"]["layers"]), 5) 

    def test_map_to_json(self):
        ''' Make some assertions about the data structure produced for serialization
            to a JSON map configuration '''
        map = Map.objects.get(id=1)
        cfg = map.viewer_json()
        self.assertEquals(cfg['about']['abstract'], MapTest.default_abstract)
        self.assertEquals(cfg['about']['title'], MapTest.default_title)
        def is_wms_layer(x):
            return cfg['sources'][x['source']]['ptype'] == 'gx_wmssource'
        layernames = [x['name'] for x in cfg['map']['layers'] if is_wms_layer(x)]
        self.assertEquals(layernames, ['base:CA',])

    def test_map_details(self): 
        '''/maps/1 -> Test accessing the detail view of a map'''
        map = Map.objects.get(id="1") 
        c = Client() 
        response = c.get("/maps/%s" % map.id)
        self.assertEquals(response.status_code,200) 

    def test_delete_map(self):
        pass

    def test_map_detail(self):
        pass

    def test_describe_map(self):
        pass

    def test_embed_map(self):
        pass

    # Batch Tests    
    
    def test_map_download(self):
        pass

    def test_check_download(self):
        pass

    def test_batch_layer_download(self):
        pass

    def test_batch_delete(self):
        pass

    # Permissions Tests

    def test_view_layer_permissions(self):
        pass

    def test_view_perms_context(self):
        pass

    def test_perms_info(self):
        pass

    def test_perms_info_json(self):
        pass

    def test_fix_map_perms_for_editor(self):
        pass

    def test_handle_perms_edit(self):
        pass

    def test_get_basic_auth_info(self):
        pass

    def test_layer_acls(self):
        pass

    def test_view_map_permissions(self):
        pass

    def test_set_map_permissions(self):
        pass

    def test_set_layer_permissions(self):
        pass

    def test_ajax_layer_permissions(self):
        pass

    def test_ajax_map_permissions(self):
        pass

    def test_batch_permissions(self):
        pass

    # Data Tests

    def test_data(self):
        '''/data/ -> Test accessing the data page'''
        c = Client()
        response = c.get('/data/')
        self.failUnlessEqual(response.status_code, 200)

    def test_browse_data(self):
        pass

    def test_describe_data(self):
        '''/data/base:CA?describe -> Test accessing the description of a layer '''

        from django.contrib.auth.models import User
        self.assertEqual(2, User.objects.all().count())
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
    
    # Layer Tests

    def test_upload_layer(self):
        pass

    def test_handle_layer_upload(self):
        pass

    def test_update_layer(self):
        pass

    def test_describe_layer(self):
        pass

    def test_remove_layer(self):
        pass

    def test_change_layer_default_style(self):
        pass

    def test_layer_controller(self):
        pass

    def test_extract_links(self):
        pass

    # Search Tests
    
    def test_search(self):
        '''/data/search/ -> Test accessing the data search page'''
        c = Client()
        response = c.get('/data/search/')
        self.failUnlessEqual(response.status_code, 200)

    def test_search_page(self):
        pass

    def test_build_search_result(self):
        pass

    def test_metadata_search(self):
        pass

    def test_search_result_detail(self):
        pass

    def test_split_query(self):
        pass
    
    def test_search_api(self):
        '''/data/search/api -> Test accessing the data search api JSON'''
        if self.GEOSERVER:
            c = Client()
            response = c.get('/data/search/api')
            self.failUnlessEqual(response.status_code, 200)

    def test_search_detail(self):
        '''
        /data/search/detail -> Test accessing the data search detail for a layer
        Disabled due to reliance on consistent UUIDs across loads.
        '''
        if self.GEOSERVER:
            layer = Layer.objects.all()[0]

            # save to geonetwork so we know the uuid is consistent between
            # django db and geonetwork
            layer.save_to_geonetwork()

            c = Client()
            response = c.get('/data/search/detail', {'uuid':layer.uuid})
            self.failUnlessEqual(response.status_code, 200)

    def test_search_template(self):
        from django.template import Context
        from django.template.loader import get_template

        layer = Layer.objects.all()[0]
        tpl = get_template("maps/csw/transaction_insert.xml")
        ctx = Context({
            'layer': layer,
        })
        md_doc = tpl.render(ctx)
        self.assert_("None" not in md_doc, "None in " + md_doc)

    def test_maps_search(self):
        pass

    def test_maps_search_page(self):
        pass

    def test_change_poc(self):
        pass

    # gs_helpers tests

    def test_fixup_style(self):
        pass

    def test_cascading_delete(self):
        pass 
