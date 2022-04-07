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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from uuid import uuid4
from collections import namedtuple

from django.test.client import RequestFactory
from geonode.layers.metadata import convert_keyword, set_metadata, parse_metadata

from geonode.tests.base import GeoNodeBaseTestSupport
from django.test import TestCase
import io
import os
import shutil
import gisdata
import logging
import zipfile
import tempfile

from unittest.mock import patch
from pinax.ratings.models import OverallRating

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.gis.geos import Polygon
from django.db.models import Count
from django.contrib.auth import get_user_model

from django.conf import settings
from django.test.utils import override_settings
from django.contrib.admin.sites import AdminSite

from geonode.layers.admin import LayerAdmin
from guardian.shortcuts import get_anonymous_user
from guardian.shortcuts import assign_perm, remove_perm

from geonode import GeoNodeException, geoserver
from geonode.decorators import on_ogc_backend
from geonode.layers.models import Layer, Style, Attribute
from geonode.layers.utils import (
    is_sld_upload_only,
    is_xml_upload_only,
    layer_type,
    get_files,
    get_valid_name,
    get_valid_layer_name,
    surrogate_escape_string, validate_input_source)
from geonode.people.utils import get_valid_user
from geonode.base.populate_test_data import all_public, create_single_layer
from geonode.base.models import TopicCategory, License, Region, Link
from geonode.layers.forms import JSONField, LayerForm, LayerUploadForm
from geonode.utils import check_ogc_backend, set_resource_default_links
from geonode.layers import LayersAppConfig
from geonode.tests.utils import NotificationsTestsHelper
from geonode.layers.populate_layers_data import create_layer_data
from geonode.layers import utils
from geonode.layers.views import _resolve_layer
from geonode.maps.models import Map, MapLayer
from geonode.utils import DisableDjangoSignals
from geonode.maps.tests_populate_maplayers import maplayers as ml
from geonode.security.utils import ResourceManager
from geonode.base.forms import BatchPermissionsForm

logger = logging.getLogger(__name__)


class LayersTest(GeoNodeBaseTestSupport):

    """Tests geonode.layers app/module
    """
    type = 'layer'

    def setUp(self):
        super().setUp()
        create_layer_data()
        self.user = 'admin'
        self.passwd = 'admin'
        self.anonymous_user = get_anonymous_user()

        site = AdminSite()
        self.admin = LayerAdmin(Layer, site)

        self.request_admin = RequestFactory().get('/admin')
        self.request_admin.user = get_user_model().objects.get(username='admin')

    # Admin Tests

    def test_admin_save_model(self):
        obj = Layer.objects.first()
        self.assertEqual(len(obj.keywords.all()), 2)
        form = self.admin.get_form(self.request_admin, obj=obj, change=True)
        self.admin.save_model(self.request_admin, obj, form, True)

    # Data Tests

    def test_data(self):
        '''/data/ -> Test accessing the data page'''
        response = self.client.get(reverse('layer_browse'))
        self.assertEqual(response.status_code, 200)

    def test_describe_data_2(self):
        '''/data/geonode:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(10, get_user_model().objects.all().count())
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.assertEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

    def test_describe_data_3(self):
        '''/data/geonode:CA/metadata_detail -> Test accessing the description of a layer '''
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Published", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Featured", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "<dt>Group</dt>", count=0, status_code=200, msg_prefix='', html=False)

        # ... now assigning a Group to the Layer
        lyr = Layer.objects.get(alternate='geonode:CA')
        group = Group.objects.first()
        lyr.group = group
        lyr.save()
        response = self.client.get(reverse('layer_metadata_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<dt>Group</dt>", count=1, status_code=200, msg_prefix='', html=False)
        lyr.group = None
        lyr.save()

    # Layer Tests

    def test_layer_name_clash(self):
        _ll_1 = Layer.objects.create(
            uuid=str(uuid4()),
            owner=get_user_model().objects.get(username=self.user),
            name='states',
            store='geonode_data',
            storeType="dataStore",
            alternate="geonode:states")
        _ll_2 = Layer.objects.create(
            uuid=str(uuid4()),
            owner=get_user_model().objects.get(username=self.user),
            name='geonode:states',
            store='httpfooremoteservce',
            storeType="remoteStore",
            alternate="geonode:states")
        _ll_1.set_permissions({'users': {"bobby": ['base.view_resourcebase']}})
        _ll_2.set_permissions({'users': {"bobby": ['base.view_resourcebase']}})
        self.client.login(username="bobby", password="bob")
        _request = self.client.request()
        _request.user = get_user_model().objects.get(username="bobby")
        _ll = _resolve_layer(_request, alternate="geonode:states")
        self.assertIsNotNone(_ll)
        self.assertEqual(_ll.name, _ll_1.name)

    # Test layer upload endpoint
    def test_upload_layer(self):
        # Test redirection to login form when not logged in
        response = self.client.get(reverse('layer_upload'))
        self.assertEqual(response.status_code, 302)

        # Test return of upload form when logged in
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse('layer_upload'))
        self.assertEqual(response.status_code, 200)

    def test_describe_data(self):
        '''/data/geonode:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(10, get_user_model().objects.all().count())
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.assertEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

    def test_layer_attributes(self):
        lyr = Layer.objects.all().first()
        # There should be a total of 3 attributes
        self.assertEqual(len(lyr.attribute_set.all()), 4)
        # 2 out of 3 attributes should be visible
        custom_attributes = lyr.attribute_set.visible()
        self.assertEqual(len(custom_attributes), 3)
        # place_ name should come before description
        self.assertEqual(custom_attributes[0].attribute_label, "Place Name")
        self.assertEqual(custom_attributes[1].attribute_label, "Description")
        self.assertEqual(
            custom_attributes[2].attribute,
            'N\xfamero_De_M\xe9dicos')
        # TODO: do test against layer with actual attribute statistics
        self.assertEqual(custom_attributes[1].count, 1)
        self.assertEqual(custom_attributes[1].min, "NA")
        self.assertEqual(custom_attributes[1].max, "NA")
        self.assertEqual(custom_attributes[1].average, "NA")
        self.assertEqual(custom_attributes[1].median, "NA")
        self.assertEqual(custom_attributes[1].stddev, "NA")
        self.assertEqual(custom_attributes[1].sum, "NA")
        self.assertEqual(custom_attributes[1].unique_values, "NA")

    def test_layer_bbox(self):
        lyr = Layer.objects.all().first()
        layer_bbox = lyr.bbox[0:4]
        logger.debug(layer_bbox)

        def decimal_encode(bbox):
            _bbox = [float(o) for o in bbox]
            # Must be in the form : [x0, x1, y0, y1
            return [_bbox[0], _bbox[2], _bbox[1], _bbox[3]]

        from geonode.utils import bbox_to_projection
        projected_bbox = decimal_encode(
            bbox_to_projection([float(coord) for coord in layer_bbox] + [lyr.srid, ],
                               target_srid=4326)[:4])
        logger.debug(projected_bbox)
        self.assertEqual(projected_bbox, [-180.0, -90.0, 180.0, 90.0])
        logger.debug(lyr.ll_bbox)
        self.assertEqual(lyr.ll_bbox, [-180.0, 180.0, -90.0, 90.0, 'EPSG:4326'])
        projected_bbox = decimal_encode(
            bbox_to_projection([float(coord) for coord in layer_bbox] + [lyr.srid, ],
                               target_srid=3857)[:4])
        solution = [-20037397.023298454, -74299743.40065672,
                    20037397.02329845, 74299743.40061197]
        logger.debug(projected_bbox)
        for coord, check in zip(projected_bbox, solution):
            self.assertAlmostEqual(coord, check, places=3)

    def test_layer_attributes_feature_catalogue(self):
        """ Test layer feature catalogue functionality
        """
        self.assertTrue(self.client.login(username='admin', password='admin'))
        # test a non-existing layer
        url = reverse('layer_feature_catalogue', args=('bad_layer',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Get the layer to work with
        layer = Layer.objects.all()[3]
        url = reverse('layer_feature_catalogue', args=(layer.alternate,))
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_layer_attribute_config(self):
        lyr = Layer.objects.all().first()
        attribute_config = lyr.attribute_config()
        custom_attributes = attribute_config["getFeatureInfo"]
        self.assertEqual(
            custom_attributes["fields"], [
                "place_name", "description", 'N\xfamero_De_M\xe9dicos'])
        self.assertEqual(
            custom_attributes["propertyNames"]["description"],
            "Description")
        self.assertEqual(
            custom_attributes["propertyNames"]["place_name"],
            "Place Name")

        attributes = Attribute.objects.filter(layer=lyr)
        for _att in attributes:
            self.assertEqual(_att.featureinfo_type, 'type_property')

        lyr.featureinfo_custom_template = "<h1>Test HTML</h1>"
        lyr.use_featureinfo_custom_template = True
        lyr.save()
        attribute_config = lyr.attribute_config()
        self.assertTrue("ftInfoTemplate" in attribute_config)
        self.assertEqual(
            attribute_config["ftInfoTemplate"],
            "<h1>Test HTML</h1>")
        lyr.use_featureinfo_custom_template = False
        lyr.save()
        attribute_config = lyr.attribute_config()
        self.assertTrue("ftInfoTemplate" not in attribute_config)

    def test_layer_styles(self):
        lyr = Layer.objects.all().first()
        # There should be a total of 3 styles
        self.assertEqual(len(lyr.styles.all()), 4)
        # One of the style is the default one
        self.assertEqual(
            lyr.default_style,
            Style.objects.get(
                id=lyr.default_style.id))

        try:
            [str(style) for style in lyr.styles.all()]
        except UnicodeEncodeError:
            self.fail(
                "str of the Style model throws a UnicodeEncodeError with special characters.")

    def test_layer_save(self):
        lyr = Layer.objects.all().first()
        lyr.keywords.add(*["saving", "keywords"])
        lyr.save()
        self.assertEqual(
            set(lyr.keyword_list()), {
                'here', 'keywords', 'populartag', 'saving'})

        # Test exotic encoding Keywords
        lyr.keywords.add(*['論語', 'ä', 'ö', 'ü', 'ß'])
        lyr.save()
        self.assertEqual(
            set(lyr.keyword_list()), {
                'here', 'keywords', 'populartag', 'saving',
                'ß', 'ä', 'ö', 'ü', '論語'})

        # Test input escape
        lyr.keywords.add(*["Europe<script>true;</script>",
                           "land_<script>true;</script>covering",
                           "<IMG SRC='javascript:true;'>Science"])

        self.assertEqual(
            set(lyr.keyword_list()), {
                '&lt;IMG SRC=&#39;javascript:true;&#39;&gt;Science', 'Europe&lt;script&gt;true;&lt;/script&gt;',
                'here', 'keywords', 'land_&lt;script&gt;true;&lt;/script&gt;covering', 'populartag', 'saving',
                'ß', 'ä', 'ö', 'ü', '論語'})

        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('layer_detail', args=(lyr.alternate,)))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('layer_detail', args=(f":{lyr.alternate}",)))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse('layer_metadata', args=(lyr.alternate,)))
        self.assertEqual(response.status_code, 200)

        from geonode.base.models import HierarchicalKeyword as hk
        keywords = hk.resource_keywords_tree(get_user_model().objects.get(username='admin'), resource_type='layer')

        self.assertEqual(len(keywords), 13)

    def test_layer_links(self):
        lyr = Layer.objects.filter(storeType="dataStore").first()
        self.assertEqual(lyr.storeType, "dataStore")
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            _def_link_types = (
                'data', 'image', 'original', 'html', 'OGC:WMS', 'OGC:WFS', 'OGC:WCS')
            Link.objects.filter(resource=lyr.resourcebase_ptr, link_type__in=_def_link_types).delete()
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            set_resource_default_links(lyr, lyr)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="image")
            self.assertIsNotNone(links)

        lyr = Layer.objects.filter(storeType="coverageStore").first()
        self.assertEqual(lyr.storeType, "coverageStore")
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            _def_link_types = (
                'data', 'image', 'original', 'html', 'OGC:WMS', 'OGC:WFS', 'OGC:WCS')
            Link.objects.filter(resource=lyr.resourcebase_ptr, link_type__in=_def_link_types).delete()
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            set_resource_default_links(lyr, lyr)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            for ll in links:
                self.assertEqual(ll.link_type, "metadata")

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="data")
            self.assertIsNotNone(links)

            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="image")
            self.assertIsNotNone(links)

    def test_get_valid_user(self):
        # Verify it accepts an admin user
        adminuser = get_user_model().objects.get(is_superuser=True)
        valid_user = get_valid_user(adminuser)
        msg = (f'Passed in a valid admin user "{adminuser}" but got "{valid_user}" in return')
        assert valid_user.id == adminuser.id, msg

        # Verify it returns a valid user after receiving None
        valid_user = get_valid_user(None)
        msg = f'Expected valid user after passing None, got "{valid_user}"'
        assert isinstance(valid_user, get_user_model()), msg

        newuser = get_user_model().objects.create(username='arieluser')
        valid_user = get_valid_user(newuser)
        msg = (f'Passed in a valid user "{newuser}" but got "{valid_user}" in return')
        assert valid_user.id == newuser.id, msg

        valid_user = get_valid_user('arieluser')
        msg = ('Passed in a valid user by username "arieluser" but got'
               f' "{valid_user}" in return')
        assert valid_user.username == 'arieluser', msg

        nn = get_anonymous_user()
        self.assertRaises(GeoNodeException, get_valid_user, nn)

    def testShapefileValidation(self):
        files = dict(
            base_file=SimpleUploadedFile('foo.shp', b' '),
            shx_file=SimpleUploadedFile('foo.shx', b' '),
            dbf_file=SimpleUploadedFile('foo.dbf', b' '),
            prj_file=SimpleUploadedFile('foo.prj', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', b' '),
            shx_file=SimpleUploadedFile('foo.SHX', b' '),
            dbf_file=SimpleUploadedFile('foo.DBF', b' '),
            prj_file=SimpleUploadedFile('foo.PRJ', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', b' '),
            shx_file=SimpleUploadedFile('foo.shx', b' '),
            dbf_file=SimpleUploadedFile('foo.dbf', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', b' '),
            shx_file=SimpleUploadedFile('foo.shx', b' '),
            dbf_file=SimpleUploadedFile('foo.dbf', b' '),
            prj_file=SimpleUploadedFile('foo.PRJ', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.SHP', b' '),
            shx_file=SimpleUploadedFile('bar.shx', b' '),
            dbf_file=SimpleUploadedFile('bar.dbf', b' '),
            prj_file=SimpleUploadedFile('bar.PRJ', b' '))
        self.assertFalse(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.shp', b' '),
            dbf_file=SimpleUploadedFile('foo.dbf', b' '),
            prj_file=SimpleUploadedFile('foo.PRJ', b' '))
        self.assertFalse(LayerUploadForm(dict(), files).is_valid())

        files = dict(
            base_file=SimpleUploadedFile('foo.txt', b' '),
            shx_file=SimpleUploadedFile('foo.shx', b' '),
            dbf_file=SimpleUploadedFile('foo.sld', b' '),
            prj_file=SimpleUploadedFile('foo.prj', b' '))
        self.assertFalse(LayerUploadForm(dict(), files).is_valid())

    def testGeoTiffValidation(self):
        files = dict(base_file=SimpleUploadedFile('foo.tif', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.TIF', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.tiff', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.TIF', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.geotif', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.GEOTIF', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.geotiff', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.GEOTIF', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

    def testASCIIValidation(self):
        files = dict(base_file=SimpleUploadedFile('foo.asc', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.ASC', b' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

    def testZipValidation(self):
        the_zip = zipfile.ZipFile('test_upload.zip', 'w')
        in_memory_file = io.StringIO()
        in_memory_file.write('test')
        the_zip.writestr('foo.shp', in_memory_file.getvalue())
        the_zip.writestr('foo.dbf', in_memory_file.getvalue())
        the_zip.writestr('foo.shx', in_memory_file.getvalue())
        the_zip.writestr('foo.prj', in_memory_file.getvalue())
        the_zip.close()
        files = dict(base_file=SimpleUploadedFile('test_upload.zip',
                                                  open('test_upload.zip', mode='rb').read()))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())
        os.remove('test_upload.zip')

    def testWriteFiles(self):
        files = dict(
            base_file=SimpleUploadedFile('foo.shp', b' '),
            shx_file=SimpleUploadedFile('foo.shx', b' '),
            dbf_file=SimpleUploadedFile('foo.dbf', b' '),
            prj_file=SimpleUploadedFile('foo.prj', b' '))
        form = LayerUploadForm(dict(), files)
        self.assertTrue(form.is_valid())

        tempdir = form.write_files()[0]
        self.assertEqual(set(os.listdir(tempdir)),
                         {'foo.shp', 'foo.shx', 'foo.dbf', 'foo.prj'})

        the_zip = zipfile.ZipFile('test_upload.zip', 'w')
        in_memory_file = io.StringIO()
        in_memory_file.write('test')
        the_zip.writestr('foo.shp', in_memory_file.getvalue())
        the_zip.writestr('foo.dbf', in_memory_file.getvalue())
        the_zip.writestr('foo.shx', in_memory_file.getvalue())
        the_zip.writestr('foo.prj', in_memory_file.getvalue())
        the_zip.close()
        files = dict(base_file=SimpleUploadedFile('test_upload.zip',
                                                  open('test_upload.zip', mode='rb').read()))
        form = LayerUploadForm(dict(), files)
        self.assertTrue(form.is_valid())
        tempdir = form.write_files()[0]
        self.assertEqual(set(os.listdir(tempdir)),
                         {'foo.shp', 'foo.shx', 'foo.dbf', 'foo.prj'})
        os.remove('test_upload.zip')

    def test_layer_type(self):
        self.assertEqual(layer_type('foo.shp'), 'vector')
        self.assertEqual(layer_type('foo.SHP'), 'vector')
        self.assertEqual(layer_type('foo.sHp'), 'vector')
        self.assertEqual(layer_type('foo.tif'), 'raster')
        self.assertEqual(layer_type('foo.TIF'), 'raster')
        self.assertEqual(layer_type('foo.TiF'), 'raster')
        self.assertEqual(layer_type('foo.geotif'), 'raster')
        self.assertEqual(layer_type('foo.GEOTIF'), 'raster')
        self.assertEqual(layer_type('foo.gEoTiF'), 'raster')
        self.assertEqual(layer_type('foo.tiff'), 'raster')
        self.assertEqual(layer_type('foo.TIFF'), 'raster')
        self.assertEqual(layer_type('foo.TiFf'), 'raster')
        self.assertEqual(layer_type('foo.geotiff'), 'raster')
        self.assertEqual(layer_type('foo.GEOTIFF'), 'raster')
        self.assertEqual(layer_type('foo.gEoTiFf'), 'raster')
        self.assertEqual(layer_type('foo.asc'), 'raster')
        self.assertEqual(layer_type('foo.ASC'), 'raster')
        self.assertEqual(layer_type('foo.AsC'), 'raster')

        # basically anything else should produce a GeoNodeException
        self.assertRaises(GeoNodeException, lambda: layer_type('foo.gml'))

    def test_get_files(self):
        def generate_files(*extensions):
            if extensions[0].lower() != 'shp':
                return
            d = None
            expected_files = None
            try:
                d = tempfile.mkdtemp()
                fnames = [f"foo.{ext}" for ext in extensions]
                expected_files = {ext.lower(): fname for ext, fname in zip(extensions, fnames)}
                for f in fnames:
                    path = os.path.join(d, f)
                    # open and immediately close to create empty file
                    open(path, 'w').close()
            finally:
                return d, expected_files

        # Check that a well-formed Shapefile has its components all picked up
        d = None
        _tmpdir = None
        try:
            d, expected_files = generate_files("shp", "shx", "prj", "dbf")
            gotten_files, _tmpdir = get_files(os.path.join(d, "foo.shp"))
            gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
            self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that a Shapefile missing required components raises an
        # exception
        d = None
        try:
            d, expected_files = generate_files("shp", "shx", "prj")
            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

        # Check that including an SLD with a valid shapefile results in the SLD
        # getting picked up
        d = None
        _tmpdir = None
        try:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                d, expected_files = generate_files("shp", "shx", "prj", "dbf", "sld")
                gotten_files, _tmpdir = get_files(os.path.join(d, "foo.shp"))
                gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
                self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that capitalized extensions are ok
        d = None
        _tmpdir = None
        try:
            d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF")
            gotten_files, _tmpdir = get_files(os.path.join(d, "foo.SHP"))
            gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
            self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that mixed capital and lowercase extensions are ok
        d = None
        _tmpdir = None
        try:
            d, expected_files = generate_files("SHP", "shx", "pRJ", "DBF")
            gotten_files, _tmpdir = get_files(os.path.join(d, "foo.SHP"))
            gotten_files = {k: os.path.basename(v) for k, v in gotten_files.items()}
            self.assertEqual(gotten_files, expected_files)
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)
            if _tmpdir is not None:
                shutil.rmtree(_tmpdir, ignore_errors=True)

        # Check that including both capital and lowercase extensions raises an
        # exception
        d = None
        try:
            d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF", "shp", "shx", "prj", "dbf")

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(expected_files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

        # Check that including both capital and lowercase PRJ (this is
        # special-cased in the implementation)
        d = None
        try:
            d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF", "prj")

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(expected_files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

        # Check that including both capital and lowercase SLD (this is
        # special-cased in the implementation)
        d = None
        try:
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                d, expected_files = generate_files("SHP", "SHX", "PRJ", "DBF", "SLD", "sld")

                # Only run the tests if this is a case sensitive OS
                if len(os.listdir(d)) == len(expected_files):
                    self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                    self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d, ignore_errors=True)

    def test_get_valid_name(self):
        self.assertEqual(get_valid_name("blug"), "blug")
        self.assertEqual(get_valid_name("<-->"), "_")
        self.assertEqual(get_valid_name("<ab>"), "_ab_")
        self.assertNotEqual(get_valid_name("CA"), "CA_1")
        self.assertNotEqual(get_valid_name("CA"), "CA_1")

    def test_get_valid_layer_name(self):
        self.assertEqual(get_valid_layer_name("blug", False), "blug")
        self.assertEqual(get_valid_layer_name("blug", True), "blug")

        self.assertEqual(get_valid_layer_name("<ab>", False), "_ab_")
        self.assertEqual(get_valid_layer_name("<ab>", True), "<ab>")

        self.assertEqual(get_valid_layer_name("<-->", False), "_")
        self.assertEqual(get_valid_layer_name("<-->", True), "<-->")

        self.assertNotEqual(get_valid_layer_name("CA", False), "CA_1")
        self.assertNotEqual(get_valid_layer_name("CA", False), "CA_1")
        self.assertEqual(get_valid_layer_name("CA", True), "CA")
        self.assertEqual(get_valid_layer_name("CA", True), "CA")

        layer = Layer.objects.get(name="CA")
        self.assertNotEqual(get_valid_layer_name(layer, False), "CA_1")
        self.assertEqual(get_valid_layer_name(layer, True), "CA")

        self.assertRaises(GeoNodeException, get_valid_layer_name, 12, False)
        self.assertRaises(GeoNodeException, get_valid_layer_name, 12, True)

    # NOTE: we don't care about file content for many of these tests (the
    # forms under test validate based only on file name, and leave actual
    # content inspection to GeoServer) but Django's form validation will omit
    # any files with empty bodies.
    #
    # That is, this leads to mysterious test failures:
    #     SimpleUploadedFile('foo', ' '.encode("UTF-8"))
    #
    # And this should be used instead to avoid that:
    #     SimpleUploadedFile('foo', ' '.encode("UTF-8"))

    def testJSONField(self):
        field = JSONField()
        # a valid JSON document should pass
        field.clean('{ "users": [] }')

        # text which is not JSON should fail
        self.assertRaises(
            ValidationError,
            lambda: field.clean('<users></users>'))

    def test_rating_layer_remove(self):
        """ Test layer rating is removed on layer remove
        """
        # Get the layer to work with
        layer = Layer.objects.all()[3]
        layer_id = layer.id
        # Create the rating with the correct content type
        ctype = ContentType.objects.get(model='layer')
        OverallRating.objects.create(
            category=2,
            object_id=layer_id,
            content_type=ctype,
            rating=3)
        rating = OverallRating.objects.all()
        self.assertEqual(rating.count(), 1)
        # Remove the layer
        layer.delete()
        # Check there are no ratings matching the remove layer
        rating = OverallRating.objects.all()
        self.assertEqual(rating.count(), 0)

    def test_sld_upload(self):
        """Test layer remove functionality
        """
        layer = Layer.objects.all().first()
        url = reverse('layer_sld_upload', args=(layer.alternate,))
        # Now test with a valid user
        self.client.login(username='admin', password='admin')

        # test a method other than POST and GET
        response = self.client.put(url)
        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertFalse("#modal_perms" in content)

    def test_layer_export(self):
        """Test export layer view
        """
        layer = Layer.objects.all().first()
        url = reverse('layer_export', args=(layer.alternate,))
        response = self.client.get(url)
        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertFalse("Export Data" in content)
        # Now test with a logged-in user
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertFalse("Export Data" in content)

    def test_layer_remove(self):
        """Test layer remove functionality
        """
        layer = Layer.objects.all().first()
        url = reverse('layer_remove', args=(layer.alternate,))

        # test unauthenticated
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # test a user without layer removal permission
        self.client.login(username='norman', password='norman')
        response = self.client.post(url)
        self.assertTrue(response.status_code in (401, 403))
        self.client.logout()

        # Now test with a valid user
        self.client.login(username='admin', password='admin')

        # test a method other than POST and GET
        response = self.client.put(url)
        self.assertTrue(response.status_code in (401, 403))

        # test the page with a valid user with layer removal permission
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # test the post method that actually removes the layer and redirects
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/layers/' in response['Location'])

        # test that the layer is actually removed
        self.assertEqual(Layer.objects.filter(pk=layer.pk).count(), 0)

        # test that all styles associated to the layer are removed
        self.assertEqual(Style.objects.count(), 0)

    def test_non_cascading(self):
        """
        Tests that deleting a layer with a shared default style will not cascade and
        delete multiple layers.
        """
        layer1 = Layer.objects.all().first()
        layer2 = Layer.objects.all()[2]
        url = reverse('layer_remove', args=(layer1.alternate,))

        layer2.default_style = layer1.default_style
        layer2.save()

        self.assertEqual(layer1.default_style, layer2.default_style)

        # Now test with a valid user
        self.client.login(username='admin', password='admin')

        # test the post method that actually removes the layer and redirects
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/layers/' in response['Location'])

        # test that the layer is actually removed

        self.assertEqual(Layer.objects.filter(pk=layer1.pk).count(), 0)
        self.assertEqual(Layer.objects.filter(pk=layer2.pk).count(), 1)

        # test that all styles associated to the layer are removed
        self.assertEqual(Style.objects.count(), 1)

    def test_category_counts(self):
        topics = TopicCategory.objects.all()
        topics = topics.annotate(
            **{'layer_count': Count('resourcebase__layer__category')})
        location = topics.get(identifier='location')
        # there are three layers with location category
        self.assertEqual(location.layer_count, 3)

        # change the category of one layers_count
        layer = Layer.objects.filter(category=location)[0]
        elevation = topics.get(identifier='elevation')
        layer.category = elevation
        layer.save()

        # reload the categories since it's caching the old count
        topics = topics.annotate(
            **{'layer_count': Count('resourcebase__layer__category')})
        location = topics.get(identifier='location')
        elevation = topics.get(identifier='elevation')
        self.assertEqual(location.layer_count, 2)
        self.assertEqual(elevation.layer_count, 4)

        # delete a layer and check the count update
        # use the first since it's the only one which has styles
        layer = Layer.objects.all().first()
        elevation = topics.get(identifier='elevation')
        self.assertEqual(elevation.layer_count, 4)
        layer.delete()
        topics = topics.annotate(
            **{'layer_count': Count('resourcebase__layer__category')})
        elevation = topics.get(identifier='elevation')
        self.assertEqual(elevation.layer_count, 3)

    def test_assign_change_layer_data_perm(self):
        """
        Ensure set_permissions supports the change_layer_data permission.
        """
        layer = Layer.objects.filter(storeType='dataStore').first()
        user = get_user_model().objects.get(username='norman')
        layer.set_permissions({'users': {user: ['change_layer_data']}})
        perms = layer.get_all_level_info()
        self.assertIn('change_layer_data', perms['users'][user], perms['users'])

    def test_batch_edit(self):
        """
        Test batch editing of metadata fields.
        """
        Model = Layer
        view = 'layer_batch_metadata'
        resources = Model.objects.all()[:3]
        ids = ','.join(str(element.pk) for element in resources)
        # test non-admin access
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse(view))
        self.assertTrue(response.status_code in (401, 403))
        # test group change
        group = Group.objects.first()
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse(view),
            data={'group': group.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.group, group)
        # test owner change
        owner = get_user_model().objects.first()
        response = self.client.post(
            reverse(view),
            data={'owner': owner.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.owner, owner)
        # test license change
        license = License.objects.first()
        response = self.client.post(
            reverse(view),
            data={'license': license.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.license, license)
        # test regions change
        region = Region.objects.first()
        response = self.client.post(
            reverse(view),
            data={'region': region.pk, 'ids': ids, 'regions': 1},
        )
        self.assertEqual(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            if resource.regions.all():
                self.assertTrue(region in resource.regions.all())
        # test language change
        language = 'eng'
        response = self.client.post(
            reverse(view),
            data={'language': language, 'ids': ids, 'regions': 1},
        )
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEqual(resource.language, language)
        # test keywords change
        keywords = 'some,thing,new'
        response = self.client.post(
            reverse(view),
            data={'keywords': keywords, 'ids': ids, 'regions': 1},
        )
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            for word in resource.keywords.all():
                self.assertTrue(word.name in keywords.split(','))

    def test_batch_permissions(self):
        """
        Test batch editing of test_batch_permissions.
        """
        group = Group.objects.first()
        Model = Layer
        view = 'layer_batch_permissions'
        resources = Model.objects.all()[:3]
        ids = ','.join(str(element.pk) for element in resources)
        # test non-admin access
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(reverse(view), data={"ids": ids})
        self.assertTrue(response.status_code in (401, 403))
        # test group permissions
        self.assertTrue(self.client.login(username='admin', password='admin'))
        data = {
            'group': group.id,
            'permission_type': ['r', ],
            'mode': 'set',
            'ids': ids
        }
        form = BatchPermissionsForm(data=data)
        logger.debug(f" -- perm_spec[groups] --> BatchPermissionsForm errors: {form.errors}")
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.errors), 0)
        response = self.client.post(
            reverse(view),
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        utils.set_layers_permissions(
            'r',
            [resource.name for resource in Model.objects.filter(
                id__in=[int(_id) for _id in ids.split(",")])],
            [],
            [group.name, ],
            False,
            verbose=True
        )
        resources = Model.objects.filter(id__in=[int(_id) for _id in ids.split(",")])
        logger.debug(f" -- perm_spec[groups] --> Testing group {group}")
        for resource in resources:
            perm_spec = resource.get_all_level_info()
            logger.debug(f" -- perm_spec[groups] --> {perm_spec['groups']}")
            self.assertTrue(group in perm_spec["groups"])
        # test user permissions
        user = get_user_model().objects.first()
        data = {
            'user': user.id,
            'permission_type': ['r', ],
            'mode': 'set',
            'ids': ids
        }
        form = BatchPermissionsForm(data=data)
        logger.debug(f" -- perm_spec[users] --> BatchPermissionsForm errors: {form.errors}")
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.errors), 0)
        response = self.client.post(
            reverse(view),
            data=data,
        )
        self.assertEqual(response.status_code, 302)
        utils.set_layers_permissions(
            'r',
            [resource.name for resource in Model.objects.filter(
                id__in=[int(_id) for _id in ids.split(",")])],
            [user.username, ],
            [],
            False,
            verbose=True
        )
        resources = Model.objects.filter(id__in=[int(_id) for _id in ids.split(",")])
        logger.debug(f" -- perm_spec[users] --> Testing user {user}")
        for resource in resources:
            perm_spec = resource.get_all_level_info()
            logger.debug(f" -- perm_spec[users] --> {perm_spec['users']}")
            self.assertFalse(user in perm_spec["users"])

    def test_surrogate_escape_string(self):
        surrogate_escape_raw = "Zo\udcc3\udcab"
        surrogate_escape_expected = "Zoë"
        surrogate_escape_result = surrogate_escape_string(
            surrogate_escape_raw, 'UTF-8')  # add more test cases using different charsets?
        self.assertEqual(
            surrogate_escape_result,
            surrogate_escape_expected,
            "layers.utils.surrogate_escape_string did not produce expected result. "
            f"Expected {surrogate_escape_expected}, received {surrogate_escape_result}")


class UnpublishedObjectTests(GeoNodeBaseTestSupport):

    """Test the is_published base attribute"""
    type = 'layer'

    def setUp(self):
        super().setUp()
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        all_public()

    def test_published_layer(self):
        """Test unpublished layer behaviour"""

        get_user_model().objects.get(username='bobby')
        self.client.login(username='bobby', password='bob')

        # default (RESOURCE_PUBLISHING=False)
        # access to layer detail page gives 200 if layer is published or
        # unpublished
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)
        layer = Layer.objects.filter(title='CA')[0]
        layer.is_published = False
        layer.save()
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    @override_settings(RESOURCE_PUBLISHING=True)
    def test_unpublished_layer(self):
        """With resource publishing"""
        layer = Layer.objects.filter(alternate='geonode:CA')[0]
        layer.is_published = False
        layer.save()

        user = get_user_model().objects.get(username='foo')
        self.client.login(username='foo', password='pass')
        # 404 if layer is unpublished
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

        # 404 if layer is unpublished but user has permission but does not belong to the group
        assign_perm('publish_resourcebase', user, layer.get_self_resource())
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

        # 200 if layer is unpublished and user is owner
        remove_perm('publish_resourcebase', user, layer.get_self_resource())
        layer.owner = user
        layer.save()
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

        # 200 if layer is published
        layer.is_published = True
        layer.save()

        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

        layer.is_published = True
        layer.save()


class LayerNotificationsTestCase(NotificationsTestsHelper):

    type = 'layer'

    def setUp(self):
        super().setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        create_layer_data()
        self.anonymous_user = get_anonymous_user()
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()
        self.setup_notifications_for(LayersAppConfig.NOTIFICATIONS, self.u)
        self.norman = get_user_model().objects.get(username='norman')
        self.norman.email = 'norman@email.com'
        self.norman.is_active = True
        self.norman.save()
        self.setup_notifications_for(LayersAppConfig.NOTIFICATIONS, self.norman)

    def testLayerNotifications(self):
        with self.settings(
                EMAIL_ENABLE=True,
                NOTIFICATION_ENABLED=True,
                NOTIFICATIONS_BACKEND="pinax.notifications.backends.email.EmailBackend",
                PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            self.clear_notifications_queue()
            self.client.login(username=self.user, password=self.passwd)
            _l = Layer.objects.create(
                uuid=str(uuid4()),
                name='test notifications',
                bbox_polygon=Polygon.from_bbox((-180, -90, 180, 90)),
                srid='EPSG:4326',
                owner=self.norman)
            self.assertTrue(self.check_notification_out('layer_created', self.u))
            # Ensure "resource.owner" won't be notified for having uploaded its own resource
            self.assertFalse(self.check_notification_out('layer_created', self.norman))

            self.clear_notifications_queue()
            _l.name = 'test notifications 2'
            _l.save(notify=True)
            self.assertTrue(self.check_notification_out('layer_updated', self.u))

            self.clear_notifications_queue()
            from dialogos.models import Comment
            lct = ContentType.objects.get_for_model(_l)
            comment = Comment(
                author=self.norman,
                name=self.u.username,
                content_type=lct,
                object_id=_l.id,
                content_object=_l,
                comment='test comment')
            comment.save()
            self.assertTrue(self.check_notification_out('layer_comment', self.u))

            self.clear_notifications_queue()
            if "pinax.ratings" in settings.INSTALLED_APPS:
                self.clear_notifications_queue()
                from pinax.ratings.models import Rating
                rating = Rating(
                    user=self.norman,
                    content_type=lct,
                    object_id=_l.id,
                    content_object=_l,
                    rating=5)
                rating.save()
                self.assertTrue(self.check_notification_out('layer_rated', self.u))


class SetLayersPermissions(GeoNodeBaseTestSupport):

    type = 'layer'

    def setUp(self):
        super().setUp()
        create_layer_data()
        self.username = 'test_username'
        self.passwd = 'test_password'
        self.user = get_user_model().objects.create(
            username=self.username
        )

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_assign_remove_permissions(self):
        # Assign
        layer = Layer.objects.filter(storeType='dataStore').first()
        perm_spec = layer.get_all_level_info()
        self.assertNotIn(self.user, perm_spec["users"])
        utils.set_layers_permissions("write", None, [self.user], None, None)
        layer_after = Layer.objects.get(name=layer.name)
        perm_spec = layer_after.get_all_level_info()
        for perm in utils.WRITE_PERMISSIONS:
            self.assertIn(perm, perm_spec["users"][self.user])
            _c = 0
            for _u in perm_spec["users"]:
                if _u == self.user:
                    _c += 1
            self.assertEqual(_c, 1)
        # Remove
        utils.set_layers_permissions("write", None, [self.user], None, True)
        layer_after = Layer.objects.get(name=layer.name)
        perm_spec = layer_after.get_all_level_info()
        for perm in utils.WRITE_PERMISSIONS:
            if self.user in perm_spec["users"]:
                self.assertNotIn(perm, perm_spec["users"][self.user])


class LayersUploaderTests(GeoNodeBaseTestSupport):

    GEONODE_REST_UPLOADER = {
        'BACKEND': 'geonode.rest',
        'OPTIONS': {
            'TIME_ENABLED': True,
            'MOSAIC_ENABLED': False,
            'GEOGIG_ENABLED': False,
        },
        'SUPPORTED_CRS': [
            'EPSG:4326',
            'EPSG:3785',
            'EPSG:3857',
            'EPSG:32647',
            'EPSG:32736'
        ],
        'SUPPORTED_EXT': [
            '.shp',
            '.csv',
            '.kml',
            '.kmz',
            '.json',
            '.geojson',
            '.tif',
            '.tiff',
            '.geotiff',
            '.gml',
            '.xml'
        ]
    }

    def setUp(self):
        super().setUp()
        create_layer_data()
        self.user = 'admin'
        self.passwd = 'admin'
        self.anonymous_user = get_anonymous_user()


class TestLayerDetailMapViewRights(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        create_layer_data()
        self.user = get_user_model().objects.create(username='dybala', email='dybala@gmail.com')
        self.user.set_password('very-secret')
        admin = get_user_model().objects.get(username='admin')
        self.map = Map.objects.create(uuid=str(uuid4()), owner=admin, title='test', is_approved=True, zoom=0, center_x=0.0, center_y=0.0)
        self.not_admin = get_user_model().objects.create(username='r-lukaku', is_active=True)
        self.not_admin.set_password('very-secret')
        self.not_admin.save()

        self.layer = Layer.objects.all().first()
        with DisableDjangoSignals():
            self.map_layer = MapLayer.objects.create(
                fixed=ml[0]['fixed'],
                group=ml[0]['group'],
                name=self.layer.alternate,
                layer_params=ml[0]['layer_params'],
                map=self.map,
                source_params=ml[0]['source_params'],
                stack_order=ml[0]['stack_order'],
                opacity=ml[0]['opacity'],
                transparent=True,
                visibility=True
            )

    def test_that_authenticated_user_without_permissions_cannot_view_map_in_layer_detail(self):
        """
        Test that an authenticated user without permissions to view a map does not see the map under
        'Maps using this layer' in layer_detail when map is not viewable by 'anyone'
        """
        ResourceManager.remove_permissions(self.map.uuid, instance=self.map.get_self_resource())
        self.client.login(username='dybala', password='very-secret')
        response = self.client.get(reverse('layer_detail', args=(self.layer.alternate,)))
        self.assertEqual(response.context['map_layers'], [])

    def test_that_keyword_multiselect_is_disabled_for_non_admin_users(self):
        """
        Test that keyword multiselect widget is disabled when the user is not an admin
        """
        self.test_layer = Layer.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True)
        url = reverse('layer_metadata', args=(self.test_layer.alternate,))

        self.client.login(username=self.not_admin.username, password='very-secret')
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.get(url)
            self.assertTrue(response.context['form']['keywords'].field.disabled)

    def test_that_keyword_multiselect_is_not_disabled_for_admin_users(self):
        """
        Test that only admin users can create/edit keywords  when FREETEXT_KEYWORDS_READONLY=True
        """
        admin = self.not_admin
        admin.is_superuser = True
        admin.save()
        self.test_layer = Layer.objects.create(uuid=str(uuid4()), owner=admin, title='test', is_approved=True)
        url = reverse('layer_metadata', args=(self.test_layer.alternate,))

        self.client.login(username=admin.username, password='very-secret')
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.get(url)
            self.assertFalse(response.context['form']['keywords'].field.disabled)

    def test_that_non_admin_user_cannot_create_edit_keyword(self):
        """
        Test that non admin users cannot edit/create keywords when FREETEXT_KEYWORDS_READONLY=True
        """
        self.test_layer = Layer.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True)
        url = reverse('layer_metadata', args=(self.test_layer.alternate,))

        self.client.login(username=self.not_admin.username, password='very-secret')
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.post(url, data={'resource-keywords': 'wonderful-keyword'})
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.content, b'Unauthorized: Cannot edit/create Free-text Keywords')

    def test_that_keyword_multiselect_is_enabled_for_non_admin_users_when_freetext_keywords_readonly_istrue(self):
        """
        Test that keyword multiselect widget is not disabled when the user is not an admin
        and FREETEXT_KEYWORDS_READONLY=False
        """
        self.test_layer = Layer.objects.create(uuid=str(uuid4()), owner=self.not_admin, title='test', is_approved=True)
        url = reverse('layer_metadata', args=(self.test_layer.alternate,))

        self.client.login(username=self.not_admin.username, password='very-secret')
        with self.settings(FREETEXT_KEYWORDS_READONLY=False):
            response = self.client.get(url)
            self.assertFalse(response.context['form']['keywords'].field.disabled)

    def test_that_anonymous_user_can_view_map_available_to_anyone(self):
        """
        Test that anonymous user can view map that has view permissions to 'anyone'
        """
        response = self.client.get(reverse('layer_detail', args=(self.layer.alternate,)))
        self.assertEqual(response.context['map_layers'], [self.map_layer])

    def test_that_anonymous_user_cannot_view_map_with_restricted_view(self):
        """
        Test that anonymous user cannot view map that are not viewable by 'anyone'
        """
        ResourceManager.remove_permissions(self.map.uuid, instance=self.map.get_self_resource())
        response = self.client.get(reverse('layer_detail', args=(self.layer.alternate,)))
        self.assertEqual(response.context['map_layers'], [])

    def test_that_only_users_with_permissions_can_view_maps_in_layer_view(self):
        """
        Test only users with view permissions to a map can view them in layer detail view
        """
        ResourceManager.remove_permissions(self.map.uuid, instance=self.map.get_self_resource())
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('layer_detail', args=(self.layer.alternate,)))
        self.assertEqual(response.context['map_layers'], [self.map_layer])

    def test_update_with_a_comma_in_title_is_replaced_by_undescore(self):
        """
        Test that when changing the dataset title, if the entered title has a comma it is replaced by an undescore.
        """
        self.test_dataset = None
        try:
            self.test_dataset = Layer.objects.create(
                uuid=str(uuid4()),
                name='test',
                alternate='geonode:test',
                title='test,comma,2021',
                is_approved=True,
                bbox_polygon=Polygon.from_bbox((-180, -90, 180, 90)),
                srid='EPSG:4326',
                owner=self.not_admin)

            data = {
                'resource-title': 'test,comma,2021',
                'resource-owner': self.test_dataset.owner.id,
                'resource-date': '2021-10-27 05:59 am',
                'resource-date_type': 'publication',
                'resource-language': self.test_dataset.language,
                'layer_attribute_set-TOTAL_FORMS': 0,
                'layer_attribute_set-INITIAL_FORMS': 0,
            }

            url = reverse('layer_metadata', args=(self.test_dataset.alternate,))
            self.assertTrue(self.client.login(username=self.not_admin.username, password='very-secret'))
            response = self.client.post(url, data=data)
            self.test_dataset.refresh_from_db()
            self.assertEqual(self.test_dataset.title, 'test_comma_2021')
            self.assertEqual(response.status_code, 200)
        finally:
            if self.test_dataset:
                self.test_dataset.delete()


'''
Smoke test to explain how the uuidhandler will override the uuid for the layers
Documentation of the handler is available here:
https://github.com/GeoNode/documentation/blob/703cc6ba92b7b7a83637a874fb449420a9f8b78a/basic/settings/index.rst#uuid-handler
'''


class DummyUUIDHandler():
    def __init__(self, instance):
        self.instance = instance

    def create_uuid(self):
        return f'abc:{self.instance.uuid}'


class TestCustomUUidHandler(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='test', email='test@test.com')
        self.sut = Layer.objects.create(
            uuid='abc-1234-abc', name="testLayer", owner=self.user, title='test', is_approved=True
        )

    def test_layer_will_maintain_his_uud_if_no_handler_is_definded(self):
        expected = "abc-1234-abc"
        self.assertEqual(expected, self.sut.uuid)

    @override_settings(LAYER_UUID_HANDLER="geonode.layers.tests.DummyUUIDHandler")
    def test_layer_will_override_the_uuid_if_handler_is_defined(self):
        self.sut.keywords.add(*["updating", "values"])
        self.sut.save()
        expected = "abc:abc-1234-abc"
        actual = Layer.objects.get(id=self.sut.id)
        self.assertEqual(expected, actual.uuid)


class TestalidateInputSource(TestCase):

    def setUp(self):
        self.maxDiff = None
        self.layer = create_single_layer('single_point')
        self.r = namedtuple('GSCatalogRes', ['resource'])

    def tearDown(self):
        self.layer.delete()

    def test_will_raise_exception_for_replace_vector_layer_with_raster(self):
        layer = Layer.objects.filter(name="single_point")[0]
        filename = "/tpm/filename.tif"
        files = ["/opt/file1.shp", "/opt/file2.ccc"]
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = "You are attempting to append a vector layer with a raster."
        self.assertEqual(expected, e.exception.args[0])

    def test_will_raise_exception_for_replace_layer_with_unknown_format(self):
        layer = Layer.objects.filter(name="single_point")[0]
        filename = "/tpm/filename.ccc"
        files = ["/opt/file1.shp", "/opt/file2.ccc"]
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = "You are attempting to append a vector layer with an unknown format."
        self.assertEqual(expected, e.exception.args[0])

    def test_will_raise_exception_for_replace_layer_with_different_file_name(self):
        layer = Layer.objects.get(name="single_point")
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "san_andres_y_providencia_highway.shp")
        files = {
            "shp": filename,
            "dbf": f"{file_path}/san_andres_y_providencia_highway.sbf",
            "prj": f"{file_path}/san_andres_y_providencia_highway.prj",
            "shx": f"{file_path}/san_andres_y_providencia_highway.shx",
        }
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = (
            "Some error occurred while trying to access the uploaded schema: "
            "Please ensure the name is consistent with the file you are trying to append."
        )
        self.assertEqual(expected, e.exception.args[0])

    @patch("geonode.layers.utils.gs_catalog")
    def test_will_raise_exception_for_not_existing_layer_in_the_catalog(self, catalog):
        catalog.get_layer.return_value = None
        layer = Layer.objects.filter(name="single_point")[0]
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "single_point.shp")
        files = {
            "shp": filename,
            "dbf": f"{file_path}/single_point.sbf",
            "prj": f"{file_path}/single_point.prj",
            "shx": f"{file_path}/single_point.shx",
        }
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = (
            "Some error occurred while trying to access the uploaded schema: "
            "The selected Layer does not exists in the catalog."
        )
        self.assertEqual(expected, e.exception.args[0])

    @patch("geonode.layers.utils.gs_catalog")
    def test_will_raise_exception_if_schema_is_not_equal_between_catalog_and_file(self, catalog):
        attr = namedtuple('GSCatalogAttr', ['attributes'])
        attr.attributes = []
        self.r.resource = attr
        catalog.get_layer.return_value = self.r
        layer = Layer.objects.filter(name="single_point")[0]
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "single_point.shp")
        files = {
            "shp": filename,
            "dbf": f"{file_path}/single_point.sbf",
            "prj": f"{file_path}/single_point.prj",
            "shx": f"{file_path}/single_point.shx",
        }
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = (
            "Some error occurred while trying to access the uploaded schema: "
            "Please ensure that the layer structure is consistent with the file you are trying to append."
        )
        self.assertEqual(expected, e.exception.args[0])

    @patch("geonode.layers.utils.gs_catalog")
    def test_validation_will_pass_for_valid_append(self, catalog):
        attr = namedtuple('GSCatalogAttr', ['attributes'])
        attr.attributes = ['label']
        self.r.resource = attr
        catalog.get_layer.return_value = self.r
        layer = Layer.objects.filter(name="single_point")[0]
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "single_point.shp")
        files = {
            "shp": filename,
            "dbf": f"{file_path}/single_point.sbf",
            "prj": f"{file_path}/single_point.prj",
            "shx": f"{file_path}/single_point.shx",
        }
        actual = validate_input_source(layer, filename, files, action_type="append")
        self.assertTrue(actual)


