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
import time
import gisdata
import logging
import datetime

from io import BytesIO
from decimal import Decimal
from tastypie.test import ResourceTestCaseMixin

from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test.utils import override_settings
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.staticfiles.templatetags import staticfiles

from geonode.layers.utils import (
    upload,
    file_upload,
)
from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.utils import check_ogc_backend
from geonode.decorators import on_ogc_backend
from geonode.base.populate_test_data import all_public
from geonode.qgis_server.models import QGISServerLayer
from geonode.geoserver.signals import gs_catalog
from geonode.geoserver.helpers import cascading_delete
from geonode.tests.utils import check_layer, get_web_page
from geonode import GeoNodeException, geoserver, qgis_server

from contextlib import closing
from zipfile import ZipFile, ZIP_DEFLATED

LOCAL_TIMEOUT = 300

LOGIN_URL = "/accounts/login/"

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


def zip_dir(basedir, archivename):
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED, allowZip64=True)) as z:
        for root, dirs, files in os.walk(basedir):
            # NOTE: ignore empty directories
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(basedir) + len(os.sep):]  # XXX: relative path
                z.write(absfn, zfn)


r"""
 HOW TO RUN THE TESTS
 --------------------

 1)
  (http://docs.geonode.org/en/2.10.x/install/core/index.html?highlight=paver#run-geonode-for-the-first-time-in-debug-mode)

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


@override_settings(SITEURL='http://localhost:8001/')
class NormalUserTest(GeoNodeLiveTestSupport):

    """
    Tests GeoNode functionality for non-administrative users
    """
    port = 8001

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
            self.assertEqual(r.status_code, 200)
            o = json.loads(r.text)
            self.assertTrue('long-array-array' in o)

            from geonode.geoserver.helpers import (get_sld_for,
                                                   fixup_style,
                                                   set_layer_style,
                                                   get_store,
                                                   set_attributes_from_geoserver,
                                                   set_styles,
                                                   create_gs_thumbnail)

            _log("0. ------------ %s " % saved_layer)
            self.assertIsNotNone(saved_layer)
            workspace, name = saved_layer.alternate.split(':')
            self.assertIsNotNone(workspace)
            self.assertIsNotNone(name)
            ws = gs_catalog.get_workspace(workspace)
            self.assertIsNotNone(ws)
            store = get_store(gs_catalog, saved_layer.store, workspace=ws)
            _log("1. ------------ %s " % store)
            self.assertIsNotNone(store)

            # Save layer attributes
            set_attributes_from_geoserver(saved_layer)

            # Save layer styles
            set_styles(saved_layer, gs_catalog)

            # set SLD
            sld = saved_layer.default_style.sld_body if saved_layer.default_style else None
            self.assertIsNotNone(sld)
            _log("2. ------------ %s " % sld)
            set_layer_style(saved_layer, saved_layer.alternate, sld)

            fixup_style(gs_catalog, saved_layer.alternate, None)
            self.assertIsNotNone(get_sld_for(gs_catalog, saved_layer))
            _log("3. ------------ %s " % get_sld_for(gs_catalog, saved_layer))

            create_gs_thumbnail(saved_layer, overwrite=True)
            _log(saved_layer.get_thumbnail_url())
            _log(saved_layer.has_thumbnail())
        try:
            saved_layer.set_default_permissions()
            url = reverse('layer_metadata', args=[saved_layer.service_typename])
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
        finally:
            # Clean up and completely delete the layer
            saved_layer.delete()
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                from geonode.geoserver.helpers import cleanup
                cleanup(saved_layer.name, saved_layer.uuid)


@override_settings(SITEURL='http://localhost:8002/')
class GeoNodeMapTest(GeoNodeLiveTestSupport):

    """
    Tests geonode.maps app/module
    """
    port = 8002

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
        with self.assertRaisesRegex(Exception, "You are attempting to replace "
                                    "a vector layer with an unknown format."):
            file_upload(sampletxt)

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
                    self.assertEqual((today.day, today.month, today.year),
                                     (todoc.day, todoc.month, todoc.year),
                                     "Expected specific date from uploaded layer XML metadata")

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
                    self.assertEqual(uploaded.title, 'Zhejiang Yangcan Yanyu')
                    self.assertEqual(len(uploaded.keyword_list()), 2)
                    self.assertEqual(uploaded.constraints_other, None)
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
                    self.assertEqual(uploaded.title, 'Ming Female 1')
                    self.assertEqual(len(uploaded.keyword_list()), 2)
                    self.assertEqual(uploaded.constraints_other, None)
        finally:
            # Clean up and completely delete the layer
            if uploaded:
                uploaded.delete()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_zip_with_spaces(self):
        """Test uploading a layer with non UTF-8 attributes names"""
        uploaded = None
        PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        thelayer_path = os.path.join(
            PROJECT_ROOT,
            'data/UNESCO Global Geoparks')
        thelayer_zip = os.path.join(
            PROJECT_ROOT,
            'data/',
            'UNESCO Global Geoparks.zip')
        try:
            if os.path.exists(thelayer_zip):
                os.remove(thelayer_zip)
            if os.path.exists(thelayer_path) and not os.path.exists(thelayer_zip):
                zip_dir(thelayer_path, thelayer_zip)
                if os.path.exists(thelayer_zip):
                    uploaded = file_upload(thelayer_zip, overwrite=True, charset='UTF-8')
                    self.assertEqual(uploaded.title, 'Unesco Global Geoparks')
                    self.assertEqual(len(uploaded.keyword_list()), 2)
                    self.assertEqual(uploaded.constraints_other, None)
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
        self.assertIsNone(gs_cat.get_resource(
            name=shp_layer.name,
            store=tif_store,
            workspace=ws)
        )

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
            self.assertEqual(resp.status_code, 200)
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
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['is_featuretype'], False)

            # test the program can determine the original layer in vector type
            vector_replace_url = reverse(
                'layer_replace', args=[
                    vector_layer.service_typename])
            response = self.client.get(vector_replace_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['is_featuretype'], True)

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
            self.assertEqual(response.status_code, 400)
            response_dict = json.loads(response.content)
            self.assertEqual(response_dict['success'], False)

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
                pass
            else:
                self.assertEqual(response.status_code, 400)
                self.assertEqual(response_dict['success'], False)

            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                # test replace a vector with an updated version of the vector file
                new_vector_file = os.path.join(
                    gisdata.VECTOR_DATA,
                    'san_andres_y_providencia_administrative.shp')
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
                    pass
                else:
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response_dict['success'], True)
                    # Get a Layer object for the newly created layer.
                    new_vector_layer = Layer.objects.get(pk=vector_layer.pk)

                    # Test the replaced layer metadata is equal to the original layer
                    self.assertEqual(vector_layer.name, new_vector_layer.name)
                    self.assertEqual(vector_layer.title, new_vector_layer.title)
                    self.assertEqual(vector_layer.alternate, new_vector_layer.alternate)

                    # Test the replaced layer bbox is indeed different from the original layer
                    self.assertEqual(vector_layer.bbox_x0, new_vector_layer.bbox_x0)
                    self.assertEqual(vector_layer.bbox_x1, new_vector_layer.bbox_x1)
                    self.assertEqual(vector_layer.bbox_y0, new_vector_layer.bbox_y0)
                    self.assertEqual(vector_layer.bbox_y1, new_vector_layer.bbox_y1)

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
                    self.assertTrue(response.status_code in (401, 403))
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


@override_settings(SITEURL='http://localhost:8003/')
class GeoNodeThumbnailTest(GeoNodeLiveTestSupport):

    """
    Tests thumbnails behavior for layers and maps.
    """
    port = 8003

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
            if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
                self.assertEqual(thumbnail_url, staticfiles.static(settings.MISSING_THUMBNAIL))
        finally:
            # Cleanup
            saved_layer.delete()


@override_settings(SITEURL='http://localhost:8005/')
class LayersStylesApiInteractionTests(
        ResourceTestCaseMixin, GeoNodeLiveTestSupport):

    """Test Layers"""
    port = 8005

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
    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
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

        if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            style_stream = BytesIO(style_body)
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
            self.assertTrue(resp.status_code in [403, 405])

            # Login using anonymous user
            self.client.login(username='AnonymousUser')
            style_stream.seek(0)
            resp = self.client.post(style_list_url, data=data)
            # Should not be able to add style without correct permission
            self.assertTrue(resp.status_code in [403, 405])
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

        self.assertEqual(len(objects), 1)

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

        # check new default_style
        resp = self.api_client.get(layer_detail_url)
        self.assertValidJSONResponse(resp)
        obj = self.deserialize(resp)
        self.assertIsNotNone(obj['default_style'])

        if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
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
