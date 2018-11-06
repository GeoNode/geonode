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
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from geonode.tests.base import GeoNodeBaseTestSupport

import os
import shutil
import tempfile
import zipfile
import StringIO
import contextlib
import json
from datetime import datetime

import gisdata

from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Group

from django.db.models import Count
from django.contrib.auth import get_user_model
from agon_ratings.models import OverallRating

from django.test.utils import override_settings

from guardian.shortcuts import get_anonymous_user
from guardian.shortcuts import assign_perm, remove_perm

from geonode import GeoNodeException, geoserver, qgis_server
from geonode.decorators import on_ogc_backend
from geonode.layers.models import Layer, Style
from geonode.layers.utils import layer_type, get_files, get_valid_name, \
    get_valid_layer_name
from geonode.people.utils import get_valid_user
from geonode.base.models import TopicCategory, License, Region, Link
from geonode.base.populate_test_data import all_public
from geonode.layers.forms import JSONField, LayerUploadForm
from geonode.utils import check_ogc_backend
from .populate_layers_data import create_layer_data
from geonode.tests.utils import NotificationsTestsHelper
from geonode.layers import LayersAppConfig

import logging

logger = logging.getLogger(__name__)


class LayersTest(GeoNodeBaseTestSupport):

    """Tests geonode.layers app/module
    """
    type = 'layer'

    def setUp(self):
        super(LayersTest, self).setUp()

        create_layer_data()
        self.user = 'admin'
        self.passwd = 'admin'
        self.anonymous_user = get_anonymous_user()

    # Data Tests

    def test_data(self):
        '''/data/ -> Test accessing the data page'''
        response = self.client.get(reverse('layer_browse'))
        self.failUnlessEqual(response.status_code, 200)

    def test_describe_data_2(self):
        '''/data/geonode:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(10, get_user_model().objects.all().count())
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)

    def test_describe_data_3(self):
        '''/data/geonode:CA/metadata_detail -> Test accessing the description of a layer '''
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata_detail', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)
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
        self.failUnlessEqual(response.status_code, 200)
        self.assertContains(response, "<dt>Group</dt>", count=1, status_code=200, msg_prefix='', html=False)
        lyr.group = None
        lyr.save()

    # Layer Tests

    # Test layer upload endpoint
    def test_upload_layer(self):
        # Test redirection to login form when not logged in
        response = self.client.get(reverse('layer_upload'))
        self.assertEquals(response.status_code, 302)

        # Test return of upload form when logged in
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse('layer_upload'))
        self.assertEquals(response.status_code, 200)

    def test_describe_data(self):
        '''/data/geonode:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(10, get_user_model().objects.all().count())
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)

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
            u'N\xfamero_De_M\xe9dicos')
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
        logger.info(layer_bbox)

        def decimal_encode(bbox):
            import decimal
            _bbox = []
            for o in [float(coord) for coord in bbox]:
                if isinstance(o, decimal.Decimal):
                    o = (str(o) for o in [o])
                _bbox.append(o)
            # Must be in the form : [x0, x1, y0, y1
            return [_bbox[0], _bbox[2], _bbox[1], _bbox[3]]

        from geonode.utils import bbox_to_projection
        projected_bbox = decimal_encode(
            bbox_to_projection([float(coord) for coord in layer_bbox] + [lyr.srid, ],
                               target_srid=4326)[:4])
        logger.info(projected_bbox)
        self.assertEquals(projected_bbox, [-180.0, -90.0, 180.0, 90.0])
        logger.info(lyr.ll_bbox)
        self.assertEquals(lyr.ll_bbox, [-180.0, 180.0, -90.0, 90.0, u'EPSG:4326'])
        projected_bbox = decimal_encode(
            bbox_to_projection([float(coord) for coord in layer_bbox] + [lyr.srid, ],
                               target_srid=3857)[:4])
        logger.info(projected_bbox)
        self.assertEquals(projected_bbox, [-20037397.0233, -74299743.4007, 20037397.0233, 74299743.4006])

    def test_layer_attributes_feature_catalogue(self):
        """ Test layer feature catalogue functionality
        """
        # test a non-existing layer
        url = reverse('layer_feature_catalogue', args=('bad_layer',))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 404)

        # Get the layer to work with
        layer = Layer.objects.all()[3]
        url = reverse('layer_feature_catalogue', args=(layer.alternate,))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response['content-type'], 'application/xml')

    def test_layer_attribute_config(self):
        lyr = Layer.objects.all().first()
        custom_attributes = (lyr.attribute_config())["getFeatureInfo"]
        self.assertEqual(
            custom_attributes["fields"], [
                "place_name", "description", u'N\xfamero_De_M\xe9dicos'])
        self.assertEqual(
            custom_attributes["propertyNames"]["description"],
            "Description")
        self.assertEqual(
            custom_attributes["propertyNames"]["place_name"],
            "Place Name")

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
            lyr.keyword_list(), [
                u'here', u'keywords', u'populartag', u'saving'])

    def test_layer_links(self):
        lyr = Layer.objects.filter(storeType="dataStore").first()
        self.assertEquals(lyr.storeType, "dataStore")
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            self.assertEquals(len(links), 7)
            for ll in links:
                self.assertEquals(ll.link_type, "metadata")

        lyr = Layer.objects.filter(storeType="coverageStore").first()
        self.assertEquals(lyr.storeType, "coverageStore")
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            links = Link.objects.filter(resource=lyr.resourcebase_ptr, link_type="metadata")
            self.assertIsNotNone(links)
            self.assertEquals(len(links), 7)
            for ll in links:
                self.assertEquals(ll.link_type, "metadata")

    def test_get_valid_user(self):
        # Verify it accepts an admin user
        adminuser = get_user_model().objects.get(is_superuser=True)
        valid_user = get_valid_user(adminuser)
        msg = ('Passed in a valid admin user "%s" but got "%s" in return'
               % (adminuser, valid_user))
        assert valid_user.id == adminuser.id, msg

        # Verify it returns a valid user after receiving None
        valid_user = get_valid_user(None)
        msg = ('Expected valid user after passing None, got "%s"' % valid_user)
        assert isinstance(valid_user, get_user_model()), msg

        newuser = get_user_model().objects.create(username='arieluser')
        valid_user = get_valid_user(newuser)
        msg = ('Passed in a valid user "%s" but got "%s" in return'
               % (newuser, valid_user))
        assert valid_user.id == newuser.id, msg

        valid_user = get_valid_user('arieluser')
        msg = ('Passed in a valid user by username "%s" but got'
               ' "%s" in return' % ('arieluser', valid_user))
        assert valid_user.username == 'arieluser', msg

        nn = get_anonymous_user()
        self.assertRaises(GeoNodeException, get_valid_user, nn)

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

    def testASCIIValidation(self):
        files = dict(base_file=SimpleUploadedFile('foo.asc', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

        files = dict(base_file=SimpleUploadedFile('foo.ASC', ' '))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())

    def testZipValidation(self):
        the_zip = zipfile.ZipFile('test_upload.zip', 'w')
        in_memory_file = StringIO.StringIO()
        in_memory_file.write('test')
        the_zip.writestr('foo.shp', in_memory_file.getvalue())
        the_zip.writestr('foo.dbf', in_memory_file.getvalue())
        the_zip.writestr('foo.shx', in_memory_file.getvalue())
        the_zip.writestr('foo.prj', in_memory_file.getvalue())
        the_zip.close()
        files = dict(base_file=SimpleUploadedFile('test_upload.zip', open('test_upload.zip').read()))
        self.assertTrue(LayerUploadForm(dict(), files).is_valid())
        os.remove('test_upload.zip')

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

        the_zip = zipfile.ZipFile('test_upload.zip', 'w')
        in_memory_file = StringIO.StringIO()
        in_memory_file.write('test')
        the_zip.writestr('foo.shp', in_memory_file.getvalue())
        the_zip.writestr('foo.dbf', in_memory_file.getvalue())
        the_zip.writestr('foo.shx', in_memory_file.getvalue())
        the_zip.writestr('foo.prj', in_memory_file.getvalue())
        the_zip.close()
        files = dict(base_file=SimpleUploadedFile('test_upload.zip', open('test_upload.zip').read()))
        form = LayerUploadForm(dict(), files)
        self.assertTrue(form.is_valid())
        tempdir = form.write_files()[0]
        self.assertEquals(set(os.listdir(tempdir)),
                          set(['foo.shp', 'foo.shx', 'foo.dbf', 'foo.prj']))
        os.remove('test_upload.zip')

    def test_layer_type(self):
        self.assertEquals(layer_type('foo.shp'), 'vector')
        self.assertEquals(layer_type('foo.SHP'), 'vector')
        self.assertEquals(layer_type('foo.sHp'), 'vector')
        self.assertEquals(layer_type('foo.tif'), 'raster')
        self.assertEquals(layer_type('foo.TIF'), 'raster')
        self.assertEquals(layer_type('foo.TiF'), 'raster')
        self.assertEquals(layer_type('foo.geotif'), 'raster')
        self.assertEquals(layer_type('foo.GEOTIF'), 'raster')
        self.assertEquals(layer_type('foo.gEoTiF'), 'raster')
        self.assertEquals(layer_type('foo.tiff'), 'raster')
        self.assertEquals(layer_type('foo.TIFF'), 'raster')
        self.assertEquals(layer_type('foo.TiFf'), 'raster')
        self.assertEquals(layer_type('foo.geotiff'), 'raster')
        self.assertEquals(layer_type('foo.GEOTIFF'), 'raster')
        self.assertEquals(layer_type('foo.gEoTiFf'), 'raster')
        self.assertEquals(layer_type('foo.asc'), 'raster')
        self.assertEquals(layer_type('foo.ASC'), 'raster')
        self.assertEquals(layer_type('foo.AsC'), 'raster')

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
            gotten_files = dict((k, v[len(d) + 1:])
                                for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(shp="foo.shp", shx="foo.shx",
                                                 prj="foo.prj", dbf="foo.dbf"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that a Shapefile missing required components raises an
        # exception
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()

            self.assertRaises(
                GeoNodeException,
                lambda: get_files(
                    os.path.join(
                        d,
                        "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including an SLD with a valid shapefile results in the SLD
        # getting picked up
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            d = None
            try:
                d = tempfile.mkdtemp()
                for f in ("foo.shp", "foo.shx", "foo.prj", "foo.dbf", "foo.sld"):
                    path = os.path.join(d, f)
                    # open and immediately close to create empty file
                    open(path, 'w').close()

                gotten_files = get_files(os.path.join(d, "foo.shp"))
                gotten_files = dict((k, v[len(d) + 1:])
                                    for k, v in gotten_files.iteritems())
                self.assertEquals(
                    gotten_files,
                    dict(
                        shp="foo.shp",
                        shx="foo.shx",
                        prj="foo.prj",
                        dbf="foo.dbf",
                        sld="foo.sld"))
            finally:
                if d is not None:
                    shutil.rmtree(d)

        # Check that including a QML with a valid shapefile
        # results in the QML
        # getting picked up
        if check_ogc_backend(qgis_server.BACKEND_PACKAGE):
            d = None
            try:
                d = tempfile.mkdtemp()
                for f in (
                        "foo.shp", "foo.shx", "foo.prj", "foo.dbf", "foo.qml",
                        "foo.json"):
                    path = os.path.join(d, f)
                    # open and immediately close to create empty file
                    open(path, 'w').close()

                gotten_files = get_files(os.path.join(d, "foo.shp"))
                gotten_files = dict((k, v[len(d) + 1:])
                                    for k, v in gotten_files.iteritems())
                self.assertEquals(
                    gotten_files,
                    dict(
                        shp="foo.shp",
                        shx="foo.shx",
                        prj="foo.prj",
                        dbf="foo.dbf",
                        qml="foo.qml",
                        json="foo.json"))
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
            gotten_files = dict((k, v[len(d) + 1:])
                                for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(shp="foo.SHP", shx="foo.SHX",
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
            gotten_files = dict((k, v[len(d) + 1:])
                                for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(shp="foo.SHP", shx="foo.shx",
                                                 prj="foo.pRJ", dbf="foo.DBF"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase extensions raises an
        # exception
        d = None
        try:
            d = tempfile.mkdtemp()
            files = (
                "foo.SHP",
                "foo.SHX",
                "foo.PRJ",
                "foo.DBF",
                "foo.shp",
                "foo.shx",
                "foo.prj",
                "foo.dbf")
            for f in files:
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(files):
                self.assertRaises(
                    GeoNodeException,
                    lambda: get_files(
                        os.path.join(
                            d,
                            "foo.SHP")))
                self.assertRaises(
                    GeoNodeException,
                    lambda: get_files(
                        os.path.join(
                            d,
                            "foo.shp")))

        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase PRJ (this is
        # special-cased in the implementation)
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
                self.assertRaises(
                    GeoNodeException,
                    lambda: get_files(
                        os.path.join(
                            d,
                            "foo.SHP")))
                self.assertRaises(
                    GeoNodeException,
                    lambda: get_files(
                        os.path.join(
                            d,
                            "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase SLD (this is
        # special-cased in the implementation)
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            d = None
            try:
                d = tempfile.mkdtemp()
                files = (
                    "foo.SHP",
                    "foo.SHX",
                    "foo.PRJ",
                    "foo.DBF",
                    "foo.SLD",
                    "foo.sld")
                for f in files:
                    path = os.path.join(d, f)
                    # open and immediately close to create empty file
                    open(path, 'w').close()

                # Only run the tests if this is a case sensitive OS
                if len(os.listdir(d)) == len(files):
                    self.assertRaises(
                        GeoNodeException,
                        lambda: get_files(
                            os.path.join(
                                d,
                                "foo.SHP")))
                    self.assertRaises(
                        GeoNodeException,
                        lambda: get_files(
                            os.path.join(
                                d,
                                "foo.shp")))
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

    # NOTE: we don't care about file content for many of these tests (the
    # forms under test validate based only on file name, and leave actual
    # content inspection to GeoServer) but Django's form validation will omit
    # any files with empty bodies.
    #
    # That is, this leads to mysterious test failures:
    #     SimpleUploadedFile('foo', '')
    #
    # And this should be used instead to avoid that:
    #     SimpleUploadedFile('foo', ' ')

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
        url = reverse('layer_remove', args=(layer.alternate,))
        layer_id = layer.id

        # Create the rating with the correct content type
        ctype = ContentType.objects.get(model='layer')
        OverallRating.objects.create(
            category=2,
            object_id=layer_id,
            content_type=ctype,
            rating=3)

        self.client.login(username='admin', password='admin')

        # Remove the layer
        self.client.post(url)

        # Check there are no ratings matching the remove layer
        rating = OverallRating.objects.filter(category=2, object_id=layer_id)
        self.assertEquals(rating.count(), 0)

    def test_layer_remove(self):
        """Test layer remove functionality
        """
        layer = Layer.objects.all().first()
        url = reverse('layer_remove', args=(layer.alternate,))

        # test unauthenticated
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

        # test a user without layer removal permission
        self.client.login(username='norman', password='norman')
        response = self.client.post(url)
        self.assertEquals(response.status_code, 401)
        self.client.logout()

        # Now test with a valid user
        self.client.login(username='admin', password='admin')

        # test a method other than POST and GET
        response = self.client.put(url)
        self.assertEquals(response.status_code, 403)

        # test the page with a valid user with layer removal permission
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)

        # test the post method that actually removes the layer and redirects
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)
        self.assertTrue('/layers/' in response['Location'])

        # test that the layer is actually removed
        self.assertEquals(Layer.objects.filter(pk=layer.pk).count(), 0)

        # test that all styles associated to the layer are removed
        self.assertEquals(Style.objects.count(), 0)

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

        self.assertEquals(layer1.default_style, layer2.default_style)

        # Now test with a valid user
        self.client.login(username='admin', password='admin')

        # test the post method that actually removes the layer and redirects
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)
        self.assertTrue('/layers/' in response['Location'])

        # test that the layer is actually removed

        self.assertEquals(Layer.objects.filter(pk=layer1.pk).count(), 0)
        self.assertEquals(Layer.objects.filter(pk=layer2.pk).count(), 1)

        # test that all styles associated to the layer are removed
        self.assertEquals(Style.objects.count(), 1)

    def test_category_counts(self):
        topics = TopicCategory.objects.all()
        topics = topics.annotate(
            **{'layer_count': Count('resourcebase__layer__category')})
        location = topics.get(identifier='location')
        # there are three layers with location category
        self.assertEquals(location.layer_count, 3)

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
        self.assertEquals(location.layer_count, 2)
        self.assertEquals(elevation.layer_count, 4)

        # delete a layer and check the count update
        # use the first since it's the only one which has styles
        layer = Layer.objects.all().first()
        elevation = topics.get(identifier='elevation')
        self.assertEquals(elevation.layer_count, 4)
        layer.delete()
        topics = topics.annotate(
            **{'layer_count': Count('resourcebase__layer__category')})
        elevation = topics.get(identifier='elevation')
        self.assertEquals(elevation.layer_count, 3)

    def test_assign_change_layer_data_perm(self):
        """
        Ensure set_permissions supports the change_layer_data permission.
        """
        layer = Layer.objects.first()
        user = get_anonymous_user()
        layer.set_permissions({'users': {user.username: ['change_layer_data']}})
        perms = layer.get_all_level_info()
        self.assertIn('change_layer_data', perms['users'][user])

    def test_batch_edit(self):
        Model = Layer
        view = 'layer_batch_metadata'
        resources = Model.objects.all()[:3]
        ids = ','.join([str(element.pk) for element in resources])
        # test non-admin access
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse(view, args=(ids,)))
        self.assertEquals(response.status_code, 401)
        # test group change
        group = Group.objects.first()
        self.client.login(username='admin', password='admin')
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'group': group.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.group, group)
        # test owner change
        owner = get_user_model().objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'owner': owner.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.owner, owner)
        # test license change
        license = License.objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'license': license.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.license, license)
        # test regions change
        region = Region.objects.first()
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'region': region.pk},
        )
        self.assertEquals(response.status_code, 302)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            if resource.regions.all():
                self.assertTrue(region in resource.regions.all())
        # test date change
        from django.utils import timezone
        date = datetime.now(timezone.get_current_timezone())
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'date': date},
        )
        self.assertEquals(response.status_code, 200)
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            today = date.today()
            todoc = resource.date.today()
            self.assertEquals((today.day, today.month, today.year),
                              (todoc.day, todoc.month, todoc.year))

        # test language change
        language = 'eng'
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'language': language},
        )
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            self.assertEquals(resource.language, language)
        # test keywords change
        keywords = 'some,thing,new'
        response = self.client.post(
            reverse(view, args=(ids,)),
            data={'keywords': keywords},
        )
        resources = Model.objects.filter(id__in=[r.pk for r in resources])
        for resource in resources:
            for word in resource.keywords.all():
                self.assertTrue(word.name in keywords.split(','))


class UnpublishedObjectTests(GeoNodeBaseTestSupport):

    """Test the is_published base attribute"""
    type = 'layer'

    def setUp(self):
        super(UnpublishedObjectTests, self).setUp()

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
        self.failUnlessEqual(response.status_code, 200)
        layer = Layer.objects.filter(title='CA')[0]
        layer.is_published = False
        layer.save()
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)

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
        self.failUnlessEqual(response.status_code, 404)

        # 404 if layer is unpublished but user has permission but does not belong to the group
        assign_perm('publish_resourcebase', user, layer.get_self_resource())
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 404)

        # 200 if layer is unpublished and user is owner
        remove_perm('publish_resourcebase', user, layer.get_self_resource())
        layer.owner = user
        layer.save()
        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)

        # 200 if layer is published
        layer.is_published = True
        layer.save()

        response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)

        layer.is_published = True
        layer.save()


