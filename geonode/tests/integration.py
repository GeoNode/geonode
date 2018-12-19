# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
# along with this profgram. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from .base import GeoNodeLiveTestSupport

import timeout_decorator

import os
import json
import datetime
import urllib2
# import base64
import time
import logging

from StringIO import StringIO
# import traceback
import gisdata
from decimal import Decimal
from lxml import etree
from urlparse import urljoin

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.contrib.staticfiles.templatetags import staticfiles
from django.contrib.auth import get_user_model
# from guardian.shortcuts import assign_perm
from geonode.base.populate_test_data import reconnect_signals, all_public
from tastypie.test import ResourceTestCaseMixin

from geonode.qgis_server.models import QGISServerLayer

from geoserver.catalog import FailedRequestError

# from geonode.security.models import *
from geonode.contrib import geotiffio
from geonode.decorators import on_ogc_backend
from geonode.base.models import TopicCategory, Link
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode import GeoNodeException, geoserver, qgis_server
from geonode.layers.utils import (
    upload,
    file_upload,
)
from geonode.tests.utils import check_layer, get_web_page

from geonode.geoserver.helpers import cascading_delete, set_attributes_from_geoserver
# FIXME(Ariel): Uncomment these when #1767 is fixed
# from geonode.geoserver.helpers import get_time_info
# from geonode.geoserver.helpers import get_wms
# from geonode.geoserver.helpers import set_time_info
from geonode.geoserver.signals import gs_catalog
from geonode.utils import check_ogc_backend

from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED

LOCAL_TIMEOUT = 300

LOGIN_URL = "/accounts/login/"

logger = logging.getLogger(__name__)

# Reconnect post_save signals that is disconnected by populate_test_data
reconnect_signals()


def zip_dir(basedir, archivename):
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED, allowZip64=True)) as z:
        for root, dirs, files in os.walk(basedir):
            # NOTE: ignore empty directories
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(basedir)+len(os.sep):]  # XXX: relative path
                z.write(absfn, zfn)


"""
 HOW TO RUN THE TESTS
 --------------------
 (https://github.com/GeoNode/geonode/blob/master/docs/tutorials/devel/testing.txt)

 1)
  (https://github.com/GeoNode/geonode/blob/master/docs/tutorials/devel/envsetup/paver.txt)

  $ paver setup

   1a. If using a PostgreSQL DB
       $ sudo su postgres
       $ psql
       ..>  ALTER USER test_geonode CREATEDB;
       ..>  ALTER USER test_geonode WITH SUPERUSER;
       ..>  \q
       $ exit

2)

  $ paver test_integration > tests_integration.log 2>&1

  2a)

    $ paver test_integration -n geonode.tests.integration:GeoNodeMapTest.test_cascading_delete

A. Create a GeoNode DB (If using a PostgreSQL DB)

$ sudo su postgres
$ psql -c "drop database test_geonode;"
$ createuser -P test_geonode
  pw: geonode
$ createdb -O test_geonode test_geonode
$ psql -d test_geonode -c "create extension postgis;"
$ psql -d test_geonode -c "grant all on spatial_ref_sys to public;"
$ psql -d test_geonode -c "grant all on geometry_columns to public;"
$ exit

$ geonode migrate
$ geonode createsuperuser

"""


class NormalUserTest(GeoNodeLiveTestSupport):

    """
    Tests GeoNode functionality for non-administrative users
    """

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_upload(self):
        """ Try uploading a layer and verify that the user can administrate
        his own layer despite not being a site administrator.
        """

        self.client.login(username='norman', password='norman')

        # TODO: Would be nice to ensure the name is available before
        # running the test...
        norman = get_user_model().objects.get(username="norman")
        saved_layer = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name="san_andres_y_providencia_poi_by_norman",
            user=norman,
            overwrite=True,
        )

        # Test that layer owner can wipe GWC Cache
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            from geonode.security.utils import set_geowebcache_invalidate_cache
            set_geowebcache_invalidate_cache(saved_layer.alternate)

            url = settings.OGC_SERVER['default']['LOCATION']
            user = settings.OGC_SERVER['default']['USER']
            passwd = settings.OGC_SERVER['default']['PASSWORD']

            import requests
            from requests.auth import HTTPBasicAuth
            r = requests.get(url + 'gwc/rest/seed/%s.json' % saved_layer.alternate,
                             auth=HTTPBasicAuth(user, passwd))
            self.assertEquals(r.status_code, 200)
            o = json.loads(r.text)
            self.assertTrue('long-array-array' in o)
            self.assertTrue(len(o['long-array-array']) > 0)
        try:
            saved_layer.set_default_permissions()
            url = reverse('layer_metadata', args=[saved_layer.service_typename])
            resp = self.client.get(url)
            self.assertEquals(resp.status_code, 200)
        finally:
            # Clean up and completely delete the layer
            saved_layer.delete()


