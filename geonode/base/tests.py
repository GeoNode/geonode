from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings
from geonode.base.models import ResourceBase
from geonode.utils import OGC_Servers_Handler


class ThumbnailTests(TestCase):

    def setUp(self):
        self.rb = ResourceBase.objects.create()

    def tearDown(self):
        t = self.rb.thumbnail
        if t:
            t.delete()

    def test_initial_behavior(self):
        self.assertFalse(self.rb.has_thumbnail())
        missing = self.rb.get_thumbnail_url()
        self.assertEquals('/static/geonode/img/missing_thumb.png', missing)

    def test_saving(self):
        # monkey patch our render function to just put the 'spec' into the file
        self.rb._render_thumbnail = lambda *a, **kw: '%s' % a[0]

        self._do_save_test('abc', 1)
        self._do_save_test('xyz', 2)

    def _do_save_test(self, content, version):
        self.rb.save_thumbnail(content)
        thumb = self.rb.thumbnail
        self.assertEquals(version, thumb.version)
        self.assertEqual(content, thumb.thumb_file.read())
        self.assertEqual(content, thumb.thumb_spec)


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





