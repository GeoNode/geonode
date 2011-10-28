from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, AnonymousUser

import geonode.maps.models
import geonode.maps.views

from geonode.maps.models import Map, Layer, LayerCategory, LayerAttribute, User
from geonode.maps.utils import get_valid_user, GeoNodeException

from mock import Mock, patch

import json
import os
import base64

_gs_resource = Mock()
_gs_resource.native_bbox = [1, 2, 3, 4]
_gs_resource.storeType = 'dataStore'

Layer.objects.geonetwork = Mock()
Layer.objects.gs_catalog = Mock()

Layer.objects.gs_catalog.get_resource.return_value = _gs_resource

geonode.maps.models.get_csw = Mock()
geonode.maps.models.get_csw.return_value.records.get.return_value.identification.keywords = { 'list': [] }

_csw_resource = Mock()
_csw_resource.protocol = "WWW:LINK-1.0-http--link"
_csw_resource.url = "http://example.com/"
_csw_resource.description = "example link"
geonode.maps.models.get_csw.return_value.records.get.return_value.distribution.online = [_csw_resource]

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
        pass

    def test_layer_delete_from_geonetwork(self):
        pass

    def test_delete_layer(self):
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
        """Verify that Layer.set_default_permissions is behaving as expected
        """
        
        # Get a Layer object to work with 
        layer = Layer.objects.all()[0]

        # Should we set some 'current' permissions to do further testing?
        
        # Save the layers Current Permissions
        current_perms = layer.get_all_level_info()

        # Set the default permissions
        layer.set_default_permissions()

        # Test that LEVEL_READ is set for ANONYMOUS_USERS and AUTHENTICATED_USERS
        self.assertEqual(layer.get_gen_level(geonode.core.models.ANONYMOUS_USERS), layer.LEVEL_READ)
        self.assertEqual(layer.get_gen_level(geonode.core.models.AUTHENTICATED_USERS), layer.LEVEL_READ)

        # Test that the previous Permissions were set to LEVEL_NONE
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.assertEqual(layer.get_user_level(user), layer.LEVEL_NONE)

        # Test that the owner was assigned LEVEL_ADMIN
        if layer.owner:
            self.assertEqual(layer.owner, layer.LEVEL_ADMIN)

    # maps.models.Map

    def test_map_center(self):
        pass

    def test_map_layers(self):
        pass

    def test_map_local_layers(self):
        pass


    viewer_config_alternative = """
    {
      "defaultSourceType": "gx_wmssource",
      "about": {
          "title": "Title2",
          "abstract": "Abstract2",
          "urlsuffix" : "",
          "introtext": "",
          "keywords": ""
      },
      "sources": {
        "capra": {
          "url":"http://localhost:8001/geoserver/wms"
        }
      },
     "treeconfig" : {},
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

        log = c.login(username="bobby", password="bob")
        response = c.put("/maps/1/data",data=MapTest.viewer_config_alternative,content_type="text/json")
        self.assertEqual(response.status_code,204)

        map = Map.objects.get(id=1)
        self.assertEquals(map.title, "Title2")
        self.assertEquals(map.abstract, "Abstract2")
        self.assertEquals(map.layer_set.all().count(), 1)

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
          "abstract": "Abstract",
          "urlsuffix" : "",
          "introtext": "",
          "keywords": ""
      },
      "sources": {
        "capra": {
          "url":"http://localhost:8001/geoserver/wms"
        }
      },
      "treeconfig": {},
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

        c = Client()

        # Test that saving a map when not logged in gives 401
        response = c.post("/maps/",data=MapTest.viewer_config,content_type="text/json")
        self.assertEqual(response.status_code,401)

        # Test successful new map creation
        log = c.login(username="bobby", password="bob")
        response = c.post("/maps/",data=MapTest.viewer_config,content_type="text/json")
        self.assertEquals(response.status_code,201)
        map_id = int(response['Location'].split('/')[-1])
        c.logout()

        self.assertEquals(map_id,2)
        map = Map.objects.get(id=map_id)
        self.assertEquals(map.title, "Title")
        self.assertEquals(map.abstract, "Abstract")
        self.assertEquals(map.layer_set.all().count(), 1)

        # Test an invalid map creation request
        log = c.login(username="bobby", password="bob")
        response = c.post("/maps/",data="not a valid viewer config",content_type="text/json")
        self.assertEquals(response.status_code,400)
        c.logout()

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
            to a JSON map configuration"""
        map = Map.objects.get(id=1)
        cfg = map.viewer_json()
        self.assertEquals(cfg['about']['abstract'], MapTest.default_abstract)
        self.assertEquals(cfg['about']['title'], MapTest.default_title)
        def is_wms_layer(x):
            return cfg['sources'][x['source']]['ptype'] == 'gxp_gnsource'
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
        map = Map.objects.get(id=1) 
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

    # Users
    # - admin (pk=2)
    # - bobby (pk=1)

    # Inherited
    # - LEVEL_NONE = _none

    # Layer
    # - LEVEL_READ = layer_read
    # - LEVEL_WRITE = layer_readwrite
    # - LEVEL_ADMIN = layer_admin

    # Map 
    # - LEVEL_READ = map_read
    # - LEVEL_WRITE = map_readwrite
    # - LEVEL_ADMIN = map_admin
    

    # FIXME: Add a comprehensive set of permissions specifications that allow us 
    # to test as many conditions as is possible/necessary
    
    # If anonymous and/or authenticated are not specified, 
    # should set_layer_permissions remove any existing perms granted??
    
    perm_spec = {"anonymous":"_none","authenticated":"_none","users":[["admin","layer_readwrite"]]}
    
    def test_set_layer_permissions(self):
        """Verify that the set_layer_permissions view is behaving as expected
        """
        
        # Get a layer to work with
        layer = Layer.objects.all()[0]

        # Save the Layers current permissions
        current_perms = layer.get_all_level_info() 
       
        # FIXME Test a comprehensive set of permisssions specifications 

        # Set the Permissions
        geonode.maps.views.set_layer_permissions(layer, self.perm_spec)

        # Test that the Permissions for ANONYMOUS_USERS and AUTHENTICATED_USERS were set correctly        
        self.assertEqual(layer.get_gen_level(geonode.core.models.ANONYMOUS_USERS), layer.LEVEL_NONE) 
        self.assertEqual(layer.get_gen_level(geonode.core.models.AUTHENTICATED_USERS), layer.LEVEL_NONE)

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the layers owner) were removed
        users = [n for (n, p) in self.perm_spec['users']]
        levels = layer.get_user_levels().exclude(user__username__in = users + [layer.owner])
        self.assertEqual(len(levels), 0)
       
        # Test that the User permissions specified in the perm_spec were applied properly
        for username, level in self.perm_spec['users']:
            user = geonode.maps.models.User.objects.get(username=username)
            self.assertEqual(layer.get_user_level(user), level)

    def test_view_layer_permissions(self):
        """Verify that the view_layer_permissions view is behaving as expected
        """

        # I'm not sure this view is actually being used anywhere (jj0hns0n 2011-04-13)

        pass        

    def test_ajax_layer_permissions(self):
        """Verify that the ajax_layer_permissions view is behaving as expected
        """
        
        # Setup some layer names to work with 
        valid_layer_typename = Layer.objects.all()[0].typename
        invalid_layer_typename = "n0ch@nc3"

        c = Client()

        # Test that an invalid layer.typename is handled for properly
        response = c.post("/data/%s/ajax-permissions" % invalid_layer_typename, 
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")
        self.assertEquals(response.status_code, 404) 

        # Test that POST is required
        response = c.get("/data/%s/ajax-permissions" % valid_layer_typename)
        self.assertEquals(response.status_code, 405)
        
        # Test that a user is required to have maps.change_layer_permissions

        # First test un-authenticated
        response = c.post("/data/%s/ajax-permissions" % valid_layer_typename, 
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")
        self.assertEquals(response.status_code, 401) 

        # Next Test with a user that does NOT have the proper perms
        logged_in = c.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True) 
        response = c.post("/data/%s/ajax-permissions" % valid_layer_typename, 
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")
        self.assertEquals(response.status_code, 401) 

        # Login as a user with the proper permission and test the endpoint
        logged_in = c.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)
        response = c.post("/data/%s/ajax-permissions" % valid_layer_typename, 
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")

        # Test that the method returns 200         
        self.assertEquals(response.status_code, 200) 

        # Test that the permissions specification is applied

        # Should we do this here, or assume the tests in 
        # test_set_layer_permissions will handle for that?

    def test_layer_acls(self):
        """ Verify that the layer_acls view is behaving as expected
        """

        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = "%s:%s" % (settings.GEOSERVER_CREDENTIALS[0],settings.GEOSERVER_CREDENTIALS[1])
        invalid_uname_pw = "%s:%s" % ("n0t", "v@l1d")

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(valid_uname_pw),
        }
        
        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(invalid_uname_pw),
        }
       
        # Test that requesting when supplying the GEOSERVER_CREDENTIALS returns the expected json 
        expected_result = {'rw': [],'ro': [],'name': settings.GEOSERVER_CREDENTIALS[0],'is_superuser':  True,'is_anonymous': False}
        c = Client()
        response = c.get('/data/acls', **valid_auth_headers)
        response_json = json.loads(response.content)
        self.assertEquals(expected_result, response_json) 

        # Test that requesting when supplying invalid credentials returns the appropriate error code
        response = c.get('/data/acls', **invalid_auth_headers)
        self.assertEquals(response.status_code, 401)  
       
        # Test logging in using Djangos normal auth system 
        logged_in = c.login(username='admin', password='admin')
       
        # Basic check that the returned content is at least valid json
        response = c.get("/data/acls")
        response_json = json.loads(response.content)

        # TODO Lots more to do here once jj0hns0n understands the ACL system better

    def test_view_perms_context(self):
        # It seems that since view_layer_permissions and view_map_permissions
        # are no longer used, that this view is also no longer used since those
        # are the only 2 places it is ever called (jj0hns0n 2011-04-13)
 
        pass

    def test_perms_info(self):
        """ Verify that the perms_info view is behaving as expected
        """
        
        # Test with a Layer object
        layer = Layer.objects.all()[0]
        layer_info = layer.get_all_level_info()
        info = geonode.maps.views._perms_info(layer, geonode.maps.views.LAYER_LEV_NAMES)
        
        # Test that ANONYMOUS_USERS and AUTHENTICATED_USERS are set properly
        self.assertEqual(info[geonode.maps.models.ANONYMOUS_USERS], layer.LEVEL_READ)
        self.assertEqual(info[geonode.maps.models.AUTHENTICATED_USERS], layer.LEVEL_READ)
        
        self.assertEqual(info['users'], sorted(layer_info['users'].items()))

        # TODO Much more to do here once jj0hns0n understands the ACL system better
 
        # Test with a Map object
        # TODO

    def test_perms_info_json(self):
        # Should only need to verify that valid json is returned?
        pass

    def test_fix_map_perms_for_editor(self):
        # I'm not sure this view is actually being used anywhere (jj0hns0n 2011-04-13)
        pass

    def test_handle_perms_edit(self):
        # I'm not sure this view is actually being used anywhere (jj0hns0n 2011-04-13)
        pass

    def test_get_basic_auth_info(self):
        # How do we test this? Perhaps as a part of test_layer_acls
        pass

    def test_view_map_permissions(self):
        pass

    def test_set_map_permissions(self):
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

    # Test layer upload endpoint
    def test_upload_layer(self):
        c = Client()

        # Test redirection to login form when not logged in
        response = c.get("/data/upload")
        self.assertEquals(response.status_code,302)

        # Test return of upload form when logged in
        c.login(username="bobby", password="bob")
        response = c.get("/data/upload")
        self.assertEquals(response.status_code,200)

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
        c = Client()

        #test around _metadata_search helper
        with patch.object(geonode.maps.views,'_metadata_search') as mock_ms:
            result = {
                'rows' : [{
                        'uuid' : 1214431  # does not exist
                        }
                          ]
                }
            mock_ms.return_value = result

            response = c.get("/data/search/api?q=foo&start=5&limit=10")

            call_args = geonode.maps.views._metadata_search.call_args
            self.assertEqual(call_args[0][0], "foo")
            self.assertEqual(call_args[0][1], 5)
            self.assertEqual(call_args[0][2], 10)

    def test_search_result_detail(self):
        pass

    def test_split_query(self):
        query = 'alpha "beta gamma"   delta  '
        keywords = geonode.maps.views._split_query(query)
        self.assertEqual(keywords[0], "alpha")
        self.assertEqual(keywords[1], "beta gamma")
        self.assertEqual(keywords[2], "delta")
    
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

        layer = Layer.objects.get(pk=1)
        tpl = get_template("maps/csw/transaction_insert.xml")
        ctx = Context({
            'layer': layer,
        })
        md_doc = tpl.render(ctx)
        self.assert_(layer.name  in md_doc, "Layer name not in " + md_doc)


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

    def test_layer_save(self):
        lyr = Layer.objects.get(pk=1)
        lyr.storeType = 'dataStore'
        lyr.keywords = "saving keywords"
        lyr.topic_category = LayerCategory.objects.get(pk=1)
        lyr.save()
        self.assertEqual(lyr.keyword_list(), ["saving", "keywords"])
        self.assertEqual(lyr.resource.keywords, ["saving", "keywords"])
        self.assertEqual(_gs_resource.keywords, ["saving", "keywords"])



    def test_layer_attributes(self):
        lyr = Layer.objects.get(pk=1)
        attribute1 = LayerAttribute.objects.create(layer=lyr, attribute='ATTR1', attribute_label="Test Attribute 1", attribute_type="xsd:string", searchable=False, visible=True, display_order=3)
        attribute2 = LayerAttribute.objects.create(layer=lyr, attribute='ATTR2', attribute_label="Test Attribute 2", attribute_type="xsd:string", searchable=False, visible=False, display_order=1)
        attribute3 = LayerAttribute.objects.create(layer=lyr, attribute='ATTR3', attribute_label="Test Attribute 3", attribute_type="xsd:string", searchable=False, visible=True, display_order=2)

        # This method should return a sorted list containing details of attribute 3, then attribute 1 (based on display order);
        # attribute2 should not be included (visible=False)
        identify_attributes = lyr.layer_attributes()

        attribute_num = len(identify_attributes)
        msg = "Expected 2 attributes, received %s instead", attribute_num
        assert len(identify_attributes) == 2, msg

        attrFirst = identify_attributes[0]
        msg =  "Expected 1st attribute  to be 'Test Attribute 3, got %s instead", attrFirst["header"]
        assert attrFirst["header"] == "Test Attribute 3", msg

        attrSecond = identify_attributes[1]
        msg =  "Expected 2nd attribute  to be 'Test Attribute 3, got %s instead", attrSecond["header"]
        assert attrSecond["header"] == "Test Attribute 1", msg



    def test_get_valid_user(self):
        # Verify it accepts an admin user
        adminuser = User.objects.get(is_superuser=True)
        valid_user = get_valid_user(adminuser)
        msg = ('Passed in a valid admin user "%s" but got "%s" in return'
                % (adminuser, valid_user))
        assert valid_user.id == adminuser.id, msg

        # Verify it returns a valid user after receiving None
        valid_user = get_valid_user(None)
        msg = ('Expected valid user after passing None, got "%s"' % valid_user)
        assert isinstance(valid_user, User), msg

        newuser = User.objects.create(username='arieluser')
        valid_user = get_valid_user(newuser)
        msg = ('Passed in a valid user "%s" but got "%s" in return'
                % (newuser, valid_user))
        assert valid_user.id == newuser.id, msg

        valid_user = get_valid_user('arieluser')
        msg = ('Passed in a valid user by username "%s" but got'
               ' "%s" in return' % ('arieluser', valid_user))
        assert valid_user.username == 'arieluser', msg

        nn = AnonymousUser()
        self.assertRaises(GeoNodeException, get_valid_user, nn)

    def test_layer_generate_links(self):
        """Verify generating download/image links for a layer"""
        lyr = Layer.objects.get(pk=1)
        orig_bbox = lyr.resource.latlon_bbox
        lyr.resource.latlon_bbox = ["1", "2", "3", "3"]
        try:
            lyr.download_links()
        except ZeroDivisionError:
            self.fail("Threw division error while generating download links")
        finally:
            lyr.resource.latlon_bbox = orig_bbox

class ViewTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    fixtures = ['test_data.json', 'map_data.json']

    def test_new_map_without_layers(self):
        client = Client()
        response = client.get("/maps/new")

    def test_new_map_with_layer(self):
        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_gs:
            mock_gs.get_resource.return_value.latlon_bbox = ["0", "1", "0", "1"]
            client = Client()
            layer = Layer.objects.all()[0]
            response = client.get("/maps/new?layer=" + layer.typename)

    def test_new_map_with_empty_bbox_layer(self):
        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_gs:
            mock_gs.get_resource.return_value.latlon_bbox = ["0", "0", "0", "0"]
            client = Client()
            layer = Layer.objects.all()[0]
            response = client.get("/maps/new?layer=" + layer.typename)


from geonode.maps.forms import JSONField, LayerUploadForm, NewLayerUploadForm
from django.core.files.uploadedfile import SimpleUploadedFile

class FormTest(TestCase):

    ## NOTE: we don't care about file content for many of these tests (the
    ## forms under test validate based only on file name, and leave actual
    ## content inspection to GeoServer) but Django's form validation will omit
    ## any files with empty bodies. 
    ##
    ## That is, this leads to mysterious test failures:
    ##     SimpleUploadedFile('foo', '') 
    ##
    ## And this should be used instead to avoid that:
    ##     SimpleUploadedFile('foo', ' ')

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testJSONField(self):
        from django.forms import ValidationError

        field = JSONField()
        # a valid JSON document should pass
        field.clean('{ "users": [] }')

        # text which is not JSON should fail
        self.assertRaises(ValidationError, lambda: field.clean('<users></users>'))

    def testShapefileValidation(self):
        files = dict(
            base_file=SimpleUploadedFile('foo.shp', ' '),
            shx_file=SimpleUploadedFile('foo.shx', ' '),
            dbf_file=SimpleUploadedFile('foo.dbf', ' '),
            prj_file=SimpleUploadedFile('foo.prj', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', ' '),
            shx_file=SimpleUploadedFile('foo.SHX', ' '),
            dbf_file=SimpleUploadedFile('foo.DBF', ' '),
            prj_file=SimpleUploadedFile('foo.PRJ', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', ' '),
            shx_file=SimpleUploadedFile('foo.shx', ' '),
            dbf_file=SimpleUploadedFile('foo.dbf', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', ' '),
            shx_file=SimpleUploadedFile('foo.shx', ' '),
            dbf_file=SimpleUploadedFile('foo.dbf', ' '),
            prj_file=SimpleUploadedFile('foo.PRJ', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', ' '),
            shx_file=SimpleUploadedFile('bar.shx', ' '),
            dbf_file=SimpleUploadedFile('bar.dbf', ' '),
            prj_file=SimpleUploadedFile('bar.PRJ', ' '))
        self.assertFalse(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.shp', ' '),
            dbf_file=SimpleUploadedFile('foo.dbf', ' '),
            prj_file=SimpleUploadedFile('foo.PRJ', ' '))
        self.assertFalse(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.txt', ' '),
            shx_file=SimpleUploadedFile('foo.shx', ' '),
            dbf_file=SimpleUploadedFile('foo.sld', ' '),
            prj_file=SimpleUploadedFile('foo.prj', ' '))
        self.assertFalse(LayerUploadForm(dict(), files).is_valid())

    def testGeoTiffValidation(self):
        files = dict(base_file=SimpleUploadedFile('foo.tif', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.TIF', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.tiff', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.TIF', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.geotif', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.GEOTIF', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.geotiff', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.GEOTIF', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

    def testWriteFiles(self):
        files = dict(
            base_file=SimpleUploadedFile('foo.shp', ' '),
            shx_file=SimpleUploadedFile('foo.shx', ' '),
            dbf_file=SimpleUploadedFile('foo.dbf', ' '),
            prj_file=SimpleUploadedFile('foo.prj', ' '))
        form = LayerUploadForm(dict(), files)
        self.assertTrue(form.is_valid())

        tempdir, base_file, sld_file = form.write_files()
        self.assertEquals(set(os.listdir(tempdir)),
            set(['foo.shp', 'foo.shx', 'foo.dbf', 'foo.prj']))


class UtilsTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    fixtures = ['map_data.json']

    def test_layer_type(self):
        from geonode.maps.utils import layer_type
        from geoserver.resource import FeatureType, Coverage
        self.assertEquals(layer_type('foo.shp'), FeatureType.resource_type)
        self.assertEquals(layer_type('foo.SHP'), FeatureType.resource_type)
        self.assertEquals(layer_type('foo.sHp'), FeatureType.resource_type)
        self.assertEquals(layer_type('foo.tif'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TIF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TiF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.geotif'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.GEOTIF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.gEoTiF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.tiff'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TIFF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TiFf'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.geotiff'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.GEOTIFF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.gEoTiFf'), Coverage.resource_type)

        # basically anything else should produce a GeoNodeException
        self.assertRaises(GeoNodeException, lambda: layer_type('foo.gml'))

    def test_get_files(self):
        from geonode.maps.utils import get_files
        import shutil
        import tempfile

        # Check that a well-formed Shapefile has its components all picked up
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj", "foo.dbf"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            gotten_files = get_files(os.path.join(d, "foo.shp"),None)
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.shp", shp="foo.shp", shx="foo.shx",
                prj="foo.prj", dbf="foo.dbf"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that a Shapefile missing required components raises an exception
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp"),None))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including an SLD with a valid shapefile results in the SLD getting picked up
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj", "foo.dbf", "foo.sld"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            gotten_files = get_files(os.path.join(d, "foo.shp"), os.path.join(d, "foo.sld"))
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.shp", shp="foo.shp", shx="foo.shx",
                prj="foo.prj", dbf="foo.dbf", sld="foo.sld"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that capitalized extensions are ok
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            gotten_files = get_files(os.path.join(d, "foo.SHP"),None)
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.SHP", shp="foo.SHP", shx="foo.SHX",
                prj="foo.PRJ", dbf="foo.DBF"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that mixed capital and lowercase extensions are ok
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.SHP", "foo.shx", "foo.pRJ", "foo.DBF"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            gotten_files = get_files(os.path.join(d, "foo.SHP"),None)
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.SHP", shp="foo.SHP", shx="foo.shx",
                prj="foo.pRJ", dbf="foo.DBF"))
        finally:
            if d is not None:
                shutil.rmtree(d)

#These don't work on a Mac (foo.SHP == foo.shp)
#        # Check that including both capital and lowercase extensions raises an exception
#        d = None
#        try:
#            d = tempfile.mkdtemp()
#            for f in ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.shp", "foo.shx", "foo.prj", "foo.dbf"):
#                path = os.path.join(d, f)
#                # open and immediately close to create empty file
#                open(path, 'w').close()
#
#            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP"),None))
#            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp"),None))
#        finally:
#            if d is not None:
#                shutil.rmtree(d)
#
#        # Check that including both capital and lowercase PRJ (this is special-cased in the implementation)
#        d = None
#        try:
#            d = tempfile.mkdtemp()
#            for f in ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.prj"):
#                path = os.path.join(d, f)
#                # open and immediately close to create empty file
#                open(path, 'w').close()
#
#            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP"),None))
#            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp"),None))
#        finally:
#            if d is not None:
#                shutil.rmtree(d)
#
#        # Check that including both capital and lowercase SLD (this is special-cased in the implementation)
#        d = None
#        try:
#            d = tempfile.mkdtemp()
#            for f in ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.SLD", "foo.sld"):
#                path = os.path.join(d, f)
#                # open and immediately close to create empty file
#                open(path, 'w').close()
#
#            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP"),None))
#            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp"),None))
#        finally:
#            if d is not None:
#                shutil.rmtree(d)

    def test_get_valid_name(self):
        from geonode.maps.utils import get_valid_name
        self.assertEquals(get_valid_name("blug")[:4], "blug")
        self.assertEquals(get_valid_name("<-->")[:1], "_")
        self.assertEquals(get_valid_name("<ab>")[:4], "_ab_")
        self.assertEquals(get_valid_name("CA")[:3], "CA_")
        self.assertEquals(get_valid_name("CA")[:3], "CA_")

    def test_get_valid_layer_name(self):
        from geonode.maps.utils import get_valid_layer_name
        self.assertEquals(get_valid_layer_name("blug", False)[:4], "blug")
        self.assertEquals(get_valid_layer_name("blug", True), "blug")

        self.assertEquals(get_valid_layer_name("<ab>", False)[:4], "_ab_")
        self.assertEquals(get_valid_layer_name("<ab>", True), "<ab>")

        self.assertEquals(get_valid_layer_name("<-->", False)[:1], "_")
        self.assertEquals(get_valid_layer_name("<-->", True), "<-->")

        self.assertEquals(get_valid_layer_name("CA", False)[:3], "CA_")
        self.assertEquals(get_valid_layer_name("CA", False)[:3], "CA_")
        self.assertEquals(get_valid_layer_name("CA", True), "CA")
        self.assertEquals(get_valid_layer_name("CA", True), "CA")

        layer = Layer.objects.get(name="CA")
        self.assertEquals(get_valid_layer_name(layer, False)[:3], "CA_")
        self.assertEquals(get_valid_layer_name(layer, True), "CA")

        self.assertRaises(GeoNodeException, get_valid_layer_name, 12, False)
        self.assertRaises(GeoNodeException, get_valid_layer_name, 12, True)

    def test_cleanup(self):
        from geonode.maps.utils import cleanup
        from geoserver.catalog import FailedRequestError
        from mock import patch

        self.assertRaises(GeoNodeException, cleanup, "CA", "1234")
        cleanup("FOO", "1234")

        def blowup(self):
            raise FailedRequestError()

        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_catalog:
            mock_catalog.get_store.return_value = None
            cleanup("FOO", "1234")

        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_catalog:
            mock_catalog.get_store.side_effect = blowup

            cleanup("FOO", "1234")

        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_catalog:
            mock_catalog.get_layer.return_value = None
            cleanup("FOO", "1234")

        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_catalog:
            mock_catalog.delete.side_effect = blowup
            cleanup("FOO", "1234")

    def test_check_geonode_is_up(self):
        from contextlib import nested
        from geonode.maps.utils import check_geonode_is_up
        from mock import patch

        def blowup():
            raise Exception("BOOM")

        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_gs:
            mock_gs.get_workspaces.side_effect = blowup

            self.assertRaises(GeoNodeException, check_geonode_is_up)

        with nested(
                patch('geonode.maps.models.Layer.objects.gs_catalog'),
                patch('geonode.maps.models.Layer.objects.geonetwork')
            ) as (mock_gs, mock_gn):
                mock_gn.login.side_effect = blowup
                self.assertRaises(GeoNodeException, check_geonode_is_up)
                self.assertTrue(mock_gs.get_workspaces.called)

        with nested(
                patch('geonode.maps.models.Layer.objects.gs_catalog'),
                patch('geonode.maps.models.Layer.objects.geonetwork')
            ) as (mock_gs, mock_gn):
                # no assertion, this should just run without error
                check_geonode_is_up()


    def test_save(self):
        import shutil
        import tempfile
        from contextlib import nested
        from geonode.maps.utils import save

        # Check that including both capital and lowercase SLD (this is special-cased in the implementation) 
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj", "foo.dbf", "foo.sld", "foo.sld"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            class MockWMS(object):

                def __init__(self):
                    self.contents = { 'geonode:a_layer': 'geonode:a_layer' }

                def __getitem__(self, idx):
                    return self.contents[idx]

            with nested(
                    patch.object(geonode.maps.models, '_wms', new=MockWMS()),
                    patch('geonode.maps.models.Layer.objects.gs_catalog'),
                    patch('geonode.maps.models.Layer.objects.geonetwork')
                ) as (mock_wms, mock_gs, mock_gn):
                    # Setup
                    mock_gs.get_store.return_value.get_resources.return_value = []
                    mock_resource = mock_gs.get_resource.return_value
                    mock_resource.name = 'a_layer'
                    mock_resource.title = 'a_layer'
                    mock_resource.abstract = 'a_layer'
                    mock_resource.store.name = "a_layer"
                    mock_resource.store.resource_type = "dataStore"
                    mock_resource.store.workspace.name = "geonode"
                    mock_resource.native_bbox = ["0", "0", "0", "0"]
                    mock_resource.latlon_bbox = ["0", "0", "0", "0"]
                    mock_resource.projection = "EPSG:4326"
                    mock_gn.url_for_uuid.return_value = "http://example.com/metadata"

                    # Exercise
                    base_file = os.path.join(d, 'foo.shp')
                    owner = User.objects.get(username="admin")
                    save('a_layer', base_file, owner)

                    # Assertions
                    (md_link,) = mock_resource.metadata_links
                    md_mime, md_spec, md_url = md_link
                    self.assertEquals(md_mime, "text/xml")
                    self.assertEquals(md_spec, "TC211")
                    self.assertEquals(md_url,  "http://example.com/metadata")
        finally:
            if d is not None:
                shutil.rmtree(d)
