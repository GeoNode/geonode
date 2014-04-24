import json

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.test.client import Client
from django.test.utils import override_settings
from geonode.base.models import ResourceBase
from geonode.geoserver.helpers import OGC_Servers_Handler
from geonode.search.populate_search_test_data import create_models
from geonode.layers.populate_layers_data import create_layer_data
from geonode.layers.models import Layer

class LayerTests(TestCase):

    fixtures = ['bobby']

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_layer_data()

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
        if settings.OGC_SERVER['default']['DATASTORE']:
            # The check was moved from the template into the view
            response = c.post(reverse('feature_edit_check', args=(valid_layer_typename,)))
            response_json = json.loads(response.content)
            self.assertEquals(response_json['authorized'], True)



class UtilsTests(TestCase):

    def setUp(self):
        self.OGC_DEFAULT_SETTINGS = {
            'default': {
                    'BACKEND': 'geonode.geoserver',
                    'LOCATION': 'http://localhost:8080/geoserver/',
                    'USER': 'admin',
                    'PASSWORD': 'geoserver',
                    'MAPFISH_PRINT_ENABLED': True,
                    'PRINTING_ENABLED': True,
                    'GEONODE_SECURITY_ENABLED': True,
                    'GEOGIT_ENABLED': False,
                    'WMST_ENABLED': False,
                    'BACKEND_WRITE_ENABLED': True,
                    'WPS_ENABLED': False,
                    'DATASTORE': str(),
                    'GEOGIT_DATASTORE_DIR': str(),
            }
        }

        self.UPLOADER_DEFAULT_SETTINGS = {'BACKEND': 'geonode.rest',
                                          'OPTIONS': {'TIME_ENABLED': False, 'GEOGIT_ENABLED': False}}

        self.DATABASE_DEFAULT_SETTINGS = {'default': {'ENGINE': 'django.db.backends.sqlite3',
                                                      'NAME': 'development.db'}}

    def test_ogc_server_settings(self):
        """
        Tests the OGC Servers Handler class.
        """

        with override_settings(OGC_SERVER=self.OGC_DEFAULT_SETTINGS, UPLOADER=self.UPLOADER_DEFAULT_SETTINGS):
            OGC_SERVER = self.OGC_DEFAULT_SETTINGS.copy()
            OGC_SERVER.update({'PUBLIC_LOCATION' : 'http://localhost:8080/geoserver/'})

            ogc_settings = OGC_Servers_Handler(OGC_SERVER)['default']
            default = OGC_SERVER.get('default')
            self.assertEqual(ogc_settings.server, default)
            self.assertEqual(ogc_settings.BACKEND, default.get('BACKEND'))
            self.assertEqual(ogc_settings.LOCATION, default.get('LOCATION'))
            self.assertEqual(ogc_settings.PUBLIC_LOCATION, default.get('PUBLIC_LOCATION'))
            self.assertEqual(ogc_settings.USER, default.get('USER'))
            self.assertEqual(ogc_settings.PASSWORD, default.get('PASSWORD'))
            self.assertEqual(ogc_settings.DATASTORE, str())
            self.assertEqual(ogc_settings.credentials, ('admin', 'geoserver'))
            self.assertTrue(ogc_settings.MAPFISH_PRINT_ENABLED)
            self.assertTrue(ogc_settings.PRINTING_ENABLED)
            self.assertTrue(ogc_settings.GEONODE_SECURITY_ENABLED)
            self.assertFalse(ogc_settings.GEOGIT_ENABLED)
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
        self.assertEqual(ogc_settings.rest, defaults['LOCATION']+'rest')
        self.assertEqual(ogc_settings.ows, defaults['LOCATION']+'ows')

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

            #  Test the importer backend without specifying a datastore or corresponding database.
            with self.assertRaises(ImproperlyConfigured):
                 OGC_Servers_Handler(ogc_server_settings)['default']

        ogc_server_settings['default']['DATASTORE'] = 'geonode_imports'

        #  Test the importer backend with a datastore but no corresponding database.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            with self.assertRaises(ImproperlyConfigured):
                OGC_Servers_Handler(ogc_server_settings)['default']

        database_settings['geonode_imports'] = database_settings['default'].copy()
        database_settings['geonode_imports'].update({'NAME': 'geonode_imports'})

        #  Test the importer backend with a datastore and a corresponding database, no exceptions should be thrown.
        with self.settings(UPLOADER=uploader_settings, OGC_SERVER=ogc_server_settings, DATABASES=database_settings):
            OGC_Servers_Handler(ogc_server_settings)['default']