class LayerModerationTestCase(GeoNodeBaseTestSupport):

    type = 'layer'

    def setUp(self):
        super(LayerModerationTestCase, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        create_layer_data()
        self.anonymous_user = get_anonymous_user()
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()

    def _get_input_paths(self):
        base_name = 'single_point'
        suffixes = 'shp shx dbf prj'.split(' ')
        base_path = gisdata.GOOD_DATA
        paths = [os.path.join(base_path, 'vector', '{}.{}'.format(base_name, suffix)) for suffix in suffixes]
        return paths, suffixes,

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_moderated_upload(self):
        """
        Test if moderation flag works
        """
        with self.settings(ADMIN_MODERATE_UPLOADS=False):
            layer_upload_url = reverse('layer_upload')
            self.client.login(username=self.user, password=self.passwd)

            # we get list of paths to shp files and list of suffixes
            input_paths, suffixes = self._get_input_paths()

            # we need file objects from above..
            input_files = [open(fp, 'rb') for fp in input_paths]

            # ..but also specific mapping for upload
            files = dict(zip(['{}_file'.format(s) for s in suffixes], input_files))

            # don't forget about renaming main file
            files['base_file'] = files.pop('shp_file')

            with contextlib.nested(*input_files):
                files['permissions'] = '{}'
                files['charset'] = 'utf-8'
                files['layer_title'] = 'test layer'
                resp = self.client.post(layer_upload_url, data=files)
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.content)
            lname = data['url'].split(':')[-1]
            _l = Layer.objects.get(name=lname)

            self.assertTrue(_l.is_published)
            _l.delete()

        with self.settings(ADMIN_MODERATE_UPLOADS=True):
            layer_upload_url = reverse('layer_upload')
            self.client.login(username=self.user, password=self.passwd)

            # we get list of paths to shp files and list of suffixes
            input_paths, suffixes = self._get_input_paths()

            # we need file objects from above..
            input_files = [open(fp, 'rb') for fp in input_paths]

            # ..but also specific mapping for upload
            files = dict(zip(['{}_file'.format(s) for s in suffixes], input_files))

            # don't forget about renaming main file
            files['base_file'] = files.pop('shp_file')

            with contextlib.nested(*input_files):
                files['permissions'] = '{}'
                files['charset'] = 'utf-8'
                files['layer_title'] = 'test layer'
                resp = self.client.post(layer_upload_url, data=files)
            self.assertEqual(resp.status_code, 200)
            data = json.loads(resp.content)
            lname = data['url'].split(':')[-1]
            _l = Layer.objects.get(name=lname)

            self.assertFalse(_l.is_published)
            _l.delete()