class TestSetMetadata(TestCase):
    def setUp(self):
        self.maxDiff = None
        self.invalid_xml = "xml"
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.custom = [
            {
                "keywords": ["features", "test_layer"],
                "thesaurus": {"date": None, "datetype": None, "title": None},
                "type": "theme",
            },
            {
                "keywords": ["no conditions to access and use"],
                "thesaurus": {
                    "date": "2020-10-30T16:58:34",
                    "datetype": "publication",
                    "title": "Test for ordering",
                },
                "type": None,
            },
            {
                "keywords": ["ad", "af"],
                "thesaurus": {
                    "date": "2008-06-01",
                    "datetype": "publication",
                    "title": "GEMET - INSPIRE themes, version 1.0",
                },
                "type": None,
            },
            {"keywords": ["Global"], "thesaurus": {"date": None, "datetype": None, "title": None}, "type": "place"},
        ]

    def test_set_metadata_will_rase_an_exception_if_is_not_valid_xml(self):
        with self.assertRaises(GeoNodeException):
            set_metadata(self.invalid_xml)

    def test_set_metadata_return_expected_values_from_xml(self):
        import datetime
        identifier, vals, regions, keywords, _ = set_metadata(open(self.exml_path).read())
        expected_vals = {
            "abstract": "real abstract",
            "constraints_other": "Not Specified: The original author did not specify a license.",
            "data_quality_statement": "Created with GeoNode",
            'date': datetime.datetime(2021, 4, 9, 9, 0, 46),
            "language": "eng",
            "purpose": None,
            "spatial_representation_type": "dataset",
            "supplemental_information": "No information provided",
            "temporal_extent_end": None,
            "temporal_extent_start": None,
            "title": "test_layer"
        }
        self.assertEqual('7cfbc42c-efa7-431c-8daa-1399dff4cd19', identifier)
        self.assertListEqual(['Global'], regions)
        self.assertDictEqual(expected_vals, vals)
        self.assertListEqual(self.custom, keywords)

    def test_convert_keyword_should_empty_list_for_empty_keyword(self):
        actual = convert_keyword([])
        self.assertListEqual([], actual)

    def test_convert_keyword_should_empty_list_for_non_empty_keyword(self):
        expected = [{
            "keywords": ['abc'],
            "thesaurus": {"date": None, "datetype": None, "title": None},
            "type": "theme",
        }]
        actual = convert_keyword(['abc'])
        self.assertListEqual(expected, actual)


'''
Smoke test to explain how the new function for multiple parsers will work
Is required to define a fuction that takes 1 parameters (the metadata xml) and return 4 parameters.
            Parameters:
                    xml (str): TextIOWrapper read example: open(self.exml_path).read())

            Returns:
                    Tuple (tuple):
                        - (identifier, vals, regions, keywords)

                    identifier(str): default empy,
                    vals(dict): default empty,
                    regions(list): default empty,
                    keywords(list(dict)): default empty
'''


class TestCustomMetadataParser(TestCase):
    def setUp(self):
        import datetime
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.expected_vals = {
            "abstract": "real abstract",
            "constraints_other": "Not Specified: The original author did not specify a license.",
            "data_quality_statement": "Created with GeoNode",
            'date': datetime.datetime(2021, 4, 9, 9, 0, 46),
            "language": "eng",
            "purpose": None,
            "spatial_representation_type": "dataset",
            "supplemental_information": "No information provided",
            "temporal_extent_end": None,
            "temporal_extent_start": None,
            "title": "test_layer"
        }

        self.keywords = [
            {
                "keywords": ["features", "test_layer"],
                "thesaurus": {"date": None, "datetype": None, "title": None},
                "type": "theme",
            },
            {
                "keywords": ["no conditions to access and use"],
                "thesaurus": {
                    "date": "2020-10-30T16:58:34",
                    "datetype": "publication",
                    "title": "Test for ordering",
                },
                "type": None,
            },
            {
                "keywords": ["ad", "af"],
                "thesaurus": {
                    "date": "2008-06-01",
                    "datetype": "publication",
                    "title": "GEMET - INSPIRE themes, version 1.0",
                },
                "type": None,
            },
            {"keywords": ["Global"], "thesaurus": {"date": None, "datetype": None, "title": None}, "type": "place"},
        ]

    def test_will_use_only_the_default_metadata_parser(self):
        identifier, vals, regions, keywords, _ = parse_metadata(open(self.exml_path).read())
        self.assertEqual('7cfbc42c-efa7-431c-8daa-1399dff4cd19', identifier)
        self.assertListEqual(['Global'], regions)
        self.assertListEqual(self.keywords, keywords)
        self.assertDictEqual(self.expected_vals, vals)

    @override_settings(METADATA_PARSERS=['__DEFAULT__', 'geonode.layers.tests.dummy_metadata_parser'])
    def test_will_use_both_parsers_defined(self):
        identifier, vals, regions, keywords, _ = parse_metadata(open(self.exml_path).read())
        self.assertEqual('7cfbc42c-efa7-431c-8daa-1399dff4cd19', identifier)
        self.assertListEqual(['Global', 'Europe'], regions)
        self.assertEqual("Passed through new parser", keywords)
        self.assertDictEqual(self.expected_vals, vals)

    def test_convert_keyword_should_empty_list_for_empty_keyword(self):
        actual = convert_keyword([])
        self.assertListEqual([], actual)

    def test_convert_keyword_should_non_empty_list_for_empty_keyword(self):
        expected = [{
            "keywords": ['abc'],
            "thesaurus": {"date": None, "datetype": None, "title": None},
            "type": "theme",
        }]
        actual = convert_keyword(['abc'])
        self.assertListEqual(expected, actual)


