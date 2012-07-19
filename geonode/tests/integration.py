import os
import urllib2
from urlparse import urljoin
from urllib import urlencode
import json
from unittest import TestCase
import urllib
import urllib2

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command

from geoserver.catalog import FailedRequestError

from geonode.security.models import *
from geonode.layers.models import Layer
from geonode.layers.views import layer_set_permissions
from geonode import GeoNodeException
from geonode.layers.utils import (
    upload,
    file_upload,
    save
)

from .utils import check_layer, get_web_page

from geonode.maps.utils import *
from geonode.catalogue import get_catalogue

from geonode.gs_helpers import cascading_delete, fixup_style
import gisdata


class _Client(object):

    def __init__(self, url, user, passwd):
        self.url = url
        self.user = user
        self.passwd = passwd
        self.opener = self._init_url_opener()

    def _init_url_opener(self):
        auth_handler = urllib2.HTTPBasicAuthHandler()
        auth_handler.add_password(
            realm='GeoNode realm',
            uri='',
            user=self.user,
            passwd=self.passwd
        )

        return urllib2.build_opener(
            auth_handler,
            urllib2.HTTPCookieProcessor,
            # MultipartPostHandler.MultipartPostHandler
        )

    def parse_cookies(self, cookies):
        res = {}
        for part in cookies.split(';'):
            key, value = part.split('=')
            res[key] = value
        return res

    def get_crsf_token(self):
        """ Method that makes a request against the home page to get
        the csrf token from the request cookies
        """
        resp = self.get('')
        cookies = self.parse_cookies(resp.headers['set-cookie'])
        return cookies.get('csrftoken', None)

    def login(self):
        """ Method to login the GeoNode site"""
        params = {'csrfmiddlewaretoken': self.get_crsf_token(),
                  'username': self.user,
                  'next': '/',
                  'password': self.passwd}
        return self._make_request(
            'accounts/login/',
            data=urllib.urlencode(params)
        )

    def _make_request(self, path, data=None):
        req = urllib2.Request(
            url=self.url + path, data=data
        )
        return self.opener.open(req)

    def get(self, path):
        return self._make_request(path)


LOGIN_URL=settings.SITEURL + "accounts/login/"


class GeoNodeCoreTest(TestCase):
    """Tests geonode.security app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

class GeoNodeProxyTest(TestCase):
    """Tests geonode.proxy app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass


class NormalUserTest(TestCase):
    """
    Tests GeoNode functionality for non-administrative users
    """

    def setUp(self):
        call_command('loaddata', 'sample_admin', verbosity=0)

    def tearDown(self):
        pass

    def test_layer_upload(self):
        """ Try uploading a layer and verify that the user can administrate
        his own layer despite not being a site administrator.
        """

        from django.contrib.auth.models import User

        client = _Client(
            settings.SITEURL,
            user='norman',
            passwd='norman'
        )

        #TODO: Would be nice to ensure the name is available before
        #running the test...
        norman = User.objects.get(username="norman")
        save("san_andres_y_providencia_poi_by_norman",
             os.path.join(gisdata.VECTOR_DATA, "san_andres_y_providencia_poi.shp"),
             norman,
             overwrite=False,
             abstract="Schools which are in Lembang",
             title="Lembang Schools",
             permissions={'users': []}
        )

        client.login()
        resp = client.get('data/geonode:san_andres_y_providencia_poi_by_norman/metadata')
        self.assertEquals(resp.code, 200)


