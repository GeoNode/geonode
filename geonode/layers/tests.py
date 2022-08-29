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

import io
import os
import shutil
import gisdata
import logging
import zipfile

from uuid import uuid4
from unittest.mock import MagicMock, patch
from collections import namedtuple
from pinax.ratings.models import OverallRating

from django.urls import reverse
from django.test import TestCase
from django.forms import ValidationError
from django.test.client import RequestFactory
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Group
from django.contrib.gis.geos import Polygon
from django.db.models import Count
from django.contrib.auth import get_user_model

from django.conf import settings
from django.test.utils import override_settings
from django.contrib.admin.sites import AdminSite
from geonode.geoserver.createlayer.utils import create_dataset

from geonode.layers import utils
from geonode.base import enumerations
from geonode.layers import DatasetAppConfig
from geonode.layers.admin import DatasetAdmin
from geonode.decorators import on_ogc_backend
from geonode.maps.models import Map, MapLayer
from geonode.utils import DisableDjangoSignals, mkdtemp
from geonode.layers.views import _resolve_dataset
from geonode import GeoNodeException, geoserver
from geonode.people.utils import get_valid_user
from guardian.shortcuts import get_anonymous_user
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.resource.manager import resource_manager
from geonode.tests.utils import NotificationsTestsHelper
from geonode.layers.models import Dataset, Style, Attribute
from geonode.layers.forms import DatasetForm, DatasetTimeSerieForm, JSONField, LayerUploadForm
from geonode.layers.populate_datasets_data import create_dataset_data
from geonode.base.models import TopicCategory, License, Region, Link
from geonode.utils import check_ogc_backend, set_resource_default_links
from geonode.layers.metadata import convert_keyword, set_metadata, parse_metadata

from geonode.layers.utils import (
    is_sld_upload_only,
    is_xml_upload_only,
    dataset_type,
    get_files,
    get_valid_name,
    get_valid_dataset_name,
    surrogate_escape_string, validate_input_source)

from geonode.base.populate_test_data import (
    all_public,
    create_models,
    remove_models,
    create_single_dataset)

logger = logging.getLogger(__name__)


