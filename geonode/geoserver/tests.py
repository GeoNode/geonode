import base64
import json

from django.contrib.auth import get_user_model
from django.http import HttpRequest
from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.utils import override_settings

from guardian.shortcuts import assign_perm, get_anonymous_user

from geonode.geoserver.helpers import OGC_Servers_Handler
from geonode.base.populate_test_data import create_models
from geonode.layers.populate_layers_data import create_layer_data
from geonode.layers.models import Layer


class LayerTests(TestCase):

    fixtures = ['bobby']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_layer_data()

    def test_style_manager(self):
        """
        Ensures the layer_style_manage route returns a 200.
        """
        layer = Layer.objects.all()[0]

        bob = get_user_model().objects.get(username='bobby')
        assign_perm('change_layer_style', bob, layer)

        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.get(reverse('layer_style_manage', args=(layer.typename,)))
        self.assertEqual(response.status_code, 200)

    def test_feature_edit_check(self):
        """Verify that the feature_edit_check view is behaving as expected
        """

        # Setup some layer names to work with
        valid_layer_typename = Layer.objects.all()[0].typename
        Layer.objects.all()[0].set_default_permissions()
        invalid_layer_typename = "n0ch@nc3"

        # Test that an invalid layer.typename is handled for properly
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    invalid_layer_typename,
                )))
        self.assertEquals(response.status_code, 404)

        # First test un-authenticated
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)

        response = self.client.post(
            reverse(
                'feature_edit_check',
                args=(
                    valid_layer_typename,
                )))

        # Test that the method returns 401 because it's not a datastore
        response_json = json.loads(response.content)
        self.assertEquals(response_json['authorized'], False)

        layer = Layer.objects.all()[0]
        layer.storeType = "dataStore"
        layer.save()

        # Test that the method returns authorized=True if it's a datastore
        if settings.OGC_SERVER['default']['DATASTORE']:
            # The check was moved from the template into the view
            response = self.client.post(
                reverse(
                    'feature_edit_check',
                    args=(
                        valid_layer_typename,
                    )))
            response_json = json.loads(response.content)
            self.assertEquals(response_json['authorized'], True)

    def test_layer_acls(self):
        """ Verify that the layer_acls view is behaving as expected
        """

        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = '%s:%s' % ('bobby', 'bob')
        invalid_uname_pw = '%s:%s' % ('n0t', 'v@l1d')

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(valid_uname_pw),
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' +
            base64.b64encode(invalid_uname_pw),
        }

        bob = get_user_model().objects.get(username='bobby')
        layer_ca = Layer.objects.get(typename='geonode:CA')
        assign_perm('change_layer_data', bob, layer_ca)

        # Test that requesting when supplying the geoserver credentials returns
        # the expected json

        expected_result = {
            u'email': u'bobby@bob.com',
            u'fullname': u'bobby',
            u'is_anonymous': False,
            u'is_superuser': False,
            u'name': u'bobby',
            u'ro': [u'geonode:layer2',
                     u'geonode:mylayer',
                     u'geonode:foo',
                     u'geonode:whatever',
                     u'geonode:fooey',
                     u'geonode:quux',
                     u'geonode:fleem'],
            u'rw': [u'geonode:CA']
        }
        response = self.client.get(reverse('layer_acls'), **valid_auth_headers)
        response_json = json.loads(response.content)
        # 'ro' and 'rw' are unsorted collections
        self.assertEquals(sorted(expected_result), sorted(response_json))

        # Test that requesting when supplying invalid credentials returns the
        # appropriate error code
        response = self.client.get(reverse('layer_acls'), **invalid_auth_headers)
        self.assertEquals(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('layer_acls'))
        response_json = json.loads(response.content)

        self.assertEquals('admin', response_json['fullname'])
        self.assertEquals('', response_json['email'])

        # TODO Lots more to do here once jj0hns0n understands the ACL system
        # better

    def test_resolve_user(self):
        """Verify that the resolve_user view is behaving as expected
        """
        # Test that HTTP_AUTHORIZATION in request.META is working properly
        valid_uname_pw = "%s:%s" % ('admin', 'admin')
        invalid_uname_pw = "%s:%s" % ("n0t", "v@l1d")

        valid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' + base64.b64encode(valid_uname_pw),
        }

        invalid_auth_headers = {
            'HTTP_AUTHORIZATION': 'basic ' +
            base64.b64encode(invalid_uname_pw),
        }

        response = self.client.get(reverse('layer_resolve_user'), **valid_auth_headers)
        response_json = json.loads(response.content)
        self.assertEquals({'geoserver': False,
                           'superuser': True,
                           'user': 'admin',
                           'fullname': 'admin',
                           'email': ''},
                          response_json)

        # Test that requesting when supplying invalid credentials returns the
        # appropriate error code
        response = self.client.get(reverse('layer_acls'), **invalid_auth_headers)
        self.assertEquals(response.status_code, 401)

        # Test logging in using Djangos normal auth system
        self.client.login(username='admin', password='admin')

        # Basic check that the returned content is at least valid json
        response = self.client.get(reverse('layer_resolve_user'))
        response_json = json.loads(response.content)

        self.assertEquals('admin', response_json['user'])
        self.assertEquals('admin', response_json['fullname'])
        self.assertEquals('', response_json['email'])