class GeoNodeMapTest(GeoNodeLiveTestSupport):

    """
    Tests geonode.maps app/module
    """

    # geonode.maps.utils
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_raster_upload(self):
        """Test that the wcs links are correctly created for a raster"""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)
        try:
            wcs_link = False
            for link in uploaded.link_set.all():
                if link.mime == 'image/tiff':
                    wcs_link = True
            self.assertTrue(wcs_link)
        finally:
            # Clean up and completely delete the layer
            uploaded.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_zipped_files(self):
        """Test that the zipped files is created for raster."""
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)
        try:
            zip_link = False
            for link in uploaded.link_set.all():
                if link.mime == 'ZIP':
                    zip_link = True
            self.assertTrue(zip_link)
        finally:
            # Clean up and completely delete the layer
            uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_upload_bbox(self):
        """Test that the bbox format is correct

        Test that it is correctly saved in` database and represented in the
        properties correctly.
        """
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        uploaded = file_upload(filename)
        try:
            # Check bbox value
            bbox_x0 = Decimal('96.956000000000000')
            bbox_x1 = Decimal('97.109705320000000')
            bbox_y0 = Decimal('-5.518732999999900')
            bbox_y1 = Decimal('-5.303545551999900')
            srid = u'EPSG:4326'

            self.assertEqual(bbox_x0, uploaded.bbox_x0)
            self.assertEqual(bbox_x1, uploaded.bbox_x1)
            self.assertEqual(bbox_y0, uploaded.bbox_y0)
            self.assertEqual(bbox_y1, uploaded.bbox_y1)
            self.assertEqual(srid, uploaded.srid)

            # bbox format: [xmin,xmax,ymin,ymax]
            expected_bbox = [
                Decimal('96.956000000000000'),
                Decimal('97.109705320000000'),
                Decimal('-5.518732999999900'),
                Decimal('-5.303545551999900'),
                u'EPSG:4326'
            ]
            self.assertEqual(expected_bbox, uploaded.bbox)

            # bbox format: [xmin,ymin,xmax,ymax]
            expected_bbox_string = (
                '96.956000000000000,-5.518732999999900,97.109705320000000,-5.303545551999900')
            self.assertEqual(expected_bbox_string, uploaded.bbox_string)
        finally:
            # Clean up and completely delete the layer
            uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_upload(self):
        """Test that layers can be uploaded to running GeoNode/GeoServer
        """
        layers = {}
        expected_layers = []
        not_expected_layers = []

        for filename in os.listdir(gisdata.GOOD_DATA):
            basename, extension = os.path.splitext(filename)
            if extension.lower() in ['.tif', '.shp', '.zip']:
                expected_layers.append(
                    os.path.join(
                        gisdata.GOOD_DATA,
                        filename))

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
                    assert errors, msg
            else:
                msg = ('Upload should have returned either "name" or '
                       '"errors" for file %s.' % item['file'])
                assert 'name' in item, msg
                layers[item['file']] = item['name']

        msg = ('There were %s compatible layers in the directory,'
               ' but only %s were sucessfully uploaded' %
               (len(expected_layers), len(layers)))
        # assert len(layers) == len(expected_layers), msg

        for layer in expected_layers:
            msg = ('The following file should have been uploaded'
                   'but was not: %s. ' % layer)
            assert layer in layers, msg

            layer_name = layers[layer]

            # Check the layer is in the Django database
            Layer.objects.get(name=layer_name)

            # Check that layer is in geoserver
            found = False
            gs_username, gs_password = settings.OGC_SERVER['default'][
                'USER'], settings.OGC_SERVER['default']['PASSWORD']
            page = get_web_page(
                os.path.join(
                    settings.OGC_SERVER['default']['LOCATION'],
                    'rest/layers'),
                username=gs_username,
                password=gs_password)
            if page.find('rest/layers/%s.html' % layer_name) > 0:
                found = True
            if not found:
                msg = (
                    'Upload could not be verified, the layer %s is not '
                    'in geoserver %s, but GeoNode did not raise any errors, '
                    'this should never happen.' %
                    (layer_name, settings.OGC_SERVER['default']['LOCATION']))
                raise GeoNodeException(msg)

        # server_url = settings.OGC_SERVER['default']['LOCATION'] + 'ows?'
        # Verify that the GeoServer GetCapabilities record is accessible:
        # metadata = get_layers_metadata(server_url, '1.0.0')
        # msg = ('The metadata list should not be empty in server %s'
        #        % server_url)
        # assert len(metadata) > 0, msg
        # Check the keywords are recognized too

        # Clean up and completely delete the layers
        for layer in expected_layers:
            layer_name = layers[layer]
            Layer.objects.get(name=layer_name).delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_extension_not_implemented(self):
        """Verify a GeoNodeException is returned for not compatible extensions
        """
        sampletxt = os.path.join(gisdata.VECTOR_DATA,
                                 'points_epsg2249_no_prj.dbf')
        try:
            file_upload(sampletxt)
        except GeoNodeException:
            pass
        except Exception:
            raise
            # msg = ('Was expecting a %s, got %s instead.' %
            #        (GeoNodeException, type(e)))
            # assert e is GeoNodeException, msg

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_upload_metadata(self):
        """Test uploading a layer with XML metadata"""
        uploaded = None
        thelayer = os.path.join(
            gisdata.PROJECT_ROOT,
            'both/good/sangis.org/Airport/Air_Runways.shp')

        self.assertTrue('%s.xml' % thelayer,
                        'Expected layer XML metadata to exist')
        try:
            if os.path.exists(thelayer):
                uploaded = file_upload(thelayer, overwrite=True)

                self.assertEqual(
                    uploaded.title,
                    'Air_Runways',
                    'Expected specific title from uploaded layer XML metadata')

                self.assertEqual(
                    uploaded.abstract,
                    'Airport Runways',
                    'Expected specific abstract from uploaded layer XML metadata')

                self.assertEqual(
                    uploaded.purpose,
                    'To show the location of Public Airports '
                    'and Runways within San Diego County',
                    'Expected specific purpose from uploaded layer XML metadata')

                self.assertEqual(uploaded.supplemental_information,
                                 'No information provided',
                                 'Expected specific supplemental information '
                                 'from uploaded layer XML metadata')

                if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                    self.assertEqual(
                        len(uploaded.keyword_list()), 7,
                        'Expected specific number of keywords from uploaded layer XML metadata')
                elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
                    # QGIS Server backend doesn't have GeoServer assigned keywords.
                    self.assertEqual(
                        len(uploaded.keyword_list()), 5,
                        'Expected specific number of keywords from uploaded layer XML metadata')

                self.assertTrue(
                     u'Airport,Airports,Landing Strips,Runway,Runways' in uploaded.keyword_csv,
                     'Expected CSV of keywords from uploaded layer XML metadata')

                self.assertTrue(
                    'Landing Strips' in uploaded.keyword_list(),
                    'Expected specific keyword from uploaded layer XML metadata')

                self.assertEqual(
                    uploaded.constraints_other,
                    'None',
                    'Expected specific constraint from uploaded layer XML metadata')

                from django.utils import timezone
                date = datetime.datetime(2010, 8, 3, 0, 0)
                date.replace(tzinfo=timezone.get_current_timezone())
                today = date.today()
                todoc = uploaded.date.today()
                self.assertEquals((today.day, today.month, today.year),
                                  (todoc.day, todoc.month, todoc.year),
                                  'Expected specific date from uploaded layer XML metadata')

                # Set
                from geonode.layers.metadata import set_metadata
                from geonode.layers.utils import resolve_regions

                thelayer_metadata = os.path.join(
                    gisdata.PROJECT_ROOT,
                    'both/good/sangis.org/Airport/Air_Runways.shp.xml')

                identifier, vals, regions, keywords = set_metadata(
                    open(thelayer_metadata).read())
                self.assertIsNotNone(regions)
                uploaded.metadata_xml = thelayer_metadata
                regions_resolved, regions_unresolved = resolve_regions(regions)
                self.assertIsNotNone(regions_resolved)
        except GeoNodeException as e:
            # layer have projection file, but has no valid srid
            self.assertEqual(
                str(e),
                "GeoServer failed to detect the projection for layer [air_runways]. "
                "It doesn't look like EPSG:4326, so backing out the layer.")
        finally:
            # Clean up and completely delete the layer
            if uploaded:
                uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_zip_upload_metadata(self):
        """Test uploading a layer with XML metadata"""
        uploaded = None
        thelayer_path = os.path.join(
            gisdata.PROJECT_ROOT,
            'both/good/sangis.org/Airport')
        thelayer_zip = os.path.join(
            gisdata.PROJECT_ROOT,
            'Air_Runways.zip')

        try:
            if os.path.exists(thelayer_zip):
                os.remove(thelayer_zip)
            if os.path.exists(thelayer_path) and not os.path.exists(thelayer_zip):
                zip_dir(thelayer_path, thelayer_zip)
                if os.path.exists(thelayer_zip):
                    uploaded = file_upload(thelayer_zip, overwrite=True)

                    self.assertEqual(
                        uploaded.title,
                        'Air_Runways',
                        'Expected specific title from uploaded layer XML metadata')

                    self.assertEqual(
                        uploaded.abstract,
                        'Airport Runways',
                        'Expected specific abstract from uploaded layer XML metadata')

                    self.assertEqual(
                        uploaded.purpose,
                        'To show the location of Public Airports '
                        'and Runways within San Diego County',
                        'Expected specific purpose from uploaded layer XML metadata')

                    self.assertEqual(uploaded.supplemental_information,
                                     'No information provided',
                                     'Expected specific supplemental information '
                                     'from uploaded layer XML metadata')

                    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                        self.assertEqual(
                            len(uploaded.keyword_list()), 7,
                            'Expected specific number of keywords from uploaded layer XML metadata')
                    elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
                        # QGIS Server backend doesn't have GeoServer assigned keywords.
                        self.assertEqual(
                            len(uploaded.keyword_list()), 5,
                            'Expected specific number of keywords from uploaded layer XML metadata')

                    self.assertTrue(
                         u'Airport,Airports,Landing Strips,Runway,Runways' in uploaded.keyword_csv,
                         'Expected CSV of keywords from uploaded layer XML metadata')

                    self.assertTrue(
                        'Landing Strips' in uploaded.keyword_list(),
                        'Expected specific keyword from uploaded layer XML metadata')

                    self.assertEqual(
                        uploaded.constraints_other,
                        'None',
                        'Expected specific constraint from uploaded layer XML metadata')

                    from django.utils import timezone
                    date = datetime.datetime(2010, 8, 3, 0, 0)
                    date.replace(tzinfo=timezone.get_current_timezone())
                    today = date.today()
                    todoc = uploaded.date.today()
                    self.assertEquals((today.day, today.month, today.year),
                                      (todoc.day, todoc.month, todoc.year),
                                      'Expected specific date from uploaded layer XML metadata')

                    # Set
                    from geonode.layers.metadata import set_metadata
                    from geonode.layers.utils import resolve_regions

                    thelayer_metadata = os.path.join(
                        gisdata.PROJECT_ROOT,
                        'both/good/sangis.org/Airport/Air_Runways.shp.xml')

                    identifier, vals, regions, keywords = set_metadata(
                        open(thelayer_metadata).read())
                    self.assertIsNotNone(regions)
                    uploaded.metadata_xml = thelayer_metadata
                    regions_resolved, regions_unresolved = resolve_regions(regions)
                    self.assertIsNotNone(regions_resolved)
        finally:
            # Clean up and completely delete the layer
            if uploaded:
                uploaded.delete()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_zip_upload_non_utf8(self):
        """Test uploading a layer with non UTF-8 attributes names"""
        uploaded = None
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        thelayer_path = os.path.join(
            PROJECT_ROOT,
            'data/zhejiang_yangcan_yanyu')
        thelayer_zip = os.path.join(
            PROJECT_ROOT,
            'data/',
            'zhejiang_yangcan_yanyu.zip')
        try:
            if os.path.exists(thelayer_zip):
                os.remove(thelayer_zip)
            if os.path.exists(thelayer_path) and not os.path.exists(thelayer_zip):
                zip_dir(thelayer_path, thelayer_zip)
                if os.path.exists(thelayer_zip):
                    uploaded = file_upload(thelayer_zip, overwrite=True, charset='windows-1258')
                    self.assertEquals(uploaded.title, 'Zhejiang Yangcan Yanyu')
                    self.assertEquals(len(uploaded.keyword_list()), 2)
                    self.assertEquals(uploaded.constraints_other, None)
        finally:
            # Clean up and completely delete the layer
            if uploaded:
                uploaded.delete()

        uploaded = None
        thelayer_path = os.path.join(
            PROJECT_ROOT,
            'data/ming_female_1')
        thelayer_zip = os.path.join(
            PROJECT_ROOT,
            'data/',
            'ming_female_1.zip')
        try:
            if os.path.exists(thelayer_zip):
                os.remove(thelayer_zip)
            if os.path.exists(thelayer_path) and not os.path.exists(thelayer_zip):
                zip_dir(thelayer_path, thelayer_zip)
                if os.path.exists(thelayer_zip):
                    uploaded = file_upload(thelayer_zip, overwrite=True, charset='windows-1258')
                    self.assertEquals(uploaded.title, 'Ming Female 1')
                    self.assertEquals(len(uploaded.keyword_list()), 2)
                    self.assertEquals(uploaded.constraints_other, None)
        finally:
            # Clean up and completely delete the layer
            if uploaded:
                uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_shapefile(self):
        """Test Uploading a good shapefile
        """
        thefile = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        uploaded = file_upload(thefile, overwrite=True)
        try:
            check_layer(uploaded)
        finally:
            # Clean up and completely delete the layer
            uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_bad_shapefile(self):
        """Verifying GeoNode complains about a shapefile without .prj
        """
        thefile = os.path.join(gisdata.BAD_DATA, 'points_epsg2249_no_prj.shp')
        try:
            # with self.assertRaises(GeoNodeException):
            thefile = file_upload(thefile, overwrite=True)
        except GeoNodeException as e:
            self.assertEqual(str(e), "Invalid Projection. Layer is missing CRS!")
        finally:
            # Clean up and completely delete the layer
            try:
                thefile.delete()
            except BaseException:
                pass

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_tiff(self):
        """Uploading a good .tiff
        """
        thefile = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        uploaded = file_upload(thefile, overwrite=True)
        try:
            check_layer(uploaded)
        finally:
            # Clean up and completely delete the layer
            uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
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
        try:
            msg = ('Expected %s but got %s' % (uploaded1.name, uploaded2.name))
            assert uploaded1.name == uploaded2.name, msg
            msg = ('Expected a different name when uploading %s using '
                   'overwrite=False but got %s' % (thefile, uploaded3.name))
            assert uploaded1.name != uploaded3.name, msg
        finally:
            # Clean up and completely delete the layers
            # uploaded1 is overwritten by uploaded2 ... no need to delete it
            uploaded2.delete()
            uploaded3.delete()

    # geonode.maps.views

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_delete_from_geoserver(self):
        """Verify that layer is correctly deleted from GeoServer
        """
        # Layer.delete() calls the pre_delete hook which uses cascading_delete()
        # Should we explicitly test that the styles and store are
        # deleted as well as the resource itself?
        # There is already an explicit test for cascading delete

        gs_cat = gs_catalog

        # Test Uploading then Deleting a Shapefile from GeoServer
        shp_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file, overwrite=True)
        # we need some time to have the service up and running
        time.sleep(20)

        ws = gs_cat.get_workspace(shp_layer.workspace)
        shp_store = gs_cat.get_store(shp_layer.store, ws)
        shp_store_name = shp_store.name
        shp_layer.delete()

        # Verify that the store was deleted
        ds = gs_cat.get_store(shp_store_name)
        self.assertIsNone(ds)

        # Test Uploading then Deleting a TIFF file from GeoServer
        tif_file = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        tif_layer = file_upload(tif_file)
        ws = gs_cat.get_workspace(tif_layer.workspace)
        tif_store = gs_cat.get_store(tif_layer.store, ws)
        tif_layer.delete()
        self.assertRaises(
            FailedRequestError,
            lambda: gs_cat.get_resource(
                shp_layer.name,
                store=tif_store))

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_delete_layer(self):
        """Verify that the 'delete_layer' pre_delete hook is functioning
        """

        gs_cat = gs_catalog

        # Upload a Shapefile Layer
        shp_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)

        # we need some time to have the service up and running
        time.sleep(20)

        shp_layer_id = shp_layer.pk
        ws = gs_cat.get_workspace(shp_layer.workspace)
        shp_store = gs_cat.get_store(shp_layer.store, ws)
        shp_store_name = shp_store.name

        uuid = shp_layer.uuid

        # Delete it with the Layer.delete() method
        shp_layer.delete()

        # Verify that it no longer exists in GeoServer
        res = gs_cat.get_layer(shp_layer.name)
        self.assertIsNone(res)

        # Verify that the store was deleted
        ds = gs_cat.get_store(shp_store_name)
        self.assertIsNone(ds)

        # Check that it was also deleted from GeoNodes DB
        self.assertRaises(ObjectDoesNotExist,
                          lambda: Layer.objects.get(pk=shp_layer_id))

        # geonode.geoserver.helpers
        # If catalogue is installed, then check that it is deleted from there
        # too.
        if 'geonode.catalogue' in settings.INSTALLED_APPS:
            from geonode.catalogue import get_catalogue
            catalogue = get_catalogue()

            # Verify that it no longer exists in GeoNetwork
            shp_layer_gn_info = catalogue.get_record(uuid)
            assert shp_layer_gn_info is None

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_geoserver_cascading_delete(self):
        """Verify that the helpers.cascading_delete() method is working properly
        """
        gs_cat = gs_catalog

        # Upload a Shapefile
        shp_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)
        try:
            # Save the names of the Resource/Store/Styles
            resource_name = shp_layer.name
            ws = gs_cat.get_workspace(shp_layer.workspace)
            store = gs_cat.get_store(shp_layer.store, ws)
            store_name = store.name
            layer = gs_cat.get_layer(resource_name)
            styles = layer.styles + [layer.default_style]

            # Delete the Layer using cascading_delete()
            cascading_delete(gs_cat, shp_layer.alternate)

            # Verify that the styles were deleted
            for style in styles:
                if style and style.name:
                    s = gs_cat.get_style(style.name, workspace=settings.DEFAULT_WORKSPACE) or \
                        gs_cat.get_style(style.name)
                    assert s is None

            # Verify that the store was deleted
            ds = gs_cat.get_store(store_name)
            self.assertIsNone(ds)
        finally:
            # Clean up and completely delete the layers
            shp_layer.delete()

    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_qgis_server_cascading_delete(self):
        """Verify that QGIS Server layer deleted and cascaded."""
        # Upload a Shapefile
        shp_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        shp_layer = file_upload(shp_file)
        try:
            # get layer and QGIS Server Layer object
            qgis_layer = shp_layer.qgis_layer
            base_path = qgis_layer.base_layer_path
            base_name, _ = os.path.splitext(base_path)

            # get existing files
            file_paths = qgis_layer.files

            for path in file_paths:
                self.assertTrue(os.path.exists(path))

            # try to access a tile to trigger tile cache
            tile_url = reverse(
                'qgis_server:tile',
                kwargs={
                    'layername': shp_layer.name,
                    'z': 9,
                    'x': 139,
                    'y': 238
                })
            response = self.client.get(tile_url)

            self.assertTrue(response.status_code, 200)

            self.assertTrue(os.path.exists(qgis_layer.cache_path))
        finally:
            # delete layer
            shp_layer.delete()

        # verify that qgis server layer no longer exists
        with self.assertRaises(QGISServerLayer.DoesNotExist):
            QGISServerLayer.objects.get(pk=qgis_layer.pk)

        with self.assertRaises(QGISServerLayer.DoesNotExist):
            QGISServerLayer.objects.get(layer__id=shp_layer.id)

        # verify that related files in QGIS Server object gets deleted.
        for path in file_paths:
            self.assertFalse(os.path.exists(path))

        # verify that cache path gets deleted
        self.assertFalse(os.path.exists(qgis_layer.cache_path))

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_keywords_upload(self):
        """Check that keywords can be passed to file_upload
        """
        thefile = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        uploaded = file_upload(
            thefile,
            keywords=[
                'foo',
                'bar'],
            overwrite=True)
        try:
            keywords = uploaded.keyword_list()
            msg = 'No keywords found in layer %s' % uploaded.name
            assert len(keywords) > 0, msg
            assert 'foo' in uploaded.keyword_list(
            ), 'Could not find "foo" in %s' % keywords
            assert 'bar' in uploaded.keyword_list(
            ), 'Could not find "bar" in %s' % keywords
        finally:
            # Clean up and completely delete the layers
            uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_empty_bbox(self):
        """Regression-test for failures caused by zero-width bounding boxes"""
        thefile = os.path.join(gisdata.VECTOR_DATA, 'single_point.shp')
        uploaded = file_upload(thefile, overwrite=True)
        try:
            uploaded.set_default_permissions()
            self.client.login(username='norman', password='norman')
            resp = self.client.get(uploaded.get_absolute_url())
            self.assertEquals(resp.status_code, 200)
        finally:
            # Clean up and completely delete the layers
            uploaded.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_replace(self):
        """Test layer replace functionality
        """
        vector_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_administrative.shp')
        vector_layer = file_upload(vector_file, overwrite=True)

        raster_file = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        raster_layer = file_upload(raster_file, overwrite=True)

        # we need some time to have the service up and running
        time.sleep(20)
        new_vector_layer = None
        try:
            self.client.login(username='admin', password='admin')

            # test the program can determine the original layer in raster type
            raster_replace_url = reverse(
                'layer_replace', args=[
                    raster_layer.service_typename])
            response = self.client.get(raster_replace_url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.context['is_featuretype'], False)

            # test the program can determine the original layer in vector type
            vector_replace_url = reverse(
                'layer_replace', args=[
                    vector_layer.service_typename])
            response = self.client.get(vector_replace_url)
            self.assertEquals(response.status_code, 200)
            self.assertEquals(response.context['is_featuretype'], True)

            # test replace a vector with a raster
            post_permissions = {
                'users': {
                    'AnonymousUser': [
                        'view_resourcebase', 'download_resourcebase']
                },
                'groups': {}
            }
            post_data = {
                'base_file': open(
                    raster_file, 'rb'),
                'permissions': json.dumps(post_permissions)
            }
            response = self.client.post(
                vector_replace_url, post_data)
            # TODO: This should really return a 400 series error with the json dict
            self.assertEquals(response.status_code, 400)
            response_dict = json.loads(response.content)
            self.assertEquals(response_dict['success'], False)

            # test replace a vector with a different vector
            new_vector_file = os.path.join(
                gisdata.VECTOR_DATA,
                'san_andres_y_providencia_coastline.shp')
            layer_path, __ = os.path.splitext(new_vector_file)
            layer_base = open(layer_path + '.shp', 'rb')
            layer_dbf = open(layer_path + '.dbf', 'rb')
            layer_shx = open(layer_path + '.shx', 'rb')
            layer_prj = open(layer_path + '.prj', 'rb')

            response = self.client.post(
                vector_replace_url,
                {'base_file': layer_base,
                 'dbf_file': layer_dbf,
                 'shx_file': layer_shx,
                 'prj_file': layer_prj,
                 'charset': 'UTF-8',
                 'permissions': json.dumps(post_permissions)
                 })
            response_dict = json.loads(response.content)

            if not response_dict['success'] and 'unknown encoding' in \
                    response_dict['errors']:
                # print(response_dict['errors'])
                pass
            else:
                self.assertEquals(response.status_code, 200)
                self.assertEquals(response_dict['success'], True)
                # Get a Layer object for the newly created layer.
                new_vector_layer = Layer.objects.get(pk=vector_layer.pk)

                # Test the replaced layer metadata is equal to the original layer
                self.assertEqual(vector_layer.name, new_vector_layer.name)
                self.assertEqual(vector_layer.title, new_vector_layer.title)
                self.assertEqual(vector_layer.alternate, new_vector_layer.alternate)

                # Test the replaced layer bbox is indeed different from the original layer
                self.assertNotEqual(vector_layer.bbox_x0, new_vector_layer.bbox_x0)
                self.assertNotEqual(vector_layer.bbox_x1, new_vector_layer.bbox_x1)
                self.assertNotEqual(vector_layer.bbox_y0, new_vector_layer.bbox_y0)
                self.assertNotEqual(vector_layer.bbox_y1, new_vector_layer.bbox_y1)

                # test an invalid user without layer replace permission
                self.client.logout()
                self.client.login(username='norman', password='norman')

                response = self.client.post(
                    vector_replace_url,
                    {'base_file': layer_base,
                     'dbf_file': layer_dbf,
                     'shx_file': layer_shx,
                     'prj_file': layer_prj,
                     'permissions': json.dumps(post_permissions)
                     })
                self.assertEquals(response.status_code, 401)
        finally:
            # Clean up and completely delete the layer
            try:
                if vector_layer:
                    vector_layer.delete()
                if raster_layer:
                    raster_layer.delete()
                if new_vector_layer:
                    new_vector_layer.delete()
            except BaseException:
                # tb = traceback.format_exc()
                # logger.warning(tb)
                pass

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_importlayer_mgmt_command(self):
        """Test layer import management command
        """
        vector_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_administrative.shp')

        call_command('importlayers', vector_file, overwrite=True,
                     keywords="test, import, san andreas",
                     title="Test San Andres y Providencia Administrative",
                     verbosity=1)

        lyr = Layer.objects.get(title='Test San Andres y Providencia Administrative')
        try:
            self.assertIsNotNone(lyr)
            self.assertEqual(lyr.name, "test_san_andres_y_providencia_administrative")
            self.assertEqual(lyr.title, "Test San Andres y Providencia Administrative")

            default_keywords = [
                u'import',
                u'san andreas',
                u'test',
            ]
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                geoserver_keywords = [
                    u'features',
                    u'test_san_andres_y_providencia_administrative'
                ]
                self.assertEqual(
                    set(lyr.keyword_list()),
                    set(default_keywords + geoserver_keywords))
            elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
                self.assertEqual(
                    set(lyr.keyword_list()),
                    set(default_keywords))
        finally:
            # Clean up and completely delete the layer
            lyr.delete()


class GeoNodePermissionsTest(GeoNodeLiveTestSupport):
    """
    Tests GeoNode permissions and its integration with GeoServer
    """

    """
    AF: This test must be refactored. Opening an issue for that.
    def test_permissions(self):
        # Test permissions on a layer

        # grab norman
        norman = get_user_model().objects.get(username="norman")

        thefile = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        layer = file_upload(thefile, overwrite=True)
        check_layer(layer)

        # we need some time to have the service up and running
        time.sleep(20)

        # Set the layer private for not authenticated users
        layer.set_permissions({'users': {'AnonymousUser': []}})

        url = 'http://localhost:8080/geoserver/geonode/ows?' \
            'LAYERS=geonode%3Asan_andres_y_providencia_poi&STYLES=' \
            '&FORMAT=image%2Fpng&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap' \
            '&SRS=EPSG%3A4326' \
            '&BBOX=-81.394599749999,13.316009005566,' \
            '-81.370560451855,13.372728455566' \
            '&WIDTH=217&HEIGHT=512'

        # test view_resourcebase permission on anonymous user
        request = urllib2.Request(url)
        response = urllib2.urlopen(request)
        self.assertTrue(
            response.info().getheader('Content-Type'),
            'application/vnd.ogc.se_xml;charset=UTF-8'
        )

        # test WMS with authenticated user that has not view_resourcebase:
        # the layer must be not accessible (response is xml)
        request = urllib2.Request(url)
        base64string = base64.encodestring(
            '%s:%s' % ('norman', 'norman')).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request)
        self.assertTrue(
            response.info().getheader('Content-Type'),
            'application/vnd.ogc.se_xml;charset=UTF-8'
        )

        # test WMS with authenticated user that has view_resourcebase: the layer
        # must be accessible (response is image)
        assign_perm('view_resourcebase', norman, layer.get_self_resource())
        request = urllib2.Request(url)
        base64string = base64.encodestring(
            '%s:%s' % ('norman', 'norman')).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request)
        self.assertTrue(response.info().getheader('Content-Type'), 'image/png')

        # test change_layer_data
        # would be nice to make a WFS/T request and test results, but this
        # would work only on PostGIS layers

        # test change_layer_style
        url = 'http://localhost:8000/gs/rest/styles/san_andres_y_providencia_poi.xml'
        sld = ""<?xml version="1.0" encoding="UTF-8"?>
<sld:StyledLayerDescriptor xmlns:sld="http://www.opengis.net/sld"
xmlns:gml="http://www.opengis.net/gml" xmlns:ogc="http://www.opengis.net/ogc"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.0.0"
xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.0.0/StyledLayerDescriptor.xsd">
   <sld:NamedLayer>
      <sld:Name>geonode:san_andres_y_providencia_poi</sld:Name>
      <sld:UserStyle>
         <sld:Name>san_andres_y_providencia_poi</sld:Name>
         <sld:Title>san_andres_y_providencia_poi</sld:Title>
         <sld:IsDefault>1</sld:IsDefault>
         <sld:FeatureTypeStyle>
            <sld:Rule>
               <sld:PointSymbolizer>
                  <sld:Graphic>
                     <sld:Mark>
                        <sld:Fill>
                           <sld:CssParameter name="fill">#8A7700
                           </sld:CssParameter>
                        </sld:Fill>
                        <sld:Stroke>
                           <sld:CssParameter name="stroke">#bbffff
                           </sld:CssParameter>
                        </sld:Stroke>
                     </sld:Mark>
                     <sld:Size>10</sld:Size>
                  </sld:Graphic>
               </sld:PointSymbolizer>
            </sld:Rule>
         </sld:FeatureTypeStyle>
      </sld:UserStyle>
   </sld:NamedLayer>
</sld:StyledLayerDescriptor>""

        # user without change_layer_style cannot edit it
        self.client.login(username='norman', password='norman')
        response = self.client.put(url, sld, content_type='application/vnd.ogc.sld+xml')
        self.assertEquals(response.status_code, 401)

        # user with change_layer_style can edit it
        assign_perm('change_layer_style', norman, layer)
        response = self.client.put(url, sld, content_type='application/vnd.ogc.sld+xml')
        self.assertEquals(response.status_code, 200)

        # Clean up and completely delete the layer
        layer.delete()
    """

    def setUp(self):
        super(GeoNodeLiveTestSupport, self).setUp()
        settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_unpublished(self):
        """Test permissions on an unpublished layer
        """
        thefile = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_highway.shp')
        layer = file_upload(thefile, overwrite=True)
        layer.set_default_permissions()
        check_layer(layer)

        # we need some time to have the service up and running
        time.sleep(20)

        try:
            # request getCapabilities: layer must be there as it is published and
            # advertised: we need to check if in response there is
            # <Name>geonode:san_andres_y_providencia_water</Name>
            geoserver_base_url = settings.OGC_SERVER['default']['LOCATION']
            get_capabilities_url = 'ows?' \
                'service=wms&version=1.3.0&request=GetCapabilities'
            url = urljoin(geoserver_base_url, get_capabilities_url)
            str_to_check = '<Name>geonode:san_andres_y_providencia_highway</Name>'
            request = urllib2.Request(url)
            response = urllib2.urlopen(request)

            # by default the uploaded layer is published
            self.assertTrue(layer.is_published, True)
            self.assertTrue(any(str_to_check in s for s in response.readlines()))
        finally:
            # Clean up and completely delete the layer
            layer.delete()

        # with settings disabled
        with self.settings(RESOURCE_PUBLISHING=True):
            layer = file_upload(thefile,
                                overwrite=True,
                                is_approved=False,
                                is_published=False)
            layer.set_default_permissions()
            check_layer(layer)

            # we need some time to have the service up and running
            time.sleep(20)

            try:
                # by default the uploaded layer must be unpublished
                self.assertEqual(layer.is_published, False)

                # check the layer is not in GetCapabilities
                request = urllib2.Request(url)
                response = urllib2.urlopen(request)
                self.assertFalse(any(str_to_check in s for s in response.readlines()))

                # now test with published layer
                layer = Layer.objects.get(pk=layer.pk)
                layer.is_published = True
                layer.save()

                # we need some time to have the service up and running
                time.sleep(20)

                request = urllib2.Request(url)
                response = urllib2.urlopen(request)
                self.assertTrue(any(str_to_check in s for s in response.readlines()))
            finally:
                # Clean up and completely delete the layer
                layer.delete()