class DatasetsTest(GeoNodeBaseTestSupport):

    """Tests geonode.layers app/module
    """
    type = 'dataset'

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        self.anonymous_user = get_anonymous_user()
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.sld_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_sld.sld"
        self.maxDiff = None
        self.sut = create_single_dataset("single_point")
        create_dataset_data(self.sut.resourcebase_ptr_id)
        create_dataset_data(Dataset.objects.first().resourcebase_ptr_id)
        self.r = namedtuple('GSCatalogRes', ['resource'])

        site = AdminSite()
        self.admin = DatasetAdmin(Dataset, site)

        self.request_admin = RequestFactory().get('/admin')
        self.request_admin.user = get_user_model().objects.get(username='admin')

    # Admin Tests

    def test_admin_save_model(self):
        obj = Dataset.objects.first()
        self.assertEqual(len(obj.keywords.all()), 2)
        form = self.admin.get_form(self.request_admin, obj=obj, change=True)
        self.admin.save_model(self.request_admin, obj, form, True)

    def test_default_sourcetype(self):
        obj = Dataset.objects.first()
        self.assertEqual(obj.sourcetype, enumerations.SOURCE_TYPE_LOCAL)

    # Data Tests

    def test_describe_data_2(self):
        '''/data/geonode:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(10, get_user_model().objects.all().count())
        response = self.client.get(reverse('dataset_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.assertEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('dataset_metadata', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

    def test_describe_data_3(self):
        '''/data/geonode:CA/metadata_detail -> Test accessing the description of a layer '''
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('dataset_metadata_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Approved", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Published", count=1, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "Featured", count=3, status_code=200, msg_prefix='', html=False)
        self.assertContains(response, "<dt>Group</dt>", count=0, status_code=200, msg_prefix='', html=False)

        # ... now assigning a Group to the Dataset
        lyr = Dataset.objects.get(alternate='geonode:CA')
        group = Group.objects.first()
        lyr.group = group
        lyr.save()
        response = self.client.get(reverse('dataset_metadata_detail', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<dt>Group</dt>", count=1, status_code=200, msg_prefix='', html=False)
        lyr.group = None
        lyr.save()

    # Dataset Tests

    def test_dataset_name_clash(self):
        _ll_1 = Dataset.objects.create(
            uuid=str(uuid4()),
            owner=get_user_model().objects.get(username=self.user),
            name='states',
            store='geonode_data',
            subtype="vector",
            alternate="geonode:states"
        )
        _ll_2 = Dataset.objects.create(
            uuid=str(uuid4()),
            owner=get_user_model().objects.get(username=self.user),
            name='geonode:states',
            store='httpfooremoteservce',
            subtype="remote",
            alternate="geonode:states"
        )
        _ll_1.set_permissions({'users': {"bobby": ['base.view_resourcebase']}})
        _ll_2.set_permissions({'users': {"bobby": ['base.view_resourcebase']}})
        self.client.login(username="bobby", password="bob")
        _request = self.client.request()
        _request.user = get_user_model().objects.get(username="bobby")
        _ll = _resolve_dataset(_request, alternate="geonode:states")
        self.assertIsNotNone(_ll)
        self.assertEqual(_ll.name, _ll_1.name)

    def test_describe_data(self):
        '''/data/geonode:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(10, get_user_model().objects.all().count())
        response = self.client.get(reverse('dataset_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.assertEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('dataset_metadata', args=('geonode:CA',)))
        self.assertEqual(response.status_code, 200)

    def test_dataset_attributes(self):
        lyr = Dataset.objects.all().first()
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

    def test_dataset_bbox(self):
        lyr = Dataset.objects.all().first()
        dataset_bbox = lyr.bbox[0:4]
        logger.debug(dataset_bbox)

        def decimal_encode(bbox):
            _bbox = [float(o) for o in bbox]
            # Must be in the form : [x0, x1, y0, y1
            return [_bbox[0], _bbox[2], _bbox[1], _bbox[3]]

        from geonode.utils import bbox_to_projection
        projected_bbox = decimal_encode(
            bbox_to_projection([float(coord) for coord in dataset_bbox] + [lyr.srid, ],
                               target_srid=4326)[:4])
        logger.debug(projected_bbox)
        self.assertEqual(projected_bbox, [-180.0, -90.0, 180.0, 90.0])
        logger.debug(lyr.ll_bbox)
        self.assertEqual(lyr.ll_bbox, [-180.0, 180.0, -90.0, 90.0, 'EPSG:4326'])
        projected_bbox = decimal_encode(
            bbox_to_projection([float(coord) for coord in dataset_bbox] + [lyr.srid, ],
                               target_srid=3857)[:4])
        solution = [-20037397.023298454, -74299743.40065672,
                    20037397.02329845, 74299743.40061197]
        logger.debug(projected_bbox)
        for coord, check in zip(projected_bbox, solution):
            self.assertAlmostEqual(coord, check, places=3)

    def test_dataset_attributes_feature_catalogue(self):
        """ Test layer feature catalogue functionality
        """
        self.assertTrue(self.client.login(username='admin', password='admin'))
        # test a non-existing layer
        url = reverse('dataset_feature_catalogue', args=('bad_dataset',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Get the layer to work with
        layer = Dataset.objects.all()[3]
        url = reverse('dataset_feature_catalogue', args=(layer.alternate,))
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 404)

    def test_dataset_attribute_config(self):
        lyr = Dataset.objects.all().first()
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

        attributes = Attribute.objects.filter(dataset=lyr)
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

    def test_dataset_styles(self):
        lyr = Dataset.objects.all().first()
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

    def test_dataset_links(self):
        lyr = Dataset.objects.filter(subtype="vector").first()
        self.assertEqual(lyr.subtype, "vector")
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

        lyr = Dataset.objects.filter(subtype="raster").first()
        self.assertEqual(lyr.subtype, "raster")
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

    def test_dataset_type(self):
        self.assertEqual(dataset_type('foo.shp'), 'vector')
        self.assertEqual(dataset_type('foo.SHP'), 'vector')
        self.assertEqual(dataset_type('foo.sHp'), 'vector')
        self.assertEqual(dataset_type('foo.tif'), 'raster')
        self.assertEqual(dataset_type('foo.TIF'), 'raster')
        self.assertEqual(dataset_type('foo.TiF'), 'raster')
        self.assertEqual(dataset_type('foo.geotif'), 'raster')
        self.assertEqual(dataset_type('foo.GEOTIF'), 'raster')
        self.assertEqual(dataset_type('foo.gEoTiF'), 'raster')
        self.assertEqual(dataset_type('foo.tiff'), 'raster')
        self.assertEqual(dataset_type('foo.TIFF'), 'raster')
        self.assertEqual(dataset_type('foo.TiFf'), 'raster')
        self.assertEqual(dataset_type('foo.geotiff'), 'raster')
        self.assertEqual(dataset_type('foo.GEOTIFF'), 'raster')
        self.assertEqual(dataset_type('foo.gEoTiFf'), 'raster')
        self.assertEqual(dataset_type('foo.asc'), 'raster')
        self.assertEqual(dataset_type('foo.ASC'), 'raster')
        self.assertEqual(dataset_type('foo.AsC'), 'raster')

        # basically anything else should produce a GeoNodeException
        self.assertRaises(GeoNodeException, lambda: dataset_type('foo.gml'))

    def test_get_files(self):
        def generate_files(*extensions):
            if extensions[0].lower() != 'shp':
                return
            d = None
            expected_files = None
            try:
                d = mkdtemp()
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

    def test_get_valid_dataset_name(self):
        self.assertEqual(get_valid_dataset_name("blug", False), "blug")
        self.assertEqual(get_valid_dataset_name("blug", True), "blug")

        self.assertEqual(get_valid_dataset_name("<ab>", False), "_ab_")
        self.assertEqual(get_valid_dataset_name("<ab>", True), "<ab>")

        self.assertEqual(get_valid_dataset_name("<-->", False), "_")
        self.assertEqual(get_valid_dataset_name("<-->", True), "<-->")

        self.assertNotEqual(get_valid_dataset_name("CA", False), "CA_1")
        self.assertNotEqual(get_valid_dataset_name("CA", False), "CA_1")
        self.assertEqual(get_valid_dataset_name("CA", True), "CA")
        self.assertEqual(get_valid_dataset_name("CA", True), "CA")

        layer = Dataset.objects.get(name="CA")
        self.assertNotEqual(get_valid_dataset_name(layer, False), "CA_1")
        self.assertEqual(get_valid_dataset_name(layer, True), "CA")

        self.assertRaises(GeoNodeException, get_valid_dataset_name, 12, False)
        self.assertRaises(GeoNodeException, get_valid_dataset_name, 12, True)

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

    def test_rating_dataset_remove(self):
        """ Test layer rating is removed on layer remove
        """
        # Get the layer to work with
        layer = Dataset.objects.all()[3]
        dataset_id = layer.id
        # Create the rating with the correct content type
        ctype = ContentType.objects.get(model='dataset')
        OverallRating.objects.create(
            category=2,
            object_id=dataset_id,
            content_type=ctype,
            rating=3)
        rating = OverallRating.objects.all()
        self.assertEqual(rating.count(), 1)
        # Remove the layer
        resource_manager.delete(layer.uuid)
        # Check there are no ratings matching the remove layer
        rating = OverallRating.objects.all()
        self.assertEqual(rating.count(), 0)

    def test_sld_upload(self):
        """Test layer remove functionality
        """
        layer = Dataset.objects.all().first()
        url = reverse('dataset_sld_upload', args=(layer.alternate,))
        # Now test with a valid user
        self.client.login(username='admin', password='admin')

        # test a method other than POST and GET
        response = self.client.put(url)
        content = response.content.decode('utf-8')
        self.assertEqual(response.status_code, 200)
        self.assertFalse("#modal_perms" in content)

    def test_category_counts(self):
        topics = TopicCategory.objects.all()
        topics = topics.annotate(
            **{'dataset_count': Count('resourcebase__dataset__category')})
        location = topics.get(identifier='location')
        # there are three layers with location category
        self.assertEqual(location.dataset_count, 3)

        # change the category of one layers_count
        layer = Dataset.objects.filter(category=location)[0]
        elevation = topics.get(identifier='elevation')
        layer.category = elevation
        layer.save()

        # reload the categories since it's caching the old count
        topics = topics.annotate(
            **{'dataset_count': Count('resourcebase__dataset__category')})
        location = topics.get(identifier='location')
        elevation = topics.get(identifier='elevation')
        self.assertEqual(location.dataset_count, 2)
        self.assertEqual(elevation.dataset_count, 4)

        # delete a layer and check the count update
        # use the first since it's the only one which has styles
        layer = Dataset.objects.all().first()
        elevation = topics.get(identifier='elevation')
        self.assertEqual(elevation.dataset_count, 4)
        layer.delete()
        topics = topics.annotate(
            **{'dataset_count': Count('resourcebase__dataset__category')})
        elevation = topics.get(identifier='elevation')
        self.assertEqual(elevation.dataset_count, 3)

    def test_assign_change_dataset_data_perm(self):
        """
        Ensure set_permissions supports the change_dataset_data permission.
        """
        layer = Dataset.objects.first()
        user = get_anonymous_user()
        layer.set_permissions({'users': {user.username: ['change_dataset_data']}})
        perms = layer.get_all_level_info()
        self.assertNotIn(user, perms['users'])
        self.assertNotIn(user.username, perms['users'])

    def test_batch_edit(self):
        """
        Test batch editing of metadata fields.
        """
        Model = Dataset
        view = 'dataset_batch_metadata'
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

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_assign_remove_permissions(self):
        # Assing
        layer = Dataset.objects.all().first()
        perm_spec = layer.get_all_level_info()
        self.assertNotIn(get_user_model().objects.get(username="norman"), perm_spec["users"])

        utils.set_datasets_permissions("write", resources_names=[layer.name], users_usernames=["norman"], delete_flag=False, verbose=True)
        perm_spec = layer.get_all_level_info()
        _c = 0
        if "users" in perm_spec:
            for _u in perm_spec["users"]:
                if _u == "norman" or _u == get_user_model().objects.get(username="norman"):
                    _c += 1
        # "norman" has both read & write permissions
        self.assertEqual(_c, 1)

        # Remove
        utils.set_datasets_permissions("read", resources_names=[layer.name], users_usernames=["norman"], delete_flag=True, verbose=True)
        perm_spec = layer.get_all_level_info()
        _c = 0
        if "users" in perm_spec:
            for _u in perm_spec["users"]:
                if _u == "norman" or _u == get_user_model().objects.get(username="norman"):
                    _c += 1
        # "norman" has no permissions
        self.assertEqual(_c, 0)

    def test_xml_form_without_files_should_raise_500(self):
        files = dict()
        files['permissions'] = '{}'
        files['charset'] = 'utf-8'
        self.client.login(username="admin", password="admin")
        resp = self.client.post(reverse('dataset_upload'), data=files)
        self.assertEqual(500, resp.status_code)

    def test_xml_should_return_404_if_the_dataset_does_not_exists(self):
        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.exml_path),
            "xml_file": open(self.exml_path),
            "dataset_title": "Fake layer title",
            "metadata_upload_form": True,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        resp = self.client.post(reverse('dataset_upload'), params)
        self.assertEqual(404, resp.status_code)

    def test_xml_should_update_the_dataset_with_the_expected_values(self):
        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.exml_path),
            "xml_file": open(self.exml_path),
            "dataset_title": "geonode:single_point",
            "metadata_upload_form": True,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        prev_dataset = Dataset.objects.get(typename="geonode:single_point")
        self.assertEqual(0, prev_dataset.keywords.count())
        resp = self.client.post(reverse('dataset_upload'), params)
        self.assertEqual(404, resp.status_code)
        self.assertEqual(resp.json()["errors"], "The UUID identifier from the XML Metadata, is different from the one saved")

    def test_sld_should_raise_500_if_is_invalid(self):
        layer = Dataset.objects.get(typename="geonode:single_point")

        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.sld_path),
            "sld_file": open(self.sld_path),
            "dataset_title": "random",
            "metadata_upload_form": False,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        self.assertGreaterEqual(layer.styles.count(), 1)
        self.assertIsNotNone(layer.styles.first())
        resp = self.client.post(reverse('dataset_upload'), params)
        self.assertEqual(500, resp.status_code)
        self.assertFalse(resp.json().get('success'))
        self.assertEqual('No Dataset matches the given query.', resp.json().get('errors'))

    def test_sld_should_update_the_dataset_with_the_expected_values(self):
        layer = Dataset.objects.get(typename="geonode:single_point")

        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.sld_path),
            "sld_file": open(self.sld_path),
            "dataset_title": f"geonode:{layer.name}",
            "metadata_upload_form": False,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        self.assertGreaterEqual(layer.styles.count(), 1)
        self.assertIsNotNone(layer.styles.first())
        resp = self.client.post(reverse('dataset_upload'), params)
        self.assertEqual(200, resp.status_code)
        updated_dataset = Dataset.objects.get(alternate=f"geonode:{layer.name}")
        # just checking some values if are updated
        self.assertGreaterEqual(updated_dataset.styles.all().count(), 1)
        self.assertIsNotNone(updated_dataset.styles.first())
        self.assertEqual(layer.styles.first().sld_title, updated_dataset.styles.first().sld_title)

    def test_xml_should_raise_an_error_if_the_uuid_is_changed(self):
        '''
        If the UUID coming from the XML and the one saved in the DB are different
        The system should raise an error
        '''
        params = {
            "permissions": '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            "base_file": open(self.exml_path),
            "xml_file": open(self.exml_path),
            "dataset_title": "geonode:single_point",
            "metadata_upload_form": True,
            "time": False,
            "charset": "UTF-8"
        }

        self.client.login(username="admin", password="admin")
        prev_dataset = Dataset.objects.get(typename="geonode:single_point")
        self.assertEqual(0, prev_dataset.keywords.count())
        resp = self.client.post(reverse('dataset_upload'), params)
        self.assertEqual(404, resp.status_code)
        expected = {
            "success": False,
            "errors": "The UUID identifier from the XML Metadata, is different from the one saved"
        }
        self.assertDictEqual(expected, resp.json())

    def test_will_raise_exception_for_replace_vector_dataset_with_raster(self):
        layer = Dataset.objects.get(name="single_point")
        filename = "/tpm/filename.tif"
        files = ["/opt/file1.shp", "/opt/file2.ccc"]
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = "You are attempting to append a vector dataset with a raster."
        self.assertEqual(expected, e.exception.args[0])

    def test_will_raise_exception_for_replace_dataset_with_unknown_format(self):
        layer = Dataset.objects.get(name="single_point")
        filename = "/tpm/filename.ccc"
        file_path = gisdata.VECTOR_DATA
        files = {
            "shp": filename,
            "dbf": f"{file_path}/san_andres_y_providencia_highway.asd",
            "prj": f"{file_path}/san_andres_y_providencia_highway.asd",
            "shx": f"{file_path}/san_andres_y_providencia_highway.asd",
        }
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = "You are attempting to append a vector dataset with an unknown format."
        self.assertEqual(expected, e.exception.args[0])

    def test_will_raise_exception_for_replace_dataset_with_different_file_name(self):
        layer = Dataset.objects.get(name="single_point")
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
    def test_will_raise_exception_for_not_existing_dataset_in_the_catalog(self, catalog):
        catalog.get_layer.return_value = None
        create_single_dataset("san_andres_y_providencia_water")
        layer = Dataset.objects.get(name="san_andres_y_providencia_water")
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "san_andres_y_providencia_water.shp")
        files = {
            "shp": filename,
            "dbf": f"{file_path}/san_andres_y_providencia_water.sbf",
            "prj": f"{file_path}/san_andres_y_providencia_water.prj",
            "shx": f"{file_path}/san_andres_y_providencia_water.shx",
        }
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = (
            "Some error occurred while trying to access the uploaded schema: "
            "The selected Dataset does not exists in the catalog."
        )
        self.assertEqual(expected, e.exception.args[0])

    @patch("geonode.layers.utils.gs_catalog")
    def test_will_raise_exception_if_schema_is_not_equal_between_catalog_and_file(self, catalog):
        attr = namedtuple('GSCatalogAttr', ['attributes'])
        attr.attributes = []
        self.r.resource = attr
        catalog.get_layer.return_value = self.r
        create_single_dataset("san_andres_y_providencia_water")
        layer = Dataset.objects.filter(name="san_andres_y_providencia_water")[0]
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "san_andres_y_providencia_water.shp")
        files = {
            "shp": filename,
            "dbf": f"{file_path}/san_andres_y_providencia_water.sbf",
            "prj": f"{file_path}/san_andres_y_providencia_water.prj",
            "shx": f"{file_path}/san_andres_y_providencia_water.shx",
        }
        with self.assertRaises(Exception) as e:
            validate_input_source(layer, filename, files, action_type="append")
        expected = (
            "Some error occurred while trying to access the uploaded schema: "
            "Please ensure that the dataset structure is consistent with the file you are trying to append."
        )
        self.assertEqual(expected, e.exception.args[0])

    @patch("geonode.layers.utils.gs_catalog")
    def test_validation_will_pass_for_valid_append(self, catalog):
        attr = namedtuple('GSCatalogAttr', ['attributes'])
        attr.attributes = ['NATURAL', 'NAME']
        self.r.resource = attr
        catalog.get_layer.return_value = self.r
        create_single_dataset("san_andres_y_providencia_water")
        layer = Dataset.objects.filter(name="san_andres_y_providencia_water")[0]
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "san_andres_y_providencia_water.shp")
        files = {
            "shp": filename,
            "dbf": f"{file_path}/san_andres_y_providencia_water.sbf",
            "prj": f"{file_path}/san_andres_y_providencia_water.prj",
            "shx": f"{file_path}/san_andres_y_providencia_water.shx",
        }
        actual = validate_input_source(layer, filename, files, action_type="append")
        self.assertTrue(actual)

    def test_dataset_download_not_found_for_non_existing_dataset(self):
        self.client.login(username="admin", password="admin")
        url = reverse('dataset_download', args=['foo-dataset'])
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    @override_settings(USE_GEOSERVER=False)
    def test_dataset_download_redirect_to_proxy_url(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        url = reverse('dataset_download', args=[dataset.alternate])
        response = self.client.get(url)
        self.assertEqual(302, response.status_code)
        self.assertEqual(f"/download/{dataset.id}", response.url)

    def test_dataset_download_invalid_wps_format(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        url = reverse('dataset_download', args=[dataset.alternate])
        response = self.client.get(f"{url}?export_format=foo")
        self.assertEqual(500, response.status_code)
        self.assertDictEqual(
            {"error": "The format provided is not valid for the selected resource"},
            response.json()
        )

    @patch("geonode.layers.views.HttpClient.request")
    def test_dataset_download_call_the_catalog_raise_error_for_no_200(self, mocked_catalog):
        _response = MagicMock(status_code=500, content="foo-bar")
        mocked_catalog.return_value = _response, 'foo-bar'
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        url = reverse('dataset_download', args=[dataset.alternate])
        response = self.client.get(url)
        self.assertEqual(500, response.status_code)
        self.assertDictEqual(
            {"error": "Download dataset exception: error during call with GeoServer: foo-bar"},
            response.json()
        )

    @patch("geonode.layers.views.HttpClient.request")
    def test_dataset_download_call_the_catalog_raise_error_for_error_content(self, mocked_catalog):
        content = '''<?xml version="1.0" encoding="UTF-8"?>
                <ows:ExceptionReport xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:ows="http://www.opengis.net/ows/1.1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/ows/1.1 http://localhost:8080/geoserver/schemas/ows/1.1.0/owsAll.xsd">
                    <ows:Exception exceptionCode="InvalidParameterValue" locator="ResponseDocument">
                        <ows:ExceptionText>Foo Bar Exception</ows:ExceptionText>
                    </ows:Exception>
                </ows:ExceptionReport>
                '''  # noqa
        _response = MagicMock(
            status_code=200,
            text=content,
            headers={"Content-Type": "text/xml"}
        )
        mocked_catalog.return_value = _response, content
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        url = reverse('dataset_download', args=[dataset.alternate])
        response = self.client.get(url)
        self.assertEqual(500, response.status_code)
        self.assertDictEqual(
            {"error": "InvalidParameterValue: Foo Bar Exception"},
            response.json()
        )

    def test_dataset_download_call_the_catalog_works(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(
            status_code=200,
            text="",  # noqa
            headers={"Content-Type": ""}
        )
        self.client.login(username="admin", password="admin")
        dataset = Dataset.objects.first()
        layer = create_dataset(
            dataset.title,
            dataset.title,
            dataset.owner,
            'Point'
        )
        with patch("geonode.layers.views.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ''
            url = reverse('dataset_download', args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)

    def test_dataset_download_call_the_catalog_not_work_without_download_resurcebase_perm(self):
        dataset = Dataset.objects.first()
        dataset.set_permissions({'users': {"bobby": ['base.view_resourcebase']}})
        self.client.login(username="bobby", password="bob")
        url = reverse('dataset_download', args=[dataset.alternate])
        response = self.client.get(url)
        self.assertEqual(404, response.status_code)

    def test_dataset_download_call_the_catalog_work_anonymous(self):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(
            status_code=200,
            text="",  # noqa
            headers={"Content-Type": ""}
        )
        dataset = Dataset.objects.first()
        layer = create_dataset(
            dataset.title,
            dataset.title,
            dataset.owner,
            'Point'
        )
        with patch("geonode.layers.views.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ''
            url = reverse('dataset_download', args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)

    @override_settings(USE_GEOSERVER=True)
    @patch("geonode.layers.views.get_template")
    def test_dataset_download_call_the_catalog_work_for_raster(self, pathed_template):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(
            status_code=200,
            text="",  # noqa
            headers={"Content-Type": ""}
        )
        dataset = Dataset.objects.filter(subtype="raster").first()
        layer = create_dataset(
            dataset.title,
            dataset.title,
            dataset.owner,
            'Point'
        )
        Dataset.objects.filter(alternate=layer.alternate).update(subtype='raster')
        with patch("geonode.layers.views.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ''
            url = reverse('dataset_download', args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)
        '''
        Evaluate that the context used by the template contains the right mimetype for the resource
        '''
        self.assertTupleEqual(
            ({
                "alternate": layer.alternate,
                "download_format": "image/tiff"
            },),
            pathed_template.mock_calls[1].args
        )

    @override_settings(USE_GEOSERVER=True)
    @patch("geonode.layers.views.get_template")
    def test_dataset_download_call_the_catalog_work_for_vector(self, pathed_template):
        # if settings.USE_GEOSERVER is false, the URL must be redirected
        _response = MagicMock(
            status_code=200,
            text="",  # noqa
            headers={"Content-Type": ""}
        )
        dataset = Dataset.objects.filter(subtype="vector").first()
        layer = create_dataset(
            dataset.title,
            dataset.title,
            dataset.owner,
            'Point'
        )
        with patch("geonode.layers.views.HttpClient.request") as mocked_catalog:
            mocked_catalog.return_value = _response, ''
            url = reverse('dataset_download', args=[layer.alternate])
            response = self.client.get(url)
            self.assertTrue(response.status_code == 200)
        '''
        Evaluate that the context used by the template contains the right mimetype for the resource
        '''
        self.assertTupleEqual(
            ({
                "alternate": layer.alternate,
                "download_format": "application/zip"
            },),
            pathed_template.mock_calls[1].args
        )


class TestLayerDetailMapViewRights(GeoNodeBaseTestSupport):

    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()
        create_single_dataset('single_point')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.create(username='dybala', email='dybala@gmail.com')
        self.user.set_password('very-secret')
        self.admin = get_user_model().objects.get(username='admin')
        self.map = Map.objects.create(uuid=str(uuid4()), owner=self.admin, title='test', is_approved=True)
        self.not_admin = get_user_model().objects.create(username='r-lukaku', is_active=True)
        self.not_admin.set_password('very-secret')
        self.not_admin.save()

        self.layer = Dataset.objects.all().first()
        create_dataset_data(self.layer.resourcebase_ptr_id)
        with DisableDjangoSignals():
            self.map_dataset = MapLayer.objects.create(
                name=self.layer.alternate,
                map=self.map,
            )

    def test_that_keyword_multiselect_is_disabled_for_non_admin_users(self):
        """
        Test that keyword multiselect widget is disabled when the user is not an admin
        """
        self.test_dataset = resource_manager.create(
            None,
            resource_type=Dataset,
            defaults=dict(
                owner=self.not_admin,
                title='test',
                is_approved=True))

        url = reverse('dataset_metadata', args=(self.test_dataset.alternate,))
        self.client.login(username=self.not_admin.username, password='very-secret')
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.get(url)
            self.assertTrue(response.context['form']['keywords'].field.disabled, self.test_dataset.alternate)

    def test_that_keyword_multiselect_is_not_disabled_for_admin_users(self):
        """
        Test that only admin users can create/edit keywords  when FREETEXT_KEYWORDS_READONLY=True
        """
        admin = self.not_admin
        admin.is_superuser = True
        admin.save()

        self.test_dataset = resource_manager.create(
            None,
            resource_type=Dataset,
            defaults=dict(
                owner=admin,
                title='test',
                is_approved=True))

        url = reverse('dataset_metadata', args=(self.test_dataset.alternate,))

        self.client.login(username=admin.username, password='very-secret')
        with self.settings(FREETEXT_KEYWORDS_READONLY=True):
            response = self.client.get(url)
            self.assertFalse(response.context['form']['keywords'].field.disabled, self.test_dataset.alternate)

    def test_that_featured_enabling_and_disabling_for_users(self):
        self.test_dataset = resource_manager.create(
            None,
            resource_type=Dataset,
            defaults=dict(
                owner=self.not_admin,
                title='test',
                is_approved=True))

        url = reverse('dataset_metadata', args=(self.test_dataset.alternate,))
        # Non Admins
        self.client.login(username=self.not_admin.username, password='very-secret')
        response = self.client.get(url)
        self.assertFalse(self.not_admin.is_superuser)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form']['featured'].field.disabled)
        # Admin
        self.client.login(username='admin', password='admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form']['featured'].field.disabled)

    def test_that_non_admin_user_cannot_create_edit_keyword(self):
        """
        Test that non admin users cannot edit/create keywords when FREETEXT_KEYWORDS_READONLY=True
        """
        self.test_dataset = resource_manager.create(
            None,
            resource_type=Dataset,
            defaults=dict(
                owner=self.not_admin,
                title='test',
                is_approved=True))

        url = reverse('dataset_metadata', args=(self.test_dataset.alternate,))
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
        self.test_dataset = resource_manager.create(
            None,
            resource_type=Dataset,
            defaults=dict(
                owner=self.not_admin,
                title='test',
                is_approved=True))

        url = reverse('dataset_metadata', args=(self.test_dataset.alternate,))

        self.client.login(username=self.not_admin.username, password='very-secret')
        with self.settings(FREETEXT_KEYWORDS_READONLY=False):
            response = self.client.get(url)
            self.assertFalse(response.context['form']['keywords'].field.disabled, self.test_dataset.alternate)

        response = self.client.get(reverse('dataset_embed', args=(self.layer.alternate,)))
        self.assertIsNotNone(response.context['resource'])

    def test_that_only_users_with_permissions_can_view_maps_in_dataset_view(self):
        """
        Test only users with view permissions to a map can view them in layer detail view
        """
        resource_manager.remove_permissions(self.map.uuid, instance=self.map.get_self_resource())
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('dataset_embed', args=(self.layer.alternate,)))
        self.assertEqual(response.context['resource'].alternate, self.map_dataset.name)

    def test_update_with_a_comma_in_title_is_replaced_by_undescore(self):
        """
        Test that when changing the dataset title, if the entered title has a comma it is replaced by an undescore.
        """
        self.test_dataset = None
        try:
            self.test_dataset = resource_manager.create(
                None,
                resource_type=Dataset,
                defaults=dict(
                    owner=self.not_admin,
                    title='test',
                    is_approved=True
                )
            )

            data = {
                'resource-title': 'test,comma,2021',
                'resource-owner': self.test_dataset.owner.id,
                'resource-date': str(self.test_dataset.date),
                'resource-date_type': self.test_dataset.date_type,
                'resource-language': self.test_dataset.language,
                'dataset_attribute_set-TOTAL_FORMS': 0,
                'dataset_attribute_set-INITIAL_FORMS': 0,
            }

            url = reverse('dataset_metadata', args=(self.test_dataset.alternate,))
            self.client.login(username=self.not_admin.username, password='very-secret')
            response = self.client.post(url, data=data)
            self.test_dataset.refresh_from_db()
            self.assertEqual(self.test_dataset.title, 'test_comma_2021')
            self.assertEqual(response.status_code, 200)
        finally:
            if self.test_dataset:
                self.test_dataset.delete()


class LayerNotificationsTestCase(NotificationsTestsHelper):

    type = 'dataset'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        self.anonymous_user = get_anonymous_user()
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()
        self.setup_notifications_for(DatasetAppConfig.NOTIFICATIONS, self.u)
        self.norman = get_user_model().objects.get(username='norman')
        self.norman.email = 'norman@email.com'
        self.norman.is_active = True
        self.norman.save()
        self.setup_notifications_for(DatasetAppConfig.NOTIFICATIONS, self.norman)

    def testLayerNotifications(self):
        with self.settings(
                EMAIL_ENABLE=True,
                NOTIFICATION_ENABLED=True,
                NOTIFICATIONS_BACKEND="pinax.notifications.backends.email.EmailBackend",
                PINAX_NOTIFICATIONS_QUEUE_ALL=False):
            self.clear_notifications_queue()
            self.client.login(username=self.user, password=self.passwd)

            _l = resource_manager.create(
                None,
                resource_type=Dataset,
                defaults=dict(
                    name='test notifications',
                    title='test notifications',
                    bbox_polygon=Polygon.from_bbox((-180, -90, 180, 90)),
                    srid='EPSG:4326',
                    owner=self.norman)
            )

            self.assertTrue(self.check_notification_out('dataset_created', self.u))
            # Ensure "resource.owner" won't be notified for having uploaded its own resource
            self.assertFalse(self.check_notification_out('dataset_created', self.norman))

            self.clear_notifications_queue()
            _l.name = 'test notifications 2'
            _l.save(notify=True)
            self.assertTrue(self.check_notification_out('dataset_updated', self.u))

            self.clear_notifications_queue()
            lct = ContentType.objects.get_for_model(_l)

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
                self.assertTrue(self.check_notification_out('dataset_rated', self.u))


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
        self.sut = Dataset.objects.create(
            name="testLayer", owner=self.user, title='test', is_approved=True, uuid='abc-1234-abc'
        )

    def test_dataset_will_maintain_his_uud_if_no_handler_is_definded(self):
        expected = "abc-1234-abc"
        self.assertEqual(expected, self.sut.uuid)

    @override_settings(LAYER_UUID_HANDLER="geonode.layers.tests.DummyUUIDHandler")
    def test_dataset_will_override_the_uuid_if_handler_is_defined(self):
        resource_manager.update(None, instance=self.sut, keywords=["updating", "values"])
        expected = "abc:abc-1234-abc"
        actual = Dataset.objects.get(id=self.sut.id)
        self.assertEqual(expected, actual.uuid)

        self.assertIsNotNone(self.sut.ows_url)
        self.assertIsNotNone(self.sut.ptype)
        self.assertIsNotNone(self.sut.sourcetype)


class TestSetMetadata(TestCase):

    def setUp(self):
        self.maxDiff = None
        self.invalid_xml = "xml"
        self.exml_path = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        self.custom = [
            {
                "keywords": ["features", "test_dataset"],
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
            "title": "test_dataset"
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
            "title": "test_dataset"
        }

        self.keywords = [
            {
                "keywords": ["features", "test_dataset"],
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


class TestDatasetForm(GeoNodeBaseTestSupport):
    def setUp(self) -> None:
        self.user = get_user_model().objects.get(username='admin')
        self.dataset = create_single_dataset("my_single_layer", owner=self.user)
        self.sut = DatasetForm
        self.time_form = DatasetTimeSerieForm

    def test_resource_form_is_invalid_extra_metadata_not_json_format(self):
        self.client.login(username="admin", password="admin")
        url = reverse("dataset_metadata", args=(self.dataset.alternate,))
        response = self.client.post(url, data={
            "resource-owner": self.dataset.owner.id,
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
        url = reverse("dataset_metadata", args=(self.dataset.alternate,))
        response = self.client.post(url, data={
            "resource-owner": self.dataset.owner.id,
            "resource-title": "layer_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": "[{'key': 'value'}]"
        })
        expected = {"success": False, "errors": ["extra_metadata: EXTRA_METADATA_SCHEMA validation schema is not available for resource dataset"]}
        self.assertDictEqual(expected, response.json())

    def test_resource_form_is_invalid_extra_metadata_invalids_schema_entry(self):
        self.client.login(username="admin", password="admin")
        url = reverse("dataset_metadata", args=(self.dataset.alternate,))
        response = self.client.post(url, data={
            "resource-owner": self.dataset.owner.id,
            "resource-title": "layer_title",
            "resource-date": "2022-01-24 16:38 pm",
            "resource-date_type": "creation",
            "resource-language": "eng",
            "resource-extra_metadata": '[{"key": "value"},{"id": "int", "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        expected = "extra_metadata: Missing keys: \'field_label\', \'field_name\', \'field_value\', \'filter_header\' at index 0 "
        self.assertIn(expected, response.json()['errors'][0])

    def test_resource_form_is_valid_extra_metadata(self):
        form = self.sut(instance=self.dataset, data={
            "owner": self.dataset.owner.id,
            "title": "layer_title",
            "date": "2022-01-24 16:38 pm",
            "date_type": "creation",
            "language": "eng",
            "extra_metadata": '[{"id": 1, "filter_header": "object", "field_name": "object", "field_label": "object", "field_value": "object"}]'
        })
        self.assertTrue(form.is_valid())

    def test_dataset_time_form_should_work(self):

        attr, _ = Attribute.objects.get_or_create(
            dataset=self.dataset,
            attribute="field_date",
            attribute_type="xsd:dateTime"
        )
        self.dataset.attribute_set.add(attr)
        self.dataset.save()
        form = self.time_form(
            instance=self.dataset,
            data={
                'attribute': self.dataset.attributes.first().id,
                'end_attribute': '',
                'presentation': 'DISCRETE_INTERVAL',
                'precision_value': 12345,
                'precision_step': 'seconds'
            }
        )
        self.assertTrue(form.is_valid())
        self.assertDictEqual({}, form.errors)

    def test_dataset_time_form_should_raise_error_if_invalid_payload(self):

        attr, _ = Attribute.objects.get_or_create(
            dataset=self.dataset,
            attribute="field_date",
            attribute_type="xsd:dateTime"
        )
        self.dataset.attribute_set.add(attr)
        self.dataset.save()
        form = self.time_form(
            instance=self.dataset,
            data={
                'attribute': self.dataset.attributes.first().id,
                'end_attribute': '',
                'presentation': 'INVALID_PRESENTATION_VALUE',
                'precision_value': 12345,
                'precision_step': 'seconds'
            }
        )
        self.assertFalse(form.is_valid())
        self.assertTrue('presentation' in form.errors)
        self.assertEqual("Select a valid choice. INVALID_PRESENTATION_VALUE is not one of the available choices.", form.errors['presentation'][0])
