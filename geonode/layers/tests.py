# -*- coding: utf-8 -*-
import os
import base64
import shutil
import tempfile

from contextlib import nested
from mock import Mock, patch

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, AnonymousUser
from django.utils import simplejson as json
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template import Context
from django.template.loader import get_template
from django.forms import ValidationError

import geonode.maps.models
import geonode.maps.views

from geonode import GeoNodeException

from geonode.layers.models import Layer
from geonode.layers.forms import JSONField, LayerUploadForm
from geonode.layers.utils import save, layer_type, get_files, get_valid_name, \
                                get_valid_layer_name, cleanup
from geonode.people.utils import get_valid_user

from geoserver.catalog import FailedRequestError
from geoserver.resource import FeatureType, Coverage


_gs_resource = Mock()
_gs_resource.native_bbox = [1, 2, 3, 4]


class LayersTest(TestCase):
    """Tests geonode.layers app/module
    """

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
        self.assertEqual(layer.get_gen_level(geonode.security.models.ANONYMOUS_USERS), layer.LEVEL_READ)
        self.assertEqual(layer.get_gen_level(geonode.security.models.AUTHENTICATED_USERS), layer.LEVEL_READ)

        # Test that the previous Permissions were set to LEVEL_NONE
        for username in current_perms['users'].keys():
            user = User.objects.get(username=username)
            self.assertEqual(layer.get_user_level(user), layer.LEVEL_NONE)

        # Test that the owner was assigned LEVEL_ADMIN
        if layer.owner:
            self.assertEqual(layer.owner, layer.LEVEL_ADMIN)    

    def test_set_layer_permissions(self):
        """Verify that the set_layer_permissions view is behaving as expected
        """
        
        # Get a layer to work with
        layer = Layer.objects.all()[0]

        # FIXME Test a comprehensive set of permisssions specifications 

        # Set the Permissions
        geonode.maps.views.set_layer_permissions(layer, self.perm_spec)

        # Test that the Permissions for ANONYMOUS_USERS and AUTHENTICATED_USERS were set correctly        
        self.assertEqual(layer.get_gen_level(geonode.security.models.ANONYMOUS_USERS), layer.LEVEL_NONE) 
        self.assertEqual(layer.get_gen_level(geonode.security.models.AUTHENTICATED_USERS), layer.LEVEL_NONE)

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the layers owner) were removed
        users = [n[0] for n in self.perm_spec['users']]
        levels = layer.get_user_levels().exclude(user__username__in = users + [layer.owner])
        self.assertEqual(len(levels), 0)
       
        # Test that the User permissions specified in the perm_spec were applied properly
        for username, level in self.perm_spec['users']:
            user = geonode.maps.models.User.objects.get(username=username)
            self.assertEqual(layer.get_user_level(user), level)

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
        c.login(username='admin', password='admin')
       
        # Basic check that the returned content is at least valid json
        response = c.get("/data/acls")
        response_json = json.loads(response.content)

        # TODO Lots more to do here once jj0hns0n understands the ACL system better

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

    # Data Tests

    def test_data(self):
        '''/data/ -> Test accessing the data page'''
        c = Client()
        response = c.get('/data/')
        self.failUnlessEqual(response.status_code, 200)

    def test_describe_data_2(self):
        '''/data/base:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(4, User.objects.all().count())
        c = Client()
        response = c.get('/data/base:CA/metadata')
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        c.login(username='bobby', password='bob')
        # ... all should be good
        response = c.get('/data/base:CA/metadata')
        self.failUnlessEqual(response.status_code, 200)
    
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

    def test_search(self):
        '''/data/search/ -> Test accessing the data search page'''
        c = Client()
        response = c.get('/data/search/')
        self.failUnlessEqual(response.status_code, 200)

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

            c.get("/data/search/api?q=foo&start=5&limit=10")

            call_args = geonode.maps.views._metadata_search.call_args
            self.assertEqual(call_args[0][0], "foo")
            self.assertEqual(call_args[0][1], 5)
            self.assertEqual(call_args[0][2], 10)

    def test_search_api(self):
        '''/data/search/api -> Test accessing the data search api JSON'''
        c = Client()
        response = c.get('/data/search/api')
        self.failUnlessEqual(response.status_code, 200)

    def test_search_detail(self):
        '''
        /data/search/detail -> Test accessing the data search detail for a layer
        Disabled due to reliance on consistent UUIDs across loads.
        '''
        layer = Layer.objects.all()[0]

        # save to geonetwork so we know the uuid is consistent between
        # django db and geonetwork
        layer.save_to_geonetwork()

        c = Client()
        response = c.get('/data/search/detail', {'uuid':layer.uuid})
        self.failUnlessEqual(response.status_code, 200)

    def test_search_template(self):

        layer = Layer.objects.all()[0]
        tpl = get_template("csw/transaction_insert.xml")
        ctx = Context({
            'layer': layer,
        })
        md_doc = tpl.render(ctx)
        self.assert_("None" not in md_doc, "None in " + md_doc)


    def test_describe_data(self):
        '''/data/base:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(4, User.objects.all().count())
        c = Client()
        response = c.get('/data/base:CA/metadata')
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        c.login(username='bobby', password='bob')
        # ... all should be good
        response = c.get('/data/base:CA/metadata')
        self.failUnlessEqual(response.status_code, 200)

    def test_layer_save(self):
        lyr = Layer.objects.get(pk=1)
        lyr.keywords.add(*["saving", "keywords"])
        lyr.save()
        self.assertEqual(lyr.keyword_list(), ["keywords", "saving"])
        self.assertEqual(lyr.resource.keywords, ["keywords", "saving"])
        self.assertEqual(_gs_resource.keywords, ["keywords", "saving"])

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

        tempdir = form.write_files()[0]
        self.assertEquals(set(os.listdir(tempdir)),
            set(['foo.shp', 'foo.shx', 'foo.dbf', 'foo.prj']))
    
    def test_save(self):
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
    
    def test_layer_type(self):
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

        # Check that a well-formed Shapefile has its components all picked up
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj", "foo.dbf"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            gotten_files = get_files(os.path.join(d, "foo.shp"))
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

            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
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

            gotten_files = get_files(os.path.join(d, "foo.shp"))
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

            gotten_files = get_files(os.path.join(d, "foo.SHP"))
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

            gotten_files = get_files(os.path.join(d, "foo.SHP"))
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.SHP", shp="foo.SHP", shx="foo.shx",
                prj="foo.pRJ", dbf="foo.DBF"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase extensions raises an exception
        d = None
        try:
            d = tempfile.mkdtemp()
            files = ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.shp", "foo.shx", "foo.prj", "foo.dbf")
            for f in files:
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))

        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase PRJ (this is special-cased in the implementation) 
        d = None
        try:
            d = tempfile.mkdtemp()
            files = ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.prj")
            for f in files:
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase SLD (this is special-cased in the implementation) 
        d = None
        try:
            d = tempfile.mkdtemp()
            files = ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.SLD", "foo.sld")
            for f in files:
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()  

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d)

    def test_get_valid_name(self):
        self.assertEquals(get_valid_name("blug"), "blug")
        self.assertEquals(get_valid_name("<-->"), "_")
        self.assertEquals(get_valid_name("<ab>"), "_ab_")
        self.assertEquals(get_valid_name("CA"), "CA_1")
        self.assertEquals(get_valid_name("CA"), "CA_1")

    def test_get_valid_layer_name(self):
        self.assertEquals(get_valid_layer_name("blug", False), "blug")
        self.assertEquals(get_valid_layer_name("blug", True), "blug")

        self.assertEquals(get_valid_layer_name("<ab>", False), "_ab_")
        self.assertEquals(get_valid_layer_name("<ab>", True), "<ab>")

        self.assertEquals(get_valid_layer_name("<-->", False), "_")
        self.assertEquals(get_valid_layer_name("<-->", True), "<-->")

        self.assertEquals(get_valid_layer_name("CA", False), "CA_1")
        self.assertEquals(get_valid_layer_name("CA", False), "CA_1")
        self.assertEquals(get_valid_layer_name("CA", True), "CA")
        self.assertEquals(get_valid_layer_name("CA", True), "CA")

        layer = Layer.objects.get(name="CA")
        self.assertEquals(get_valid_layer_name(layer, False), "CA_1")
        self.assertEquals(get_valid_layer_name(layer, True), "CA")

        self.assertRaises(GeoNodeException, get_valid_layer_name, 12, False)
        self.assertRaises(GeoNodeException, get_valid_layer_name, 12, True)

    def test_cleanup(self):
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


    def testJSONField(self):
        field = JSONField()
        # a valid JSON document should pass
        field.clean('{ "users": [] }')

        # text which is not JSON should fail
        self.assertRaises(ValidationError, lambda: field.clean('<users></users>'))