class UtilsTests(TestCase):

    def setUp(self):
        self.OGC_DEFAULT_SETTINGS = {
            'default': {
                'BACKEND': 'geonode.geoserver',
                'LOCATION': 'http://localhost:8080/geoserver/',
                'USER': 'admin',
                'PASSWORD': 'geoserver',
                'MAPFISH_PRINT_ENABLED': True,
                'PRINT_NG_ENABLED': True,
                'GEONODE_SECURITY_ENABLED': True,
                'GEOGIG_ENABLED': False,
                'WMST_ENABLED': False,
                'BACKEND_WRITE_ENABLED': True,
                'WPS_ENABLED': False,
                'DATASTORE': str(),
                'GEOGIG_DATASTORE_DIR': str(),
            }
        }

        self.UPLOADER_DEFAULT_SETTINGS = {
            'BACKEND': 'geonode.rest',
            'OPTIONS': {
                'TIME_ENABLED': False,
                'GEOGIG_ENABLED': False}}

        self.DATABASE_DEFAULT_SETTINGS = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'development.db'}}

    def test_ogc_server_settings(self):
        """
        Tests the OGC Servers Handler class.
        """

        with override_settings(OGC_SERVER=self.OGC_DEFAULT_SETTINGS, UPLOADER=self.UPLOADER_DEFAULT_SETTINGS):
            OGC_SERVER = self.OGC_DEFAULT_SETTINGS.copy()
            OGC_SERVER.update(
                {'PUBLIC_LOCATION': 'http://localhost:8080/geoserver/'})

            ogc_settings = OGC_Servers_Handler(OGC_SERVER)['default']
            default = OGC_SERVER.get('default')
            self.assertEqual(ogc_settings.server, default)
            self.assertEqual(ogc_settings.BACKEND, default.get('BACKEND'))
            self.assertEqual(ogc_settings.LOCATION, default.get('LOCATION'))
            self.assertEqual(
                ogc_settings.PUBLIC_LOCATION,
                default.get('PUBLIC_LOCATION'))
            self.assertEqual(ogc_settings.USER, default.get('USER'))
            self.assertEqual(ogc_settings.PASSWORD, default.get('PASSWORD'))
            self.assertEqual(ogc_settings.DATASTORE, str())
            self.assertEqual(ogc_settings.credentials, ('admin', 'geoserver'))
            self.assertTrue(ogc_settings.MAPFISH_PRINT_ENABLED)
            self.assertTrue(ogc_settings.PRINT_NG_ENABLED)
            self.assertTrue(ogc_settings.GEONODE_SECURITY_ENABLED)
            self.assertFalse(ogc_settings.GEOGIG_ENABLED)
            self.assertFalse(ogc_settings.WMST_ENABLED)
            self.assertTrue(ogc_settings.BACKEND_WRITE_ENABLED)
            self.assertFalse(ogc_settings.WPS_ENABLED)

    def test_ogc_server_defaults(self):
        """
        Tests that OGC_SERVER_SETTINGS are built if they do not exist in the settings.
        """

        OGC_SERVER = {'default': dict()}

        defaults = self.OGC_DEFAULT_SETTINGS.get('default')
        ogc_settings = OGC_Servers_Handler(OGC_SERVER)['default']
        self.assertEqual(ogc_settings.server, defaults)
        self.assertEqual(ogc_settings.rest, defaults['LOCATION'] + 'rest')
        self.assertEqual(ogc_settings.ows, defaults['LOCATION'] + 'ows')

        # Make sure we get None vs a KeyError when the key does not exist
        self.assertIsNone(ogc_settings.SFDSDFDSF)

    def test_importer_configuration(self):
        """
        Tests that the OGC_Servers_Handler throws an ImproperlyConfigured exception when using the importer
        backend without a vector database and a datastore configured.
        """
        database_settings = self.DATABASE_DEFAULT_SETTINGS.copy()
        ogc_server_settings = self.OGC_DEFAULT_SETTINGS.copy()
        uploader_settings = self.UPLOADER_DEFAULT_SETTINGS.copy()

        uploader_settings['BACKEND'] = 'geonode.importer'
        self.assertTrue(['geonode_imports' not in database_settings.keys()])

        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):

            # Test the importer backend without specifying a datastore or
            # corresponding database.
            with self.assertRaises(ImproperlyConfigured):
                OGC_Servers_Handler(ogc_server_settings)['default']

        ogc_server_settings['default']['DATASTORE'] = 'geonode_imports'

        # Test the importer backend with a datastore but no corresponding
        # database.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            with self.assertRaises(ImproperlyConfigured):
                OGC_Servers_Handler(ogc_server_settings)['default']

        database_settings['geonode_imports'] = database_settings[
            'default'].copy()
        database_settings['geonode_imports'].update(
            {'NAME': 'geonode_imports'})

        # Test the importer backend with a datastore and a corresponding
        # database, no exceptions should be thrown.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            OGC_Servers_Handler(ogc_server_settings)['default']