class GeoNodeThumbnailTest(GeoNodeLiveTestSupport):

    """
    Tests thumbnails behavior for layers and maps.
    """

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_thumbnail(self):
        """Test the layer save method generates a thumbnail link
        """
        # TODO: Would be nice to ensure the name is available before
        # running the test...
        norman = get_user_model().objects.get(username="norman")
        saved_layer = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name="san_andres_y_providencia_poi_by_norman",
            user=norman,
            overwrite=True,
        )
        try:
            self.client.login(username='norman', password='norman')

            thumbnail_url = saved_layer.get_thumbnail_url()
            self.assertNotEqual(thumbnail_url, staticfiles.static(settings.MISSING_THUMBNAIL))
        finally:
            # Cleanup
            saved_layer.delete()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_map_thumbnail(self):
        """Test the map save method generates a thumbnail link
        """
        # TODO: Would be nice to ensure the name is available before
        # running the test...
        norman = get_user_model().objects.get(username="norman")
        saved_layer = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name="san_andres_y_providencia_poi_by_norman",
            user=norman,
            overwrite=True,
        )
        try:
            self.client.login(username='norman', password='norman')

            saved_layer.set_default_permissions()
            map_obj = Map(owner=norman, zoom=0,
                          center_x=0, center_y=0)
            map_obj.create_from_layer_list(norman, [saved_layer], 'title', '')

            thumbnail_url = map_obj.get_thumbnail_url()

            self.assertNotEqual(thumbnail_url, staticfiles.static(settings.MISSING_THUMBNAIL))
        finally:
            # Cleanup
            saved_layer.delete()