class GeoNodeMapTest(TestCase):
    """Tests geonode.maps app/module
    """

    def setUp(self):
        call_command('loaddata', 'sample_admin', verbosity=0)

    def tearDown(self):
        pass

    # geonode.maps.utils 

    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """
        layers = {}
        expected_layers = []
        not_expected_layers = []

        for filename in os.listdir(gisdata.GOOD_DATA):
            basename, extension = os.path.splitext(filename)
            if extension.lower() in ['.tif', '.shp', '.zip']:
                expected_layers.append(os.path.join(gisdata.GOOD_DATA, filename))

        for filename in os.listdir(gisdata.BAD_DATA):        
            not_expected_layers.append(
                                    os.path.join(gisdata.BAD_DATA, filename)
                                       )
        uploaded = upload(gisdata.DATA_DIR)

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
        sampletxt = os.path.join(gisdata.VECTOR_DATA,
            'points_epsg2249_no_prj.dbf')
        try:
            file_upload(sampletxt)
        except GeoNodeException, e:
            pass
        except Exception, e:
            raise
            # msg = ('Was expecting a %s, got %s instead.' %
            #        (GeoNodeException, type(e)))
            # assert e is GeoNodeException, msg


    def test_shapefile(self):
        """Test Uploading a good shapefile
        """
        thefile = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        uploaded = file_upload(thefile)
        check_layer(uploaded)

        # Clean up and completely delete the layer
        uploaded.delete()

    def test_bad_shapefile(self):
        """Verifying GeoNode complains about a shapefile without .prj
        """

        thefile = os.path.join(gisdata.BAD_DATA, 'points_epsg2249_no_prj.shp')
        try:
            uploaded = file_upload(thefile)
        except GeoNodeException, e:
            pass
        except Exception, e:
            raise
            # msg = ('Was expecting a %s, got %s instead.' %
            #        (GeoNodeException, type(e)))
            # assert e is GeoNodeException, msg


    def test_tiff(self):
        """Uploading a good .tiff
        """
        thefile = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        uploaded = file_upload(thefile)
        check_layer(uploaded)

        # Clean up and completely delete the layer
        uploaded.delete()
    
    def test_repeated_upload(self):
        """Upload the same file more than once
        """
        thefile = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
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
        self.assertEquals(int(results["total"]), Layer.objects.count())
        
        # Test n0ch@nc3 Search (returns no results)
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "n0ch@nc3", 0, 10)
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), 0)
        
        # Test Keyword Search (various search terms)
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "NIC", 0, 10)
        results = json.loads(get_web_page(test_url))
        #self.assertEquals(int(results["total"]), 3)

        # This Section should be greatly expanded upon after uploading several
        # Test layers. Issues found with GeoNetwork search should be 'documented'
        # here with a Test Case

        # Test BBOX Search (various bbox)
        
        # - Test with an empty query string and Global BBOX and validate that total is correct
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % (settings.SITEURL, "", 0, 10, "-180,-90,180,90")
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), Layer.objects.count())

        # - Test with a specific query string and a bbox that is disjoint from its results
        #test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % (settings.SITEURL, "NIC", 0, 10, "0,-90,180,90")
        #results = json.loads(get_web_page(test_url))
        #self.assertEquals(int(results["total"]), 0) 

        # - Many more Tests required

        # Test start/limit params (do in unit test?)

        # Test complex/compound Search

        # Test Permissions applied to search from ACLs

        # TODO Write a method to accept a perm_spec and query params
        # and test that query results are returned respecting the
        # perm_spec

        # - Test with Anonymous User
        perm_spec = {"anonymous":"_none","authenticated":"_none","users":[["admin","layer_readwrite"]]}
        for layer in Layer.objects.all():
            layer_set_permissions(layer, perm_spec)

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
        results = json.loads(get_web_page(test_url, username="admin", password="admin", login_url=LOGIN_URL))
        
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

    def test_layer_delete_from_geoserver(self):
        """Verify that layer is correctly deleted from GeoServer
        """
        # Layer.delete_from_geoserver() uses cascading_delete()
        # Should we explicitly test that the styles and store are
        # deleted as well as the resource itself?
        # There is already an explicit test for cascading delete

        gs_cat = Layer.objects.gs_catalog

        # Test Uploading then Deleting a Shapefile from GeoServer
        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=shp_store))

        shp_layer.delete()

        # Test Uploading then Deleting a TIFF file from GeoServer
        tif_file = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        tif_store = gs_cat.get_store(tif_layer.name)
        tif_layer.delete_from_geoserver()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=tif_store))

        tif_layer.delete()

    def test_layer_delete_from_catalogue(self):
        """Verify that layer is correctly deleted from CSW catalogue
        """

        # Test Uploading then Deleting a Shapefile from GeoNetwork
        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)
        catalogue = get_catalogue()
        catalogue.remove_record(shp_layer.uuid)
        shp_layer_info = catalogue.get_record(shp_layer.uuid)
        assert shp_layer_info == None

        # Clean up and completely delete the layer
        shp_layer.delete()

        # Test Uploading then Deleting a TIFF file from GeoNetwork
        tif_file = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        catalogue.remove_record(tif_layer.uuid)
        tif_layer_info = catalogue.get_record(tif_layer.uuid)
        assert tif_layer_info == None

        # Clean up and completely delete the layer
        tif_layer.delete()

    def test_delete_layer(self):
        """Verify that the 'delete_layer' pre_delete hook is functioning
        """

        gs_cat = Layer.objects.gs_catalog

        # Upload a Shapefile Layer
        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)
        shp_layer_id = shp_layer.pk
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_store_name = shp_store.name

        id = shp_layer.pk
        name = shp_layer.name
        uuid = shp_layer.uuid

        # Delete it with the Layer.delete() method
        shp_layer.delete()

        # Verify that it no longer exists in GeoServer
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(name, store=shp_store))
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_store(shp_store_name))

        catalogue = get_catalogue()

        # Verify that it no longer exists in GeoNetwork
        shp_layer_gn_info = catalogue.get_record(uuid)
        assert shp_layer_gn_info == None

        # Check that it was also deleted from GeoNodes DB
        self.assertRaises(ObjectDoesNotExist,
            lambda: Layer.objects.get(pk=shp_layer_id))

    # geonode.maps.gs_helpers

    def test_cascading_delete(self):
        """Verify that the gs_helpers.cascading_delete() method is working properly
        """
        gs_cat = Layer.objects.gs_catalog

        # Upload a Shapefile
        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
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
            s = gs_cat.get_style(style.name)
            assert s == None
        
        # Verify that the resource was deleted
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_resource(resource_name, store=store))

        # Verify that the store was deleted 
        self.assertRaises(FailedRequestError, lambda: gs_cat.get_store(store_name))

        # Clean up by deleting the layer from GeoNode's DB and GeoNetwork
        shp_layer.delete()


    def test_keywords_upload(self):
        """Check that keywords can be passed to file_upload
        """
        thefile = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        uploaded = file_upload(thefile, keywords=['foo', 'bar'], overwrite=True)
        keywords = uploaded.keyword_list()
        msg='No keywords found in layer %s' % uploaded.name
        assert len(keywords)>0, msg
        assert 'foo' in uploaded.keyword_list(), 'Could not find "foo" in %s' % keywords
        assert 'bar' in uploaded.keyword_list(), 'Could not find "bar" in %s' % keywords

    def test_empty_bbox(self):
        """Regression-test for failures caused by zero-width bounding boxes"""
        thefile = os.path.join(gisdata.VECTOR_DATA, 'single_point.shp')
        uploaded = file_upload(thefile, overwrite=True)
        client = _Client(
            settings.SITEURL,
            user='norman',
            passwd='norman'
        )
        client.login()
        resp = client.get('/' + uploaded.get_absolute_url())
        self.assertEquals(resp.code, 200)