class SecurityTest(TestCase):

    """
    Tests for the Geonode security app.
    """

    def setUp(self):
        self.admin, created = get_user_model().objects.get_or_create(
            username='admin', password='admin', is_superuser=True)

    def test_login_middleware(self):
        """
        Tests the Geonode login required authentication middleware.
        """
        from geonode.security.middleware import LoginRequiredMiddleware
        middleware = LoginRequiredMiddleware()

        white_list = [
            reverse('account_ajax_login'),
            reverse('account_confirm_email', kwargs=dict(key='test')),
            reverse('account_login'),
            reverse('account_password_reset'),
            reverse('forgot_username'),
            reverse('layer_acls'),
            reverse('layer_resolve_user'),
        ]

        black_list = [
            reverse('account_signup'),
            reverse('document_browse'),
            reverse('maps_browse'),
            reverse('layer_browse'),
            reverse('layer_detail', kwargs=dict(layername='geonode:Test')),
            reverse('layer_remove', kwargs=dict(layername='geonode:Test')),
            reverse('profile_browse'),
        ]

        request = HttpRequest()
        request.user = get_anonymous_user()

        # Requests should be redirected to the the `redirected_to` path when un-authenticated user attempts to visit
        # a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(
                response.get('Location').startswith(
                    middleware.redirect_to))

        # The middleware should return None when an un-authenticated user
        # attempts to visit a white-listed url.
        for path in white_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(
                response,
                msg="Middleware activated for white listed path: {0}".format(path))

        self.client.login(username='admin', password='admin')
        self.assertTrue(self.admin.is_authenticated())
        request.user = self.admin

        # The middleware should return None when an authenticated user attempts
        # to visit a black-listed url.
        for path in black_list:
            request.path = path
            response = middleware.process_request(request)
            self.assertIsNone(response)