'''
Just a dummy function required for the smoke test above
'''


def dummy_metadata_parser(exml, uuid, vals, regions, keywords, custom):
    keywords = "Passed through new parser"
    regions.append("Europe")
    return uuid, vals, regions, keywords, custom


class TestIsXmlUploadOnly(TestCase):
    '''
    This function will check if the files uploaded is a metadata file
    '''

    def setUp(self):
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.request = RequestFactory()

    def test_give_single_file_should_return_True(self):
        with open(self.exml_path, 'rb') as f:
            request = self.request.post('/random/url')
            request.FILES['base_file'] = f
        actual = is_xml_upload_only(request)
        self.assertTrue(actual)

    def test_give_single_file_should_return_False(self):
        base_path = gisdata.GOOD_DATA
        with open(f'{base_path}/vector/single_point.shp', 'rb') as f:
            request = self.request.post('/random/url')
            request.FILES['base_file'] = f
        actual = is_xml_upload_only(request)
        self.assertFalse(actual)


class TestUploadLayerMetadata(GeoNodeBaseTestSupport):

    fixtures = ["group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.sld_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_sld.sld"
        self.sut = create_single_layer("single_point")

    def test_xml_form_without_files_should_raise_500(self):
        files = dict()
        files['permissions'] = '{}'
        files['charset'] = 'utf-8'
        self.client.login(username="admin", password="admin")
        resp = self.client.post(reverse('layer_upload'), data=files)
        self.assertEqual(500, resp.status_code)

    def test_xml_should_return_404_if_the_layer_does_not_exists(self):
        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.exml_path),
            "xml_file": open(self.exml_path),
            "layer_title": "Fake layer title",
            "metadata_upload_form": True,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        resp = self.client.post(reverse('layer_upload'), params)
        self.assertEqual(404, resp.status_code)

    def test_xml_should_raise_an_error_if_the_uuid_is_changed(self):
        '''
        If the UUID coming from the XML and the one saved in the DB are different
        The system should raise an error
        '''
        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.exml_path),
            "xml_file": open(self.exml_path),
            "layer_title": "geonode:single_point",
            "metadata_upload_form": True,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        prev_layer = Layer.objects.get(typename="geonode:single_point")
        self.assertEqual(0, prev_layer.keywords.count())
        resp = self.client.post(reverse('layer_upload'), params)
        self.assertEqual(404, resp.status_code)
        expected = {
            "success": False,
            "errors": "The UUID identifier from the XML Metadata, is different from the one saved"
        }
        self.assertDictEqual(expected, resp.json())

    def test_xml_should_update_the_layer_with_the_expected_values(self):
        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.exml_path),
            "xml_file": open(self.exml_path),
            "layer_title": "geonode:single_point",
            "metadata_upload_form": True,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        prev_layer = Layer.objects.get(typename="geonode:single_point")
        # updating the layer with the same uuid of the xml uploaded
        # otherwise will rase an error
        prev_layer.uuid = '7cfbc42c-efa7-431c-8daa-1399dff4cd19'
        prev_layer.save()

        self.assertEqual(0, prev_layer.keywords.count())
        resp = self.client.post(reverse('layer_upload'), params)
        self.assertEqual(200, resp.status_code)
        updated_layer = Layer.objects.get(typename="geonode:single_point")
        # just checking some values if are updated
        self.assertEqual(6, updated_layer.keywords.all().count())

    def test_sld_should_raise_500_if_is_invalid(self):
        layer = Layer.objects.first()
        create_layer_data(layer.resourcebase_ptr_id)
        layer = Layer.objects.filter(alternate=layer.alternate).first()

        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.sld_path),
            "sld_file": open(self.sld_path),
            "layer_title": "random",
            "metadata_upload_form": False,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        self.assertGreaterEqual(layer.styles.count(), 1)
        self.assertIsNotNone(layer.styles.first())
        resp = self.client.post(reverse('layer_upload'), params)
        self.assertEqual(500, resp.status_code)
        self.assertFalse(resp.json().get('success'))
        self.assertEqual('No Layer matches the given query.', resp.json().get('errors'))

    def test_sld_should_update_the_layer_with_the_expected_values(self):
        lid = Layer.objects.first().resourcebase_ptr_id
        create_layer_data(lid)
        layer = Layer.objects.get(typename="geonode:single_point")

        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.sld_path),
            "sld_file": open(self.sld_path),
            "layer_title": f"geonode:{layer.name}",
            "metadata_upload_form": False,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        self.assertGreaterEqual(layer.styles.count(), 1)
        self.assertIsNotNone(layer.styles.first())
        resp = self.client.post(reverse('layer_upload'), params)
        self.assertEqual(200, resp.status_code)
        updated_layer = Layer.objects.get(alternate=f"geonode:{layer.name}")
        # just checking some values if are updated
        self.assertGreaterEqual(updated_layer.styles.all().count(), 1)


