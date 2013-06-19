# -*- coding: utf-8 -*-
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
import base64
import shutil
import tempfile

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User, AnonymousUser
from django.utils import simplejson as json
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from agon_ratings.models import OverallRating

import geonode.layers.utils
import geonode.layers.views
import geonode.layers.models

from geonode import GeoNodeException

from geonode.layers.models import Layer, Style
from geonode.layers.forms import JSONField, LayerUploadForm
from geonode.layers.utils import layer_type, get_files, get_valid_name, \
                                get_valid_layer_name
from geonode.people.utils import get_valid_user
from geonode.security.enumerations import ANONYMOUS_USERS, AUTHENTICATED_USERS
from geonode.base.models import TopicCategory
from geonode.search.populate_search_test_data import create_models
from .populate_layers_data import create_layer_data

from geoserver.resource import FeatureType, Coverage

class LayersTest(TestCase):
    """Tests geonode.layers app/module
    """

    fixtures = ['initial_data.json']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_layer_data()

    # Permissions Tests

    # Users
    # - admin (pk=2)
    # - bobby (pk=1)

    # Inherited
    # - LEVEL_NONE = _none

    # Layer
    # - LEVEL_READ = layer_read
    # - LEVEL_WRITE = layer_readwrite
    # - LEVEL_ADMIN = layer_admin

    # Map
    # - LEVEL_READ = map_read
    # - LEVEL_WRITE = map_readwrite
    # - LEVEL_ADMIN = map_admin


    # FIXME: Add a comprehensive set of permissions specifications that allow us
    # to test as many conditions as is possible/necessary

    # If anonymous and/or authenticated are not specified,
    # should set_layer_permissions remove any existing perms granted??

    perm_spec = {"anonymous":"_none","authenticated":"_none","users":[["admin","layer_readwrite"]]}
    def test_layer_set_default_permissions(self):
        """Verify that Layer.set_default_permissions is behaving as expected
        """

        # Get a Layer object to work with
        layer = Layer.objects.all()[0]

        # Set the default permissions
        layer.set_default_permissions()

        # Save the layers Current Permissions
        current_perms = layer.get_all_level_info()

        # Test that LEVEL_READ is set for ANONYMOUS_USERS and AUTHENTICATED_USERS
        self.assertEqual(layer.get_gen_level(ANONYMOUS_USERS), layer.LEVEL_READ)
        self.assertEqual(layer.get_gen_level(AUTHENTICATED_USERS), layer.LEVEL_READ)

        admin_perms = current_perms['users'][layer.owner.username]

        # Test that the owner was assigned LEVEL_ADMIN
        self.assertEqual(admin_perms, layer.LEVEL_ADMIN)

    def test_set_layer_permissions(self):
        """Verify that the set_layer_permissions view is behaving as expected
        """

        # Get a layer to work with
        layer = Layer.objects.all()[0]

        # FIXME Test a comprehensive set of permissions specifications

        # Set the Permissions

        geonode.layers.utils.layer_set_permissions(layer, self.perm_spec)

        # Test that the Permissions for ANONYMOUS_USERS and AUTHENTICATED_USERS were set correctly
        self.assertEqual(layer.get_gen_level(ANONYMOUS_USERS), layer.LEVEL_NONE)
        self.assertEqual(layer.get_gen_level(AUTHENTICATED_USERS), layer.LEVEL_NONE)

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the layers owner) were removed
        users = [n[0] for n in self.perm_spec['users']]
        levels = layer.get_user_levels().exclude(user__username__in = users + [layer.owner])
        self.assertEqual(len(levels), 0)

        # Test that the User permissions specified in the perm_spec were applied properly
        for username, level in self.perm_spec['users']:
            user = geonode.maps.models.User.objects.get(username=username)
            self.assertEqual(layer.get_user_level(user), level)

    def test_ajax_layer_permissions(self):
        """Verify that the ajax_layer_permissions view is behaving as expected
        """

        # Setup some layer names to work with
        valid_layer_typename = Layer.objects.all()[0].typename
        invalid_layer_typename = "n0ch@nc3"

        c = Client()

        # Test that an invalid layer.typename is handled for properly
        response = c.post(reverse('layer_permissions', args=(invalid_layer_typename,)),
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")
        self.assertEquals(response.status_code, 404)

        # Test that GET returns permissions
        response = c.get(reverse('layer_permissions', args=(valid_layer_typename,)))
        assert('permissions' in response.content)

        # Test that a user is required to have maps.change_layer_permissions

        # First test un-authenticated
        response = c.post(reverse('layer_permissions', args=(valid_layer_typename,)),
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = c.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = c.post(reverse('layer_permissions', args=(valid_layer_typename,)),
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        logged_in = c.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)

        response = c.post(reverse('layer_permissions', args=(valid_layer_typename,)),
                            data=json.dumps(self.perm_spec),
                            content_type="application/json")

        # Test that the method returns 200
        self.assertEquals(response.status_code, 200)

        # Test that the permissions specification is applied

        # Should we do this here, or assume the tests in
        # test_set_layer_permissions will handle for that?

    def test_layer_acls(self):
        """ Verify that the layer_acls view is behaving as expected
        """

        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = "%s:%s" % (settings.GEOSERVER_CREDENTIALS[0],settings.GEOSERVER_CREDENTIALS[1])
        invalid_uname_pw = "%s:%s" % ("n0t", "v@l1d")

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(valid_uname_pw),
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(invalid_uname_pw),
        }

        # Test that requesting when supplying the GEOSERVER_CREDENTIALS returns the expected json

        expected_result = {
            u'rw': [],
            u'ro': [],
            u'name': unicode(settings.GEOSERVER_CREDENTIALS[0]),
            u'is_superuser': True,
            u'is_anonymous': False
        }

        c = Client()
        response = c.get(reverse('layer_acls'), **valid_auth_headers)
        response_json = json.loads(response.content)
        self.assertEquals(expected_result, response_json)

        # Test that requesting when supplying invalid credentials returns the appropriate error code
        response = c.get(reverse('layer_acls'), **invalid_auth_headers)
        self.assertEquals(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        c.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = c.get(reverse('layer_acls'))
        response_json = json.loads(response.content)

        # TODO Lots more to do here once jj0hns0n understands the ACL system better

    def test_perms_info(self):
        """ Verify that the perms_info view is behaving as expected
        """

        # Test with a Layer object
        layer = Layer.objects.all()[0]
        layer_info = layer.get_all_level_info()
        info = geonode.security.views._perms_info(layer, geonode.layers.views.LAYER_LEV_NAMES)

        # Test that ANONYMOUS_USERS and AUTHENTICATED_USERS are set properly
        self.assertEqual(info[ANONYMOUS_USERS], layer.LEVEL_READ)
        self.assertEqual(info[AUTHENTICATED_USERS], layer.LEVEL_READ)

        self.assertEqual(info['users'], sorted(layer_info['users'].items()))

        # Test that layer owner can edit layer
        self.assertTrue(layer.owner.has_perm(set([u'layers.change_layer']), layer))

        # TODO Much more to do here once jj0hns0n understands the ACL system better

        # Test with a Map object
        # TODO

    # Data Tests

    def test_data(self):
        '''/data/ -> Test accessing the data page'''
        c = Client()
        response = c.get(reverse('layer_browse'))
        self.failUnlessEqual(response.status_code, 200)

    def test_describe_data_2(self):
        '''/data/base:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(7, User.objects.all().count())
        c = Client()
        response = c.get(reverse('layer_metadata', args=('base:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        c.login(username='admin', password='admin')
        # ... all should be good
        response = c.get(reverse('layer_metadata', args=('base:CA',)))
        self.failUnlessEqual(response.status_code, 200)

    # Layer Tests

    # Test layer upload endpoint
    def test_upload_layer(self):
        c = Client()

        # Test redirection to login form when not logged in
        response = c.get(reverse('data_upload'))
        self.assertEquals(response.status_code,302)
        # Test return of upload form when logged in
        c.login(username="bobby", password="bob")
        response = c.get(reverse('data_upload'))
        self.assertEquals(response.status_code,200)

    def test_describe_data(self):
        '''/data/base:CA/metadata -> Test accessing the description of a layer '''
        self.assertEqual(7, User.objects.all().count())
        c = Client()
        response = c.get(reverse('layer_metadata', args=('base:CA',)))
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 302)
        # but if we log in ...
        c.login(username='admin', password='admin')
        # ... all should be good
        response = c.get(reverse('layer_metadata', args=('base:CA',)))
        self.failUnlessEqual(response.status_code, 200)

    def test_layer_attributes(self):
        lyr = Layer.objects.get(pk=1)
        #There should be a total of 3 attributes
        self.assertEqual(len(lyr.attribute_set.all()), 3)
        #2 out of 3 attributes should be visible
        custom_attributes = lyr.attribute_set.visible()
        self.assertEqual(len(custom_attributes), 2)
        #place_ name should come before description
        self.assertEqual(custom_attributes[0].attribute_label, "Place Name")
        self.assertEqual(custom_attributes[1].attribute_label, "Description")
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
        self.assertEqual(custom_attributes["fields"],["place_name","description"])
        self.assertEqual(custom_attributes["propertyNames"]["description"], "Description")
        self.assertEqual(custom_attributes["propertyNames"]["place_name"], "Place Name")

    def test_layer_styles(self):
        lyr = Layer.objects.get(pk=1)
        #There should be a total of 3 styles
        self.assertEqual(len(lyr.styles.all()), 3)
        #One of the style is the default one
        self.assertEqual(lyr.default_style, Style.objects.get(id=lyr.default_style.id))

    def test_layer_save(self):
        lyr = Layer.objects.get(pk=1)
        lyr.keywords.add(*["saving", "keywords"])
        lyr.save()
        self.assertEqual(lyr.keyword_list(), ["populartag", "here", "keywords", "saving"])

    def test_get_valid_user(self):
        # Verify it accepts an admin user
        adminuser = User.objects.get(is_superuser=True)
        valid_user = get_valid_user(adminuser)
        msg = ('Passed in a valid admin user "%s" but got "%s" in return'
                % (adminuser, valid_user))
        assert valid_user.id == adminuser.id, msg

        # Verify it returns a valid user after receiving None
        valid_user = get_valid_user(None)
        msg = ('Expected valid user after passing None, got "%s"' % valid_user)
        assert isinstance(valid_user, User), msg

        newuser = User.objects.create(username='arieluser')
        valid_user = get_valid_user(newuser)
        msg = ('Passed in a valid user "%s" but got "%s" in return'
                % (newuser, valid_user))
        assert valid_user.id == newuser.id, msg

        valid_user = get_valid_user('arieluser')
        msg = ('Passed in a valid user by username "%s" but got'
               ' "%s" in return' % ('arieluser', valid_user))
        assert valid_user.username == 'arieluser', msg

        nn = AnonymousUser()
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


    def test_layer_type(self):
        self.assertEquals(layer_type('foo.shp'), FeatureType.resource_type)
        self.assertEquals(layer_type('foo.SHP'), FeatureType.resource_type)
        self.assertEquals(layer_type('foo.sHp'), FeatureType.resource_type)
        self.assertEquals(layer_type('foo.tif'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TIF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TiF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.geotif'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.GEOTIF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.gEoTiF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.tiff'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TIFF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.TiFf'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.geotiff'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.GEOTIFF'), Coverage.resource_type)
        self.assertEquals(layer_type('foo.gEoTiFf'), Coverage.resource_type)

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
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.shp", shp="foo.shp", shx="foo.shx",
                prj="foo.prj", dbf="foo.dbf"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that a Shapefile missing required components raises an exception
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()

            self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including an SLD with a valid shapefile results in the SLD getting picked up
        d = None
        try:
            d = tempfile.mkdtemp()
            for f in ("foo.shp", "foo.shx", "foo.prj", "foo.dbf", "foo.sld"):
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()

            gotten_files = get_files(os.path.join(d, "foo.shp"))
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.shp", shp="foo.shp", shx="foo.shx",
                prj="foo.prj", dbf="foo.dbf", sld="foo.sld"))
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
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.SHP", shp="foo.SHP", shx="foo.SHX",
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
            gotten_files = dict((k, v[len(d) + 1:]) for k, v in gotten_files.iteritems())
            self.assertEquals(gotten_files, dict(base="foo.SHP", shp="foo.SHP", shx="foo.shx",
                prj="foo.pRJ", dbf="foo.DBF"))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase extensions raises an exception
        d = None
        try:
            d = tempfile.mkdtemp()
            files = ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.shp", "foo.shx", "foo.prj", "foo.dbf")
            for f in files:
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))

        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase PRJ (this is special-cased in the implementation)
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
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
        finally:
            if d is not None:
                shutil.rmtree(d)

        # Check that including both capital and lowercase SLD (this is special-cased in the implementation)
        d = None
        try:
            d = tempfile.mkdtemp()
            files = ("foo.SHP", "foo.SHX", "foo.PRJ", "foo.DBF", "foo.SLD", "foo.sld")
            for f in files:
                path = os.path.join(d, f)
                # open and immediately close to create empty file
                open(path, 'w').close()

            # Only run the tests if this is a case sensitive OS
            if len(os.listdir(d)) == len(files):
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.SHP")))
                self.assertRaises(GeoNodeException, lambda: get_files(os.path.join(d, "foo.shp")))
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

    ## NOTE: we don't care about file content for many of these tests (the
    ## forms under test validate based only on file name, and leave actual
    ## content inspection to GeoServer) but Django's form validation will omit
    ## any files with empty bodies.
    ##
    ## That is, this leads to mysterious test failures:
    ##     SimpleUploadedFile('foo', '')
    ##
    ## And this should be used instead to avoid that:
    ##     SimpleUploadedFile('foo', ' ')


    def testJSONField(self):
        field = JSONField()
        # a valid JSON document should pass
        field.clean('{ "users": [] }')

        # text which is not JSON should fail
        self.assertRaises(ValidationError, lambda: field.clean('<users></users>'))

    def test_feature_edit_check(self):
        """Verify that the feature_edit_check view is behaving as expected
        """

        # Setup some layer names to work with
        valid_layer_typename = Layer.objects.all()[0].typename
        invalid_layer_typename = "n0ch@nc3"

        c = Client()

        # Test that an invalid layer.typename is handled for properly
        response = c.post(reverse('feature_edit_check', args=(invalid_layer_typename,)))
        self.assertEquals(response.status_code, 404)


        # First test un-authenticated
        response = c.post(reverse('feature_edit_check', args=(valid_layer_typename,)))
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        # Next Test with a user that does NOT have the proper perms
        logged_in = c.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = c.post(reverse('feature_edit_check', args=(valid_layer_typename,)))
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        # Login as a user with the proper permission and test the endpoint
        logged_in = c.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)

        response = c.post(reverse('feature_edit_check', args=(valid_layer_typename,)))

        # Test that the method returns 401 because it's not a datastore
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        layer = Layer.objects.all()[0]
        layer.storeType = "dataStore"
        layer.save()


        # Test that the method returns authorized=True if it's a datastore
        with self.settings(DB_DATASTORE=True):
            # The check was moved from the template into the view
            response = c.post(reverse('feature_edit_check', args=(valid_layer_typename,)))
            response_json = json.loads(response.content)
            self.assertEquals(response_json['authorized'], True)

    def test_rating_layer_remove(self):
        """ Test layer rating is removed on layer remove
        """
        #Get the layer to work with
        layer = Layer.objects.get(pk=3)
        layer.default_style = Style.objects.get(pk=layer.pk)
        layer.save()
        url = reverse('layer_remove', args=(layer.typename,))
        layer_id = layer.id

        #Create the rating with the correct content type
        ctype = ContentType.objects.get(model='layer')
        OverallRating.objects.create(category=2,object_id=layer_id,content_type=ctype, rating=3)

        c = Client()

        c.login(username='admin', password='admin')

        #Remove the layer
        c.post(url)

        #Check there are no ratings matching the remove layer
        rating = OverallRating.objects.filter(category=2,object_id=layer_id)
        self.assertEquals(rating.count(),0)

    def test_layer_remove(self):
        """Test layer remove functionality
        """
        layer = Layer.objects.get(pk = 1)
        url = reverse('layer_remove', args=(layer.typename,))
        layer.default_style = Style.objects.get(pk=layer.pk)
        layer.save()
        c = Client()

        # test unauthenticated
        response = c.get(url)
        self.assertEquals(response.status_code, 302)

        #test a user without layer removal permission
        c = Client()
        c.login(username='norman', password='norman')
        response = c.post(url)
        self.assertEquals(response.status_code, 302)
        c.logout()

        # Now test with a valid user
        c = Client()
        c.login(username='admin', password='admin')

        #test a method other than POST and GET
        response = c.put(url)
        self.assertEquals(response.status_code, 403)

        #test the page with a valid user with layer removal permission
        response = c.get(url)
        self.assertEquals(response.status_code, 200)

        #test the post method that actually removes the layer and redirects
        response = c.post(url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(response['Location'], 'http://testserver/layers/')

        #test that the layer is actually removed
        self.assertEquals(Layer.objects.filter(pk=layer.pk).count(), 0)
        
        #test that all styles associated to the layer are removed
        self.assertEquals(Style.objects.count(), 0)

    def test_category_counts(self):
        location = TopicCategory.objects.get(slug='location')
        # there are three layers with location category
        self.assertEquals(location.layers_count,3)

        # change the category of one layers_count
        layer = Layer.objects.filter(category=location)[0]
        elevation = TopicCategory.objects.get(slug='elevation')
        layer.category = elevation
        layer.save()
        
        #reload the categories since it's caching the old count
        location = TopicCategory.objects.get(slug='location')
        elevation = TopicCategory.objects.get(slug='elevation')
        self.assertEquals(location.layers_count,2)
        self.assertEquals(elevation.layers_count,4)

        # delete a layer and check the count update
        # use the first since it's the only one which has styles
        layer =  Layer.objects.get(pk=1)
        elevation = TopicCategory.objects.get(slug='elevation')
        self.assertEquals(elevation.layers_count,4)
        layer.delete()
        elevation = TopicCategory.objects.get(slug='elevation')
        self.assertEquals(elevation.layers_count,3)