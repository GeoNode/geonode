from django.conf import settings
from django.test import TestCase
from django.test.client import Client

import geonode.maps.models

from geonode.maps.models import Map, Layer
from geonode.maps.views import DEFAULT_MAP_CONFIG
from geonode.maps.utils import upload, file_upload, GeoNodeException

from geoserver.catalog import FailedRequestError

from gs_helpers import cascading_delete

from mock import Mock

import json
import unittest
import os
import urllib2

#_gs_resource = Mock()
#_gs_resource.native_bbox = [1, 2, 3, 4]
#Layer.objects.geonetwork = Mock()
#Layer.objects.gs_catalog = Mock()
#Layer.objects.gs_catalog.get_resource.return_value = _gs_resource

#geonode.maps.models.get_csw = Mock()
#geonode.maps.models.get_csw.return_value.records.get.return_value.identification.keywords = { 'list': [] }
#geonode.maps.models.get_csw.return_value.records.get.return_value.distribution.onlineresource.url = "http://example.com/"
#geonode.maps.models.get_csw.return_value.records.get.return_value.distribution.onlineresource.description= "bogus data"

TEST_DATA = os.path.join(settings.GEONODE_HOME,
                       'geonode_test_data')

def check_layer(uploaded):
    """Verify if an object is a valid Layer.
    """
    msg = ('Was expecting layer object, got %s' % (type(uploaded)))
    assert type(uploaded) is Layer, msg
    msg = ('The layer does not have a valid name: %s' % uploaded.name)
    assert len(uploaded.name) > 0, msg


def get_web_page(url, username=None, password=None):
    """Get url page possible with username and password.
    """

    if username is not None:

        # Create password manager
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
        passman.add_password(None, url, username, password)

        # create the handler
        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        opener = urllib2.build_opener(authhandler)
        urllib2.install_opener(opener)

    try:
        pagehandle = urllib2.urlopen(url)
    except HTTPError, e:
        msg = ('The server couldn\'t fulfill the request. '
                'Error code: ' % e.code)
        e.args = (msg,)
        raise
    except urllib2.URLError, e:
        msg = 'Could not open URL "%s": %s' % (url, e)
        e.args = (msg,)
        raise
    else:
        page = pagehandle.readlines()

    return page