class GeoNodeMapPrintTest(GeoNodeLiveTestSupport):

    """
    Tests geonode.maps print
    """

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def testPrintProxy(self):
        """ Test the PrintProxyMiddleware if activated.
            It should respect the permissions on private layers.
        """

        if 'geonode.middleware.PrintProxyMiddleware' in settings.MIDDLEWARE_CLASSES:
            # STEP 1: Import a layer
            from geonode.maps.models import Map

            self.client.login(username='norman', password='norman')

            # TODO: Would be nice to ensure the name is available before
            # running the test...
            norman = get_user_model().objects.get(username="norman")
            saved_layer = file_upload(
                os.path.join(
                    gisdata.VECTOR_DATA,
                    "san_andres_y_providencia_poi.shp"),
                name="san_andres_y_providencia_poi_by_norman",
                user=norman,
                overwrite=True,
            )
            try:
                # Set the layer private
                saved_layer.set_permissions(
                    {'users': {'AnonymousUser': ['view_resourcebase']}})

                url = reverse(
                    'layer_metadata',
                    args=[
                        saved_layer.service_typename])

                # check is accessible while logged in
                resp = self.client.get(url)
                self.assertEquals(resp.status_code, 200)

                # check is inaccessible when not logged in
                self.client.logout()
                resp = self.client.get(url)
                self.assertEquals(resp.status_code, 302)

                # STEP 2: Create a Map with that layer

                map_obj = Map(owner=norman, zoom=0,
                              center_x=0, center_y=0)
                map_obj.create_from_layer_list(norman, [saved_layer], 'title', '')

                # STEP 3: Print the map

                print_url = settings.OGC_SERVER['default'][
                    'LOCATION'] + 'pdf/create.json'

                post_payload = {
                    'dpi': 75,
                    'layers': [
                        {
                            'baseURL': settings.OGC_SERVER['default']['LOCATION'] +
                            'wms?SERVICE=WMS&',
                            'format': "image/png",
                            'customParams': {
                                'TILED': True,
                                'TRANSPARENT': True},
                            'layers': [
                                saved_layer.service_typename],
                            'opacity': 1,
                            'singleTile': False,
                            'type': 'WMS'}],
                    'layout': 'A4 portrait',
                    'mapTitle': 'test',
                    'outputFilename': 'print',
                    'srs': getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857'),
                    'units': 'm'}

                self.client.post(print_url, post_payload)

                # Test the layer is still inaccessible as non authenticated
                resp = self.client.get(url)
                self.assertEquals(resp.status_code, 302)
            finally:
                # Clean up and completely delete the layer
                saved_layer.delete()
        else:
            pass


