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
import datetime
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

from geonode.geoserver.helpers import cascading_delete, fixup_style

from geonode.security.enumerations import AUTHENTICATED_USERS, ANONYMOUS_USERS

import gisdata

import zipfile

LOGIN_URL= "/accounts/login/"

import logging
logging.getLogger("south").setLevel(logging.INFO)

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
        call_command('loaddata', 'people_data', verbosity=0)

    def tearDown(self):
        pass

    def test_layer_upload(self):
        """ Try uploading a layer and verify that the user can administrate
        his own layer despite not being a site administrator.
        """

        from django.contrib.auth.models import User

        client = Client()
        client.login(username='norman', password='norman')

        #TODO: Would be nice to ensure the name is available before
        #running the test...
        norman = User.objects.get(username="norman")
        saved_layer = save("san_andres_y_providencia_poi_by_norman",
             os.path.join(gisdata.VECTOR_DATA, "san_andres_y_providencia_poi.shp"),
             norman,
             overwrite=True,
        )

        url = reverse('layer_metadata', args=[saved_layer.typename])
        resp = client.get(url)
        self.assertEquals(resp.status_code, 200)


class GeoNodeMapTest(TestCase):
    """Tests geonode.maps app/module
    """

    def setUp(self):
        call_command('loaddata', 'people_data', verbosity=0)

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
        uploaded = upload(gisdata.DATA_DIR, console=None)

        for item in uploaded:
            errors = 'error' in item
            if errors:
                # should this file have been uploaded?
                if item['file'] in not_expected_layers:
                    continue
                else:
                    msg = ('Could not upload file "%s", '
                           'and it is not in %s' % (
                           item['file'], not_expected_layers))
                    assert errors == True, msg
            else:
                msg = ('Upload should have returned either "name" or '
                      '"errors" for file %s.' % item['file'])
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

    def test_layer_upload_metadata(self):
        """Test uploading a layer with XML metadata"""

        thelayer = os.path.join(gisdata.PROJECT_ROOT,
                   'both', 'good', 'sangis.org', 'Airport', 'Air_Runways.shp')

        self.assertTrue('%s.xml' % thelayer,
            'Expected layer XML metadata to exist')

        uploaded = file_upload(thelayer, overwrite=True)

        self.assertEqual(uploaded.title, 'Air_Runways',
            'Expected specific title from uploaded layer XML metadata')

        self.assertEqual(uploaded.abstract, 'Airport Runways',
            'Expected specific abstract from uploaded layer XML metadata')

        self.assertEqual(uploaded.purpose,
            'To show the location of Public Airports '\
            'and Runways within San Diego County',
            'Expected specific purpose from uploaded layer XML metadata')

        self.assertEqual(uploaded.supplemental_information,
            'No information provided',
            'Expected specific supplemental information '\
            'from uploaded layer XML metadata')

        self.assertEqual(len(uploaded.keyword_list()), 5,
            'Expected specific number of keywords from uploaded layer XML metadata')

        self.assertTrue('Landing Strips' in uploaded.keyword_list(),
            'Expected specific keyword from uploaded layer XML metadata')

        self.assertEqual(uploaded.constraints_other, 'None',
            'Expected specific constraint from uploaded layer XML metadata')

        self.assertEqual(uploaded.date, datetime.datetime(2010, 8, 3, 0, 0),
            'Expected specific date from uploaded layer XML metadata')

        # Clean up and completely delete the layer
        uploaded.delete()

    def test_shapefile(self):
        """Test Uploading a good shapefile
        """
        thefile = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        uploaded = file_upload(thefile, overwrite=True)
        check_layer(uploaded)

        # Clean up and completely delete the layer
        uploaded.delete()

    def test_bad_shapefile(self):
        """Verifying GeoNode complains about a shapefile without .prj
        """

        thefile = os.path.join(gisdata.BAD_DATA, 'points_epsg2249_no_prj.shp')
        try:
            uploaded = file_upload(thefile, overwrite=True)
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
        uploaded = file_upload(thefile, overwrite=True)
        check_layer(uploaded)

        # Clean up and completely delete the layer
        uploaded.delete()

    def test_repeated_upload(self):
        """Upload the same file more than once
        """
        thefile = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        uploaded1 = file_upload(thefile, overwrite=True)
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


    def test_layer_delete_from_geoserver(self):
        """Verify that layer is correctly deleted from GeoServer
        """
        # Layer.delete() calls the pre_delete hook which uses cascading_delete()
        # Should we explicitly test that the styles and store are
        # deleted as well as the resource itself?
        # There is already an explicit test for cascading delete

        gs_cat = Layer.objects.gs_catalog

        # Test Uploading then Deleting a Shapefile from GeoServer
        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file, overwrite=True)
        shp_store = gs_cat.get_store(shp_layer.name)
        shp_layer.delete()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=shp_store))

        # Test Uploading then Deleting a TIFF file from GeoServer
        tif_file = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        tif_store = gs_cat.get_store(tif_layer.name)
        tif_layer.delete()
        self.assertRaises(FailedRequestError,
            lambda: gs_cat.get_resource(shp_layer.name, store=tif_store))

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

    # geonode.geoserver.helpers
        # If catalogue is installed, then check that it is deleted from there too.
        if 'geonode.catalogue' in settings.INSTALLED_APPS:
            from geonode.catalogue import get_catalogue
            catalogue = get_catalogue()

            # Verify that it no longer exists in GeoNetwork
            shp_layer_gn_info = catalogue.get_record(uuid)
            assert shp_layer_gn_info == None


    def test_cascading_delete(self):
        """Verify that the helpers.cascading_delete() method is working properly
        """
        gs_cat = Layer.objects.gs_catalog

        # Upload a Shapefile
        shp_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)

        # Save the names of the Resource/Store/Styles
        resource_name = shp_layer.name
        ws = gs_cat.get_workspace(shp_layer.workspace)
        store = gs_cat.get_store(shp_layer.store, ws)
        store_name = store.name
        layer = gs_cat.get_layer(resource_name)
        styles = layer.styles + [layer.default_style]

        # Delete the Layer using cascading_delete()
        cascading_delete(gs_cat, shp_layer.typename)

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
        client = Client()
        client.login(username='norman', password='norman')
        resp = client.get(uploaded.get_absolute_url())
        self.assertEquals(resp.status_code, 200)

    def test_layer_replace(self):
        """Test layer replace functionality
        """
        vector_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_administrative.shp')
        vector_layer = file_upload(vector_file, overwrite=True)

        raster_file = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        raster_layer = file_upload(raster_file, overwrite=True)

        c = Client()
        c.login(username='admin', password='admin')

        #test the program can determine the original layer in raster type
        raster_replace_url = reverse('layer_replace', args=[raster_layer.typename])
        response = c.get(raster_replace_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['is_featuretype'], False)

        #test the program can determine the original layer in vector type
        vector_replace_url = reverse('layer_replace', args=[vector_layer.typename])
        response = c.get(vector_replace_url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.context['is_featuretype'], True)

        #test replace a vector with a raster
        response = c.post(vector_replace_url, {'base_file': open(raster_file) })
        # TODO: This should really return a 400 series error with the json dict
        self.assertEquals(response.status_code, 200)
        response_dict = json.loads(response.content)
        self.assertEquals(response_dict['success'], False)

        #test replace a vector with a different vector
        new_vector_file = os.path.join(gisdata.VECTOR_DATA, 'san_andres_y_providencia_poi.shp')
        layer_path, __ = os.path.splitext(new_vector_file)
        layer_base = open(layer_path + '.shp')
        layer_dbf = open(layer_path + '.dbf')
        layer_shx = open(layer_path + '.shx')
        layer_prj = open(layer_path + '.prj')

        response = c.post(vector_replace_url, {'base_file': layer_base,
                                'dbf_file': layer_dbf,
                                'shx_file': layer_shx,
                                'prj_file': layer_prj
                                })
        self.assertEquals(response.status_code, 200)
        response_dict = json.loads(response.content)
        self.assertEquals(response_dict['success'], True)

        # Get a Layer object for the newly created layer.
        new_vector_layer = Layer.objects.get(pk=vector_layer.pk)
        #FIXME(Ariel): Check the typename does not change.

        #Test the replaced layer is indeed different from the original layer
        self.assertNotEqual(vector_layer.bbox_x0, new_vector_layer.bbox_x0)
        self.assertNotEqual(vector_layer.bbox_x1, new_vector_layer.bbox_x1)
        self.assertNotEqual(vector_layer.bbox_y0, new_vector_layer.bbox_y0)
        self.assertNotEqual(vector_layer.bbox_y1, new_vector_layer.bbox_y1)

        #test an invalid user without layer replace permission
        c.logout()
        c.login(username='norman', password='norman')

        response = c.post(vector_replace_url, {'base_file': layer_base,
                                'dbf_file': layer_dbf,
                                'shx_file': layer_shx,
                                'prj_file': layer_prj
                                })
        self.assertEquals(response.status_code, 302)

class GeoNodeMapPrintTest(TestCase):
    """Tests geonode.maps print
    """

    def setUp(self):
        call_command('loaddata', 'people_data', verbosity=0)

    def tearDown(self):
        pass


    def testPrintProxy(self):
        """ Test the PrintProxyMiddleware if activated.
            It should respect the permissions on private layers.
        """
        
        if 'geonode.middleware.PrintProxyMiddleware' in settings.MIDDLEWARE_CLASSES:
            # STEP 1: Import a layer
            from django.contrib.auth.models import User
            from geonode.maps.models import Map

            client = Client()
            client.login(username='norman', password='norman')

            #TODO: Would be nice to ensure the name is available before
            #running the test...
            norman = User.objects.get(username="norman")
            saved_layer = save("san_andres_y_providencia_poi_by_norman",
                 os.path.join(gisdata.VECTOR_DATA, "san_andres_y_providencia_poi.shp"),
                 norman,
                 overwrite=True,
            )
            # Set the layer private
            saved_layer.set_gen_level(ANONYMOUS_USERS, saved_layer.LEVEL_NONE)

            url = reverse('layer_metadata', args=[saved_layer.typename])

            # check is accessible while logged in
            resp = client.get(url)
            self.assertEquals(resp.status_code, 200)

            # check is inaccessible when not logged in
            client.logout()
            resp = client.get(url)
            self.assertEquals(resp.status_code, 302)

            # STEP 2: Create a Map with that layer

            map_obj = Map(owner=norman, zoom=0,
                      center_x=0, center_y=0)
            map_obj.create_from_layer_list(norman, [saved_layer], 'title','')
            map_obj.set_default_permissions()

            # STEP 3: Print the map

            print_url = settings.GEOSERVER_BASE_URL + 'pdf/create.json'

            post_payload = {
                'dpi': 75,
                'layers': [
                    {
                        'baseURL': settings.GEOSERVER_BASE_URL + 'wms?SERVICE=WMS&',
                        'format': "image/png",
                        'customParams': {
                            'TILED': True,
                            'TRANSPARENT': True
                        },
                        'layers': [saved_layer.typename],
                        'opacity': 1,
                        'singleTile': False,
                        'type': 'WMS'
                    }
                ],
                'layout': 'A4 portrait',
                'mapTitle': 'test',
                'outputFilename': 'print',
                'srs': 'EPSG:900913',
                'units': 'm'
            }

            client.post(print_url, post_payload)

            # Test the layer is still inaccessible as non authenticated
            resp = client.get(url)
            self.assertEquals(resp.status_code, 302)

        else:
            pass