class MapTest(TestCase):
    """Tests geonode.maps app/module
    """

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

    def test_layer_save_to_geoserver(self):
        pass

    def test_layer_save_to_geonetwork(self):
        pass

    def test_post_save_layer(self):
        pass 

    def test_layer_verify(self):
        pass

    def test_layer_download_links(self):
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
        """Verify that layer is correctly deleted from GeoServer
        """

        # Layer.delete_from_geoserver() uses cascading_delete()
        # Should we explicitly test that the styles and store are
        # deleted as well as the resource itself?
        # There is already an explicit test for cascading delete
        
        gs_cat = Layer.objects.gs_catalog
    
        # Test Uploading then Deleting a Shapefile from GeoServer
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_resource(shp_layer.name, store=shp_store))
        
        # Test Uploading then Deleting a TIFF file from GeoServer
        tif_file = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        tif_layer = file_upload(tif_file)
        tif_store = gs_cat.get_store(tif_layer.name)
        tif_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_resource(shp_layer.name, store=tif_store))

        # Clean up and completely delete the Layers from GeoNode and GeoNetwork?

    def test_layer_delete_from_geonetwork(self):
        """Verify that layer is correctly deleted from GeoNetwork
        """

        gn_cat = Layer.objects.gn_catalog
         
        # Test Uploading then Deleting a Shapefile from GeoNetwork
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_layer.delete_from_geonetwork()
        shp_layer_info = gn_cat.get_by_uuid(shp_layer.uuid)
        assert shp_layer_info == None

        # Test Uploading then Deleting a TIFF file from GeoNetwork
        tif_file = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        tif_layer = file_upload(tif_file)
        tif_layer.delete_from_geonetwork()
        tif_layer_info = gn_cat.get_by_uuid(tif_layer.uuid)
        assert tif_layer_info == None

        # Clean up and completely delete the Layers from GeoNode and GeoServer?

    def test_delete_layer(self):
        """Verify that the 'delete_layer' pre_delete hook is functioning
        """
        gs_cat = Layer.objects.gs_catalog
        gn_cat = Layer.objects.gn_catalog
        
        # Upload a Shapefile Layer
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_store_name = shp_store.name

        id = shp_layer.pk
        name = shp_layer.name
        uuid = shp_layer.uuid

        # Delete it with the Layer.delete() method
        shp_layer.delete()
        
        # Verify that it no longer exists in GeoServer
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_resource(name, store=shp_store))
       
        # Should we also verify that the store was deleted
        
        # Verify that it no longer exists in GeoNetwork
        shp_layer_gn_info = gn_cat.get_by_uuid(uuid)
        assert shp_layer_gn_info == None

        # Should we also check that it was deleted from GeoNodes DB?

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

    def test_map_controller(self):
        pass

    def test_new_map(self):
        pass

    def test_map_save(self):
        """POST /maps -> Test saving a new map"""

        # since django's test client doesn't support providing a JSON request
        # body, just test the model directly. 
        # the view's hooked up right, I promise.
        map = Map(zoom=7, center_x=0, center_y=0)
        map.save() # can't attach layers to a map whose pk isn't set yet
        map.update_from_viewer(json.loads(self.viewer_config))
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
        """ Make some assertions about the data structure produced for serialization
            to a JSON map configuration """
        map = Map.objects.get(id=1)
        cfg = map.viewer_json()
        self.assertEquals(cfg['about']['abstract'], MapTest.default_abstract)
        self.assertEquals(cfg['about']['title'], MapTest.default_title)
        def is_wms_layer(x):
            return cfg['sources'][x['source']]['ptype'] == 'gx_wmssource'
        layernames = [x['name'] for x in cfg['map']['layers'] if is_wms_layer(x)]
        self.assertEquals(layernames, ['base:CA',])

    def test_map_details(self): 
        """/maps/1 -> Test accessing the detail view of a map"""
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

    # Much of this will be replaced by tests of maps/utils.py (see below)

    def test_upload_layer(self):
        """Test uploading a layer to a running GeoNode/GeoServer/GeoNetwork
        """
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

    # maps/utils.py tests

    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """
        layers = {}
        expected_layers = []
        not_expected_layers = []
        datadir = TEST_DATA
        BAD_LAYERS = [
            'lembang_schools_percentage_loss.shp',
        ]

        for filename in os.listdir(datadir):
            basename, extension = os.path.splitext(filename)
            if extension.lower() in ['.asc', '.tif', '.shp', '.zip']:
                if filename not in BAD_LAYERS:
                    expected_layers.append(os.path.join(datadir, filename))
                else:
                    not_expected_layers.append(
                                    os.path.join(datadir, filename)
                                             )
        uploaded = upload(datadir)

        for item in uploaded:
            errors = 'errors' in item
            if errors:
                # should this file have been uploaded?
                if item['file'] in not_expected_layers:
                    continue
                msg = 'Could not upload %s. ' % item['file']
                assert errors is False, msg + 'Error was: %s' % item['errors']
                msg = ('Upload should have returned either "name" or '
                  '"errors" for file %s.' % item['file'])
            else:
                assert 'name' in item, msg
                layers[item['file']] = item['name']

        msg = ('There were %s compatible layers in the directory,'
               ' but only %s were sucessfully uploaded' %
               (len(expected_layers), len(layers)))
        assert len(layers) == len(expected_layers), msg

        uploaded_layers = [layer for layer in layers.items()]

        for layer in expected_layers:
            msg = ('The following file should have been uploaded'
                   'but was not: %s. ' % layer)
            assert layer in layers, msg

            layer_name = layers[layer]

            # Check the layer is in the Django database
            Layer.objects.get(name=layer_name)

            # Check that layer is in geoserver
            found = False
            gs_username, gs_password = settings.GEOSERVER_CREDENTIALS
            page = get_web_page(os.path.join(settings.GEOSERVER_BASE_URL,
                                             'rest/layers'),
                                             username=gs_username,
                                             password=gs_password)
            for line in page:
                if line.find('rest/layers/%s.html' % layer_name) > 0:
                    found = True
            if not found:
                msg = ('Upload could not be verified, the layer %s is not '
                   'in geoserver %s, but GeoNode did not raise any errors, '
                   'this should never happen.' %
                   (layer_name, settings.GEOSERVER_BASE_URL))
                raise GeoNodeException(msg)

        server_url = settings.GEOSERVER_BASE_URL + 'ows?'
        # Verify that the GeoServer GetCapabilities record is accesible:
        metadata = get_layers_metadata(server_url, '1.0.0')
        msg = ('The metadata list should not be empty in server %s'
                % server_url)
        assert len(metadata) > 0, msg
        # Check the keywords are recognized too

    def test_extension_not_implemented(self):
        """Verify a GeoNodeException is returned for not compatible extensions
        """
        sampletxt = os.path.join(TEST_DATA, 'lembang_schools_percentage_loss.dbf')
        try:
            file_upload(sampletxt)
        except GeoNodeException, e:
            pass
        except Exception, e:
            msg = ('Was expecting a %s, got %s instead.' %
                   (GeoNodeException, type(e)))
            assert e is GeoNodeException, msg


    def test_shapefile(self):
        """Test Uploading a good shapefile
        """
        thefile = os.path.join(TEST_DATA, 'lembang_schools.shp')
        uploaded = file_upload(thefile)
        check_layer(uploaded)


    def test_bad_shapefile(self):
        """Verifying GeoNode complains about a shapefile without .prj
        """

        thefile = os.path.join(TEST_DATA, 'lembang_schools_percentage_loss.shp')
        try:
            uploaded = file_upload(thefile)
        except GeoNodeException, e:
            pass
        except Exception, e:
            msg = ('Was expecting a %s, got %s instead.' %
                   (GeoNodeException, type(e)))
            assert e is GeoNodeException, msg


    def test_tiff(self):
        """Uploading a good .tiff
        """
        thefile = os.path.join(TEST_DATA, 'lembang_mmi_hazmap.tif')
        uploaded = file_upload(thefile)
        check_layer(uploaded)


    def test_asc(self):
        """Uploading a good .asc
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.asc')
        uploaded = file_upload(thefile)
        check_layer(uploaded)


    def test_repeated_upload(self):
        """Upload the same file more than once
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.asc')
        uploaded1 = file_upload(thefile)
        check_layer(uploaded1)
        uploaded2 = file_upload(thefile, overwrite=True)
        check_layer(uploaded2)
        uploaded3 = file_upload(thefile, overwrite=False)
        check_layer(uploaded3)
        msg = ('Expected %s but got %s' % (uploaded1.name, uploaded2.name))
        assert uploaded1.name == uploaded2.name, msg
        msg = ('Expected a different name when uploading %s using '
               'overwrite=False but got %s' % (thefile, uploaded3.name))
        assert uploaded1.name != uploaded3.name, msg
    
    # gs_helpers tests

    def test_fixup_style(self):
        pass

    def test_cascading_delete(self):
        """Verify that the gs_helpers.cascading_delete() method is working properly
        """

        gs_cat = Layer.objects.gs_catalog

        # Upload a Shapefile
        shp_file = os.path.join(TEST_DATA, 'lembang_schools.shp')
        shp_layer = file_upload(shp_file)
       
        # Save the names of the Resource/Store/Styles 
        resource_name = shp_layer.resource.name
        store = shp_layer.resource.store
        store_name = store.name
        layer = gs_cat.get_layer(resource_name)
        styles = layer.styles + [layer.default_style]
        
        # Delete the Layer using cascading_delete()
        cascading_delete(gs_cat, shp_layer.resource)
        
        # Verify that the styles were deleted
        for style in styles:
            s = gs_cat.get_style(style)
            assert s == None
        
        # Verify that the resource was deleted
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_resource(resource_name, store=store))

        # Verify that the store was deleted 
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_store(store_name))

        # Clean up by deleting the layer from GeoNode's DB and GeoNetwork?
