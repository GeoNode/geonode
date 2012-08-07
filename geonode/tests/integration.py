#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

import os
import urllib2
from urlparse import urljoin
from urllib import urlencode
import json
import urllib
import urllib2
import time

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.test import Client
from django.test import LiveServerTestCase as TestCase
from django.core.urlresolvers import reverse

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
from geonode.utils import http_client
from .utils import check_layer, get_web_page

from geonode.maps.utils import *

from geonode.gs_helpers import cascading_delete, fixup_style
import gisdata

import zipfile

LOGIN_URL= "/accounts/login/"


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

        client = Client(
            user='norman',
            passwd='norman'
        )

        #TODO: Would be nice to ensure the name is available before
        #running the test...
        norman = User.objects.get(username="norman")
        saved_layer = save("san_andres_y_providencia_poi_by_norman",
             os.path.join(gisdata.VECTOR_DATA, "san_andres_y_providencia_poi.shp"),
             norman,
             overwrite=False,
             abstract="Schools which are in Lembang",
             title="Lembang Schools",
             permissions={'users': []}
        )

        resp = client.get('layer_metadata', args=[saved_layer.typename])
        self.assertEquals(resp.status_code, 200)


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
        test_url = "/data/search/api/?q=%s&start=%d&limit=%d"  % ("", 0, 10)
        client = Client()
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(int(results["total"]), Layer.objects.count())
        
        # Test n0ch@nc3 Search (returns no results)
        test_url = "/data/search/api/?q=%s&start=%d&limit=%d"  % ("n0ch@nc3", 0, 10)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(int(results["total"]), 0)
        
        # Test Keyword Search (various search terms)
        test_url = "/data/search/api/?q=%s&start=%d&limit=%d"  % ("NIC", 0, 10)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        #self.assertEquals(int(results["total"]), 3)

        # This Section should be greatly expanded upon after uploading several
        # Test layers. Issues found with GeoNetwork search should be 'documented'
        # here with a Test Case

        # Test BBOX Search (various bbox)
        
        # - Test with an empty query string and Global BBOX and validate that total is correct
        test_url = "/data/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % ("", 0, 10, "-180,-90,180,90")
        resp = client.get(test_url)
        results = json.loads(resp.content)
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

        test_url = "/data/search/api/?q=%s&start=%d&limit=%d"  % ("", 0, 10)
        resp = client.get(test_url)
        results = json.loads(resp.content)

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
        client = Client(username='admin', password='admin')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        
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
        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)
 
        # Test with a valid UUID
        uuid=Layer.objects.all()[0].uuid

        test_url = "/data/search/detail/?uuid=%s"  % uuid
        client = Client()
        resp = client.get(test_url)
        results = resp.content
        
        # Test with an invalid UUID (should return 404, but currently does not)
        uuid="xyz"
        test_url = "/data/search/detail/?uuid=%s" % uuid
        # Should use assertRaisesRegexp here, but new in 2.7
        resp = client.get(test_url)
        msg = 'Result for uuid: "%s" should have returned a 404' % resp.status_code
        assert resp.status_code == 404, msg

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

        # Check that it was also deleted from GeoNodes DB
        self.assertRaises(ObjectDoesNotExist,
            lambda: Layer.objects.get(pk=shp_layer_id))

        # If catalogue is installed, then check that it is deleted from there too.
        if 'geonode.catalogue' in settings.INSTALLED_APPS:
            from geonode.catalogue import get_catalogue
            catalogue = get_catalogue()

            # Verify that it no longer exists in GeoNetwork
            shp_layer_gn_info = catalogue.get_record(uuid)
            assert shp_layer_gn_info == None


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
        client = Client(
            user='norman',
            passwd='norman'
        )
        client.login()
        resp = client.get(uploaded.get_absolute_url())
        self.assertEquals(resp.status_code, 200)

    def test_layer_replace(self):
        """Test layer replace functionality
        """
        # Upload Some Data to work with
               
        uploaded_vector = upload(gisdata.VECTOR_DATA)
        upload_list_vector = []
        for item in uploaded_vector:
            upload_list_vector.append('geonode:' + item['name'])

        uploaded_raster = upload(gisdata.RASTER_DATA)
        upload_list_raster = []
        for item in uploaded_raster:
            upload_list_raster.append('geonode:' + item['name'])
        
        #test a valid user with layer replace permission         
        from django.test.client import Client
        c = Client()
        c.login(username='admin', password='admin')

        #test the program can determine the original layer in raster type 
        raster_layer = upload_list_raster.pop()
        raster_url = '/data/%s/replace' % (raster_layer)
        response = c.get(raster_url)
        self.assertEquals(response.status_code, 200)   
        self.assertEquals(response.context['is_featuretype'], False)
        
        #test the program can determine the original layer in vector type
        original_vector_layer_name = upload_list_vector.pop()
        original_vector_layer = Layer.objects.get(typename = original_vector_layer_name)
        vector_url = '/data/%s/replace' % (original_vector_layer_name)
        response = c.get(vector_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['is_featuretype'], True)
   
        #test replace a vector with a raster 
        layer_typename = raster_layer 
        layer_path = str('%s/%s' % (gisdata.RASTER_DATA, layer_typename.replace('geonode:', '')))
        layer_base = open(layer_path + '.tif')
        response = c.post(vector_url, {'base_file': layer_base})
        # TODO: This should really return a 400 series error with the json dict
        self.assertEquals(response.status_code, 200)
        response_dict = json.loads(response.content)
        self.assertEquals(response_dict['success'], False)

        #test replace a vector with a different vector
        new_vector_layer_name = upload_list_vector.pop()
        new_vector_layer = Layer.objects.get(typename = new_vector_layer_name)
        layer_path = str('%s/%s' % (gisdata.VECTOR_DATA, new_vector_layer_name.replace('geonode:', '')))
        layer_base = open(layer_path + '.shp')
        layer_dbf = open(layer_path + '.dbf')
        layer_shx = open(layer_path + '.shx')
        try:
            layer_prj = open(layer_path + '.prj')
        except:
            layer_prj = None

        response = c.post(vector_url, {'base_file': layer_base,
                                'dbf_file': layer_dbf,
                                'shx_file': layer_shx,
                                'prj_file': layer_prj
                                })
        self.assertEquals(response.status_code, 200)
        response_dict = json.loads(response.content) 
        self.assertEquals(response_dict['success'], True)

        #Test the replaced layer is indeed different from the original layer
        self.assertNotEqual(original_vector_layer.typename, new_vector_layer.typename)
        self.assertNotEqual(original_vector_layer.bbox_string, new_vector_layer.bbox_string)

        #test an invalid user without layer replace permission
        c.logout()   
        c.login(username='norman', password='norman')
          
        response = c.post(vector_url, {'base_file': layer_base,
                                'dbf_file': layer_dbf,
                                'shx_file': layer_shx,
                                'prj_file': layer_prj
                                })
        self.assertEquals(response.status_code, 403)