class GeoNodeGeoServerSync(GeoNodeLiveTestSupport):

    """
    Tests GeoNode/GeoServer syncronization
    """

    def setUp(self):
        super(GeoNodeLiveTestSupport, self).setUp()
        settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_set_attributes_from_geoserver(self):
        """Test attributes syncronization
        """

        # upload a shapefile
        shp_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        layer = file_upload(shp_file)
        try:
            # set attributes for resource
            for attribute in layer.attribute_set.all():
                attribute.attribute_label = '%s_label' % attribute.attribute
                attribute.description = '%s_description' % attribute.attribute
                attribute.save()

            # sync the attributes with GeoServer
            set_attributes_from_geoserver(layer)

            # tests if everything is synced properly
            for attribute in layer.attribute_set.all():
                self.assertEquals(
                    attribute.attribute_label,
                    '%s_label' % attribute.attribute
                )
                self.assertEquals(
                    attribute.description,
                    '%s_description' % attribute.attribute
                )

            links = Link.objects.filter(resource=layer.resourcebase_ptr)
            self.assertIsNotNone(links)
            self.assertTrue(len(links) > 7)

            original_data_links = [ll for ll in links if 'original' == ll.link_type]
            self.assertEquals(len(original_data_links), 1)

            resp = self.client.get(original_data_links[0].url)
            self.assertEquals(resp.status_code, 200)
        finally:
            # Clean up and completely delete the layers
            layer.delete()


