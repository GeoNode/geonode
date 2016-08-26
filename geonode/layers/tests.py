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

import os
import shutil
import tempfile
import zipfile
import StringIO

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from django.db.models import Count
from django.contrib.auth import get_user_model
from agon_ratings.models import OverallRating

from guardian.shortcuts import get_anonymous_user
from guardian.shortcuts import assign_perm, remove_perm

from geonode import GeoNodeException
from geonode.layers.models import Layer, Style
from geonode.layers.utils import layer_type, get_files, get_valid_name, \
    get_valid_layer_name
from geonode.people.utils import get_valid_user
from geonode.base.models import TopicCategory
from geonode.base.populate_test_data import create_models, all_public
from geonode.layers.forms import JSONField, LayerUploadForm
from .populate_layers_data import create_layer_data


class LayersTest(TestCase):

    """Tests geonode.layers app/module
    """

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_layer_data()
        self.anonymous_user = get_anonymous_user()

    # Data Tests

    def test_data(self):
        '''/data/ -> Test accessing the data page'''
        response = self.client.get(reverse('layer_browse'))
        self.failUnlessEqual(response.status_code, 200)

    def test_describe_data_2(self):
        '''/data/geonode:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(8, get_user_model().objects.all().count())
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)

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
        self.assertEqual(8, get_user_model().objects.all().count())
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('layer_metadata', args=('geonode:CA',)))
        self.failUnlessEqual(response.status_code, 200)

    def test_layer_attributes(self):
        lyr = Layer.objects.get(pk=1)
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

    def test_layer_attribute_config(self):
        lyr = Layer.objects.get(pk=1)
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
        lyr = Layer.objects.get(pk=1)
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
        lyr = Layer.objects.get(pk=1)
        lyr.keywords.add(*["saving", "keywords"])
        lyr.save()
        self.assertEqual(
            lyr.keyword_list(), [
                u'here', u'keywords', u'populartag', u'saving'])

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
        layer = Layer.objects.get(pk=3)
        layer.default_style = Style.objects.get(pk=layer.pk)
        layer.save()
        url = reverse('layer_remove', args=(layer.typename,))
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
        layer = Layer.objects.get(pk=1)
        url = reverse('layer_remove', args=(layer.typename,))
        layer.default_style = Style.objects.get(pk=layer.pk)
        layer.save()

        # test unauthenticated
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)

        # test a user without layer removal permission
        self.client.login(username='norman', password='norman')
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)
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
        self.assertEquals(response['Location'], 'http://testserver/layers/')

        # test that the layer is actually removed
        self.assertEquals(Layer.objects.filter(pk=layer.pk).count(), 0)

        # test that all styles associated to the layer are removed
        self.assertEquals(Style.objects.count(), 0)

    def test_non_cascading(self):
        """
        Tests that deleting a layer with a shared default style will not cascade and
        delete multiple layers.
        """
        layer1 = Layer.objects.get(pk=1)
        layer2 = Layer.objects.get(pk=2)
        url = reverse('layer_remove', args=(layer1.typename,))

        layer1.default_style = Style.objects.get(pk=layer1.pk)
        layer1.save()
        layer2.default_style = Style.objects.get(pk=layer1.pk)
        layer2.save()

        self.assertEquals(layer1.default_style, layer2.default_style)

        # Now test with a valid user
        self.client.login(username='admin', password='admin')

        # test the post method that actually removes the layer and redirects
        response = self.client.post(url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'], 'http://testserver/layers/')

        # test that the layer is actually removed

        self.assertEquals(Layer.objects.filter(pk=layer1.pk).count(), 0)
        self.assertEquals(Layer.objects.filter(pk=2).count(), 1)

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
        layer = Layer.objects.get(pk=1)
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


class UnpublishedObjectTests(TestCase):

    """Test the is_published base attribute"""

    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(UnpublishedObjectTests, self).setUp()

        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        create_models(type='layer')
        all_public()

    def test_unpublished_layer(self):
        """Test unpublished layer behaviour"""

        user = get_user_model().objects.get(username='bobby')
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

        # with resource publishing
        with self.settings(RESOURCE_PUBLISHING=True):
            # 404 if layer is unpublished
            response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
            self.failUnlessEqual(response.status_code, 404)
            # 200 if layer is unpublished but user has permission
            assign_perm('publish_resourcebase', user, layer.get_self_resource())
            response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
            self.failUnlessEqual(response.status_code, 200)
            # 200 if layer is published
            layer.is_published = True
            layer.save()
            remove_perm('publish_resourcebase', user, layer.get_self_resource())
            response = self.client.get(reverse('layer_detail', args=('geonode:CA',)))
            self.failUnlessEqual(response.status_code, 200)

        layer.is_published = True
        layer.save()
