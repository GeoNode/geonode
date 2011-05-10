import os, sys
import urllib2
import contextlib 
import json

from unittest import TestCase

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import AnonymousUser

from geoserver.catalog import FailedRequestError

from geonode.core.models import *
from geonode.maps.models import Layer
from geonode.maps.views import set_layer_permissions

from geonode.maps.utils import upload, file_upload, GeoNodeException

from tests.utils import check_layer, get_web_page

TEST_DATA = os.path.join(settings.PROJECT_ROOT, 'geonode_test_data')

LOGIN_URL=settings.SITEURL + "accounts/login/"

class GeoNodeCoreTest(TestCase):
    """Tests geonode.core app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        assert(True)
    
class GeoNodeProxyTest(TestCase):
    """Tests geonode.proxy app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        assert(True)

class GeoNodeMapTest(TestCase):
    """Tests geonode.maps app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
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
            if extension.lower() in ['.tif', '.shp', '.zip']:
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
        #assert len(layers) == len(expected_layers), msg

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
            if page.find('rest/layers/%s.html' % layer_name) > 0:
                found = True
            if not found:
                msg = ('Upload could not be verified, the layer %s is not '
                   'in geoserver %s, but GeoNode did not raise any errors, '
                   'this should never happen.' %
                   (layer_name, settings.GEOSERVER_BASE_URL))
                raise GeoNodeException(msg)

        server_url = settings.GEOSERVER_BASE_URL + 'ows?'
        # Verify that the GeoServer GetCapabilities record is accesible:
        #metadata = get_layers_metadata(server_url, '1.0.0')
        #msg = ('The metadata list should not be empty in server %s'
        #        % server_url)
        #assert len(metadata) > 0, msg
        # Check the keywords are recognized too

        # Clean up and completely delete the layers
        for layer in expected_layers:
            layer_name = layers[layer]
            Layer.objects.get(name=layer_name).delete()

    def test_extension_not_implemented(self):
        """Verify a GeoNodeException is returned for not compatible extensions
        """
        sampletxt = os.path.join(TEST_DATA,
            'lembang_schools_percentage_loss.dbf')
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

        # Clean up and completely delete the layer
        uploaded.delete()

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
        thefile = os.path.join(TEST_DATA, 'test_grid.tif')
        uploaded = file_upload(thefile)
        check_layer(uploaded)

        # Clean up and completely delete the layer
        uploaded.delete()
    
    def test_repeated_upload(self):
        """Upload the same file more than once
        """
        thefile = os.path.join(TEST_DATA, 'test_grid.tif')
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

        # Clean up and completely delete the layers

        # uploaded1 is overwritten by uploaded2 ... no need to delete it
        uploaded2.delete()
        uploaded3.delete()
    
    # geonode.maps.views

    # Search Tests
    
    def test_metadata_search(self):
        
        # Test Empty Search [returns all results, should match len(Layer.objects.all())+5]
        # +5 is for the 5 'default' records in GeoNetwork
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "", 0, 10)
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), len(Layer.objects.all())+5)
        
        # Test n0ch@nc3 Search (returns no results)
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "n0ch@nc3", 0, 10)
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), 0)
        
        # Test Keyword Search (various search terms)
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "NIC", 0, 10)
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), 3)

        # This Section should be greatly expanded upon after uploading several
        # Test layers. Issues found with GeoNetwork search should be 'documented'
        # here with a Test Case

        # Test BBOX Search (various bbox)
        
        # - Test with an empty query string and Global BBOX and validate that total is correct
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % (settings.SITEURL, "", 0, 10, "-180,-90,180,90")
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), len(Layer.objects.all())+5)

        # - Test with a specific query string and a bbox that is disjoint from its results
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % (settings.SITEURL, "NIC", 0, 10, "0,-90,180,90")
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), 0) 

        # - Many more Tests required

        # Test start/limit params (do in unit test?)

        # Test complex/compound Search

        # Test Permissions applied to search from ACLs

        # TODO Write a method to accept a perm_spec and query params and test that query results are returned respecting the perm_spec

        # - Test with Anonymous User
        perm_spec = {"anonymous":"_none","authenticated":"_none","users":[["admin","layer_readwrite"]]}
        for layer in Layer.objects.all():
            set_layer_permissions(layer, perm_spec)

        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL,"", 0, 10)

        results = json.loads(get_web_page(test_url))
        
        for layer in results["rows"]:
            if layer["_local"] == False:
                # Ignore non-local layers
                pass
            else:
                self.assertEquals(layer["_permissions"]["view"], False)
                self.assertEquals(layer["_permissions"]["change"], False)
                self.assertEquals(layer["_permissions"]["delete"], False)
                self.assertEquals(layer["_permissions"]["change_permissions"], False)

        # - Test with Authenticated User
        results = json.loads(get_web_page(test_url, username="admin", password="@dm1n", login_url=LOGIN_URL))
        
        for layer in results["rows"]:
            if layer["_local"] == False:
                # Ignore non-local layers
                pass
            else:
                self.assertEquals(layer["_permissions"]["view"], True)
                self.assertEquals(layer["_permissions"]["change"], True)
                self.assertEquals(layer["_permissions"]["delete"], True)
                self.assertEquals(layer["_permissions"]["change_permissions"], True)
        
        # Test that MAX_SEARCH_BATCH_SIZE is respected (in unit test?)
    
    def test_search_result_detail(self):
        # Test with a valid UUID
        uuid=Layer.objects.all()[0].uuid
        test_url = "%sdata/search/detail/?uuid=%s"  % (settings.SITEURL, uuid)
        results = get_web_page(test_url)
        
        # Test with an invalid UUID (should return 404, but currently does not)
        uuid="xyz"
        test_url = "%sdata/search/detail/?uuid=%s"  % (settings.SITEURL, uuid)
        # Should use assertRaisesRegexp here, but new in 2.7
        self.assertRaises(urllib2.HTTPError,
            lambda: get_web_page(test_url)) 

    def test_maps_search(self):
        pass

    # geonode.maps.models

    # geonode.maps.gs_helpers