class TestIsSldUploadOnly(TestCase):
    '''
    This function will check if the files uploaded is a metadata file
    '''

    def setUp(self):
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_sld.sld"
        self.request = RequestFactory()

    def test_give_single_file_should_return_True(self):
        with open(self.exml_path, 'rb') as f:
            request = self.request.post('/random/url')
            request.FILES['base_file'] = f
        actual = is_sld_upload_only(request)
        self.assertTrue(actual)

    def test_give_single_file_should_return_False(self):
        base_path = gisdata.GOOD_DATA
        with open(f'{base_path}/vector/single_point.shp', 'rb') as f:
            request = self.request.post('/random/url')
            request.FILES['base_file'] = f
        actual = is_sld_upload_only(request)
        self.assertFalse(actual)


class TestLayerForm(GeoNodeBaseTestSupport):
    def setUp(self) -> None:
        self.user = get_user_model().objects.get(username='admin')
        self.layer = create_single_layer("my_single_layer", owner=self.user)
        self.sut = LayerForm

    def test_resource_form_is_invalid_extra_metadata_not_json_format(self):
        self.client.login(username="admin", password="admin")
        url = reverse("layer_metadata", args=(self.layer.alternate,))
        response = self.client.post(url, data={
            "resource-owner": self.layer.owner.id,
            "resource-title": "layer_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": "not-a-json"
        })
        expected = {"success": False, "errors": ["extra_metadata: The value provided for the Extra metadata field is not a valid JSON"]}
        self.assertDictEqual(expected, response.json())

    @override_settings(EXTRA_METADATA_SCHEMA={"key": "value"})
    def test_resource_form_is_invalid_extra_metadata_not_schema_in_settings(self):
        self.client.login(username="admin", password="admin")
        url = reverse("layer_metadata", args=(self.layer.alternate,))
        response = self.client.post(url, data={
            "resource-owner": self.layer.owner.id,
            "resource-title": "layer_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": "[{'key': 'value'}]"
        })
        expected = {"success": False, "errors": ["extra_metadata: EXTRA_METADATA_SCHEMA validation schema is not available for resource layer"]}
        self.assertDictEqual(expected, response.json())

    def test_resource_form_is_invalid_extra_metadata_invalids_schema_entry(self):
        self.client.login(username="admin", password="admin")
        url = reverse("layer_metadata", args=(self.layer.alternate,))
        response = self.client.post(url, data={
            "resource-owner": self.layer.owner.id,
            "resource-title": "layer_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": '[{"key": "value"},{"id": "int", "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        expected = "extra_metadata: Missing keys: \'field_label\', \'field_name\', \'field_value\', \'filter_header\' at index 0 "
        self.assertIn(expected, response.json()['errors'][0])

    def test_resource_form_is_valid_extra_metadata(self):
        form = self.sut(instance=self.layer, data={
            "owner": self.layer.owner.id,
            "title": "layer_title",
            "date": "2022-01-24 16:38 pm",
            "date_type": "creation",
            "language": "eng",
            "extra_metadata": '[{"id": 1, "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        self.assertTrue(form.is_valid())