class LayerNotificationsTestCase(NotificationsTestsHelper):

    type = 'layer'

    def setUp(self):
        super(LayerNotificationsTestCase, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        create_layer_data()
        self.anonymous_user = get_anonymous_user()
        self.u = get_user_model().objects.get(username=self.user)
        self.u.email = 'test@email.com'
        self.u.is_active = True
        self.u.save()
        self.setup_notifications_for(LayersAppConfig.NOTIFICATIONS, self.u)

    def testLayerNotifications(self):
        with self.settings(PINAX_NOTIFICATIONS_QUEUE_ALL=True):
            self.clear_notifications_queue()
            _l = Layer.objects.create(
                name='test notifications',
                bbox_x0=-180,
                bbox_x1=180,
                bbox_y0=-90,
                bbox_y1=90,
                srid='EPSG:4326')
            _l.name = 'test notifications 2'
            _l.save()
            self.assertTrue(self.check_notification_out('layer_updated', self.u))

            from dialogos.models import Comment
            lct = ContentType.objects.get_for_model(_l)
            comment = Comment(author=self.u, name=self.u.username,
                              content_type=lct, object_id=_l.id,
                              content_object=_l, comment='test comment')
            comment.save()

            self.assertTrue(self.check_notification_out('layer_comment', self.u))