class GeoNodeGeoServerCapabilities(GeoNodeLiveTestSupport):

    """
    Tests GeoNode/GeoServer GetCapabilities per layer, user, category and map
    """

    def setUp(self):
        super(GeoNodeLiveTestSupport, self).setUp()
        settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED'] = True

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_capabilities(self):
        """Test capabilities
        """

        # a category
        category = TopicCategory.objects.all()[0]

        # some users
        norman = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")

        # create 3 layers, 2 with norman as an owner an 2 with category as a category
        layer1 = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_poi.shp"),
            name='layer1',
            user=norman,
            category=category,
            overwrite=True,
        )
        layer2 = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "single_point.shp"),
            name='layer2',
            user=norman,
            overwrite=True,
        )
        layer3 = file_upload(
            os.path.join(
                gisdata.VECTOR_DATA,
                "san_andres_y_providencia_administrative.shp"),
            name='layer3',
            user=admin,
            category=category,
            overwrite=True,
        )
        try:
            namespaces = {'wms': 'http://www.opengis.net/wms',
                          'xlink': 'http://www.w3.org/1999/xlink',
                          'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

            # 0. test capabilities_layer
            url = reverse('capabilities_layer', args=[layer1.id])
            resp = self.client.get(url)
            layercap = etree.fromstring(resp.content)
            rootdoc = etree.ElementTree(layercap)
            layernodes = rootdoc.findall('./[wms:Name]', namespaces)
            layernode = layernodes[0]

            self.assertEquals(1, len(layernodes))
            self.assertEquals(layernode.find('wms:Name', namespaces).text,
                              '%s:%s' % ('geonode', layer1.name))

            # 1. test capabilities_user
            url = reverse('capabilities_user', args=[norman.username])
            resp = self.client.get(url)
            layercap = etree.fromstring(resp.content)
            rootdoc = etree.ElementTree(layercap)
            layernodes = rootdoc.findall('./[wms:Name]', namespaces)

            # norman has 2 layers
            self.assertEquals(1, len(layernodes))

            # the norman two layers are named layer1 and layer2
            count = 0
            for layernode in layernodes:
                if layernode.find('wms:Name', namespaces).text == '%s:%s' % ('geonode', layer1.name):
                    count += 1
                elif layernode.find('wms:Name', namespaces).text == '%s:%s' % ('geonode', layer2.name):
                    count += 1
            self.assertEquals(1, count)

            # 2. test capabilities_category
            url = reverse('capabilities_category', args=[category.identifier])
            resp = self.client.get(url)
            layercap = etree.fromstring(resp.content)
            rootdoc = etree.ElementTree(layercap)
            layernodes = rootdoc.findall('./[wms:Name]', namespaces)

            # category is in two layers
            self.assertEquals(1, len(layernodes))

            # the layers for category are named layer1 and layer3
            count = 0
            for layernode in layernodes:
                if layernode.find('wms:Name', namespaces).text == '%s:%s' % ('geonode', layer1.name):
                    count += 1
                elif layernode.find('wms:Name', namespaces).text == '%s:%s' % ('geonode', layer3.name):
                    count += 1
            self.assertEquals(1, count)

            # 3. test for a map
            # TODO
        finally:
            # Clean up and completely delete the layers
            layer1.delete()
            layer2.delete()
            layer3.delete()


class LayersStylesApiInteractionTests(
        ResourceTestCaseMixin, GeoNodeLiveTestSupport):
    """Test Layers"""

    def setUp(self):
        super(LayersStylesApiInteractionTests, self).setUp()

        self.layer_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        self.style_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'styles'})
        filename = os.path.join(gisdata.GOOD_DATA, 'raster/test_grid.tif')
        self.layer = file_upload(filename)
        all_public()

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_layer_interaction(self):
        """Layer API interaction check."""
        layer_id = self.layer.id

        layer_detail_url = reverse(
            'api_dispatch_detail',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers',
                'id': layer_id
            }
        )
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        # Should have links
        self.assertTrue('links' in obj and obj['links'])
        # Should have default style
        self.assertTrue('default_style' in obj and obj['default_style'])
        # Should have styles
        self.assertTrue('styles' in obj and obj['styles'])

        # Test filter layers by id
        filter_url = self.layer_list_url + '?id=' + str(layer_id)
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']
        self.assertEqual(len(objects), 1)
        obj = objects[0]
        # Should not have links
        self.assertFalse('links' in obj)
        # Should not have styles
        self.assertTrue('styles' not in obj)
        # Should have default_style
        self.assertTrue('default_style' in obj and obj['default_style'])
        # Should have resource_uri to browse layer detail
        self.assertTrue('resource_uri' in obj and obj['resource_uri'])

        prev_obj = obj
        # Test filter layers by name
        filter_url = self.layer_list_url + '?name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']
        self.assertEqual(len(objects), 1)
        obj = objects[0]

        self.assertEqual(obj, prev_obj)

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_style_interaction(self):
        """Style API interaction check."""

        # filter styles by layer id
        filter_url = self.style_list_url + '?layer__id=' + str(self.layer.id)
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']

        self.assertEqual(len(objects), 1)

        # filter styles by layer name
        filter_url = self.style_list_url + '?layer__name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        # This is a list url
        objects = self.deserialize(resp)['objects']

        self.assertEqual(len(objects), 1)

        # Check necessary list fields
        obj = objects[0]
        field_list = [
            'layer',
            'name',
            'title',
            'style_url',
            'type',
            'resource_uri'
        ]

        # Additional field based on OGC Backend
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            field_list += [
                'version',
                'workspace'
            ]
        elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            field_list += [
                'style_legend_url'
            ]
        for f in field_list:
            self.assertTrue(f in obj)

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            self.assertEqual(obj['type'], 'sld')
        elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            self.assertEqual(obj['type'], 'qml')

        # Check style detail
        detail_url = obj['resource_uri']
        resp = self.api_client.get(detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)

        # should include body field
        self.assertTrue('body' in obj and obj['body'])

    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @on_ogc_backend(qgis_server.BACKEND_PACKAGE)
    def test_add_delete_styles(self):
        """Style API Add/Delete interaction."""
        # Check styles count
        style_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'styles'
            }
        )
        filter_url = style_list_url + '?layer__name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        objects = self.deserialize(resp)['objects']

        # Fetch default style
        layer_detail_url = reverse(
            'api_dispatch_detail',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers',
                'id': self.layer.id
            }
        )
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        # Take default style url from Layer detail info

        default_style_url = obj['default_style']
        try:
            resp = self.api_client.get(default_style_url)
            if resp.status_code != 200:
                return
        except BaseException:
            return
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        style_body = obj['body']

        style_stream = StringIO(style_body)
        # Add virtual filename
        style_stream.name = 'style.qml'
        data = {
            'layer__id': self.layer.id,
            'name': 'new_style',
            'title': 'New Style',
            'style': style_stream
        }
        # Use default client to request
        resp = self.client.post(style_list_url, data=data)

        # Should not be able to add style without authentication
        self.assertEqual(resp.status_code, 403)

        # Login using anonymous user
        self.client.login(username='AnonymousUser')
        style_stream.seek(0)
        resp = self.client.post(style_list_url, data=data)
        # Should not be able to add style without correct permission
        self.assertEqual(resp.status_code, 403)
        self.client.logout()

        # Use admin credentials
        self.client.login(username='admin', password='admin')
        style_stream.seek(0)
        resp = self.client.post(style_list_url, data=data)
        self.assertEqual(resp.status_code, 201)

        # Check styles count
        filter_url = style_list_url + '?layer__name=' + self.layer.name
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        objects = self.deserialize(resp)['objects']

        self.assertEqual(len(objects), 2)

        # Attempt to set default style
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        # Get style list and get new default style
        styles = obj['styles']
        new_default_style = None
        for s in styles:
            if not s == obj['default_style']:
                new_default_style = s
                break
        obj['default_style'] = new_default_style
        # Put the new update
        patch_data = {
            'default_style': new_default_style
        }
        resp = self.client.patch(
            layer_detail_url,
            data=json.dumps(patch_data),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        # check new default_style
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        self.assertEqual(obj['default_style'], new_default_style)

        # Attempt to delete style
        filter_url = style_list_url + '?layer__id=%d&name=%s' % (
            self.layer.id, data['name'])
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        objects = self.deserialize(resp)['objects']

        resource_uri = objects[0]['resource_uri']

        resp = self.client.delete(resource_uri)
        self.assertEqual(resp.status_code, 204)

        resp = self.api_client.get(filter_url)
        meta = self.deserialize(resp)['meta']

        self.assertEqual(meta['total_count'], 0)


class GeoTIFFIOTest(GeoNodeLiveTestSupport):
    """
    Tests integration of geotiff.io
    """

    def testLink(self):
        thefile = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        uploaded = file_upload(thefile, overwrite=True)
        access_token = "8FYB137y87sdfb8b1l8ybf7dsbf"

        # changing settings for this test
        geotiffio.settings.GEOTIFF_IO_ENABLED = True
        geotiffio.settings.GEOTIFF_IO_BASE_URL = "http://app.geotiff.io"

        url = geotiffio.create_geotiff_io_url(uploaded, access_token)
        expected = (
            'http://app.geotiff.io?url='
            'http%3A//localhost%3A8000/gs/wcs%3F'
            'service%3DWCS'
            '%26format%3Dimage%252Ftiff'
            '%26request%3DGetCoverage'
            '%26srs%3DEPSG%253A4326'
            '%26version%3D2.0.1'
            '%26coverageid%3Dgeonode%253Atest_grid'
            '%26access_token%3D8FYB137y87sdfb8b1l8ybf7dsbf')
        self.assertTrue(url, expected)

        # Clean up and completely delete the layer
        uploaded.delete()

    def testNoLinkForVector(self):
        thefile = os.path.join(
            gisdata.VECTOR_DATA,
            "san_andres_y_providencia_poi.shp")
        uploaded = file_upload(thefile, overwrite=True)
        access_token = None
        created = geotiffio.create_geotiff_io_url(uploaded, access_token)
        self.assertEqual(created, None)

        # Clean up and completely delete the layer
        uploaded.delete()

    def testNoAccessToken(self):
        thefile = os.path.join(gisdata.RASTER_DATA, 'test_grid.tif')
        uploaded = file_upload(thefile, overwrite=True)
        access_token = None

        # changing settings for this test
        geotiffio.settings.GEOTIFF_IO_ENABLED = True
        geotiffio.settings.GEOTIFF_IO_BASE_URL = "http://app.geotiff.io"

        url = geotiffio.create_geotiff_io_url(uploaded, access_token)
        expected = (
            'http://app.geotiff.io?url='
            'http%3A//localhost%3A8000/gs/wcs%3F'
            'service%3DWCS'
            '%26format%3Dimage%252Ftiff'
            '%26request%3DGetCoverage'
            '%26srs%3DEPSG%253A4326'
            '%26version%3D2.0.1'
            '%26coverageid%3Dgeonode%253Atest_grid')
        self.assertTrue(url, expected)

        # Clean up and completely delete the layer
        uploaded.delete()
