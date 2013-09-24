from django.test import TestCase
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

    def test_ogc_server_settings(self):
        """
        Tests the OGC Servers Handler class.
        """

        OGC_SERVER = {
            'default': {
                'BACKEND': 'geonode.geoserver',
                'LOCATION': 'http://localhost:8080/geoserver/',
                'PUBLIC_LOCATION' : 'http://localhost:8080/geoserver/',
                'USER': 'admin',
                'PASSWORD': 'geoserver',
                'MAPFISH_PRINT_ENABLED': True,
                'PRINTING_ENABLED': True,
                'GEONODE_SECURITY_ENABLED': True,
                'GEOGIT_ENABLED': True,
                'WMST_ENABLED': False,
                'BACKEND_WRITE_ENABLED': True,
                'WPS_ENABLED': False,
                'DATASTORE': str(),
            }
        }

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
        self.assertTrue(ogc_settings.GEOGIT_ENABLED)
        self.assertFalse(ogc_settings.WMST_ENABLED)
        self.assertTrue(ogc_settings.BACKEND_WRITE_ENABLED)
        self.assertFalse(ogc_settings.WPS_ENABLED)


    def test_ogc_server_defaults(self):
        """
        Tests that OGC_SERVER_SETTINGS are built if they do not exist in the settings.
        """

        OGC_SERVER = {
             'default': dict(),
         }

        EXPECTATION ={
            'default' : {
                    'BACKEND' : 'geonode.geoserver',
                    'LOCATION' : 'http://localhost:8080/geoserver/',
                    'USER' : 'admin',
                    'PASSWORD' : 'geoserver',
                    'MAPFISH_PRINT_ENABLED' : True,
                    'PRINTING_ENABLED' : True,
                    'GEONODE_SECURITY_ENABLED' : True,
                    'GEOGIT_ENABLED' : False,
                    'WMST_ENABLED' : False,
                    'BACKEND_WRITE_ENABLED': True,
                    'WPS_ENABLED' : False,
                    'DATASTORE': str(),
                    'GEOGIT_DATASTORE_DIR': str(),
            }
        }

        defaults = EXPECTATION.get('default')
        ogc_settings = OGC_Servers_Handler(OGC_SERVER)['default']
        self.assertEqual(ogc_settings.server, defaults)
        self.assertEqual(ogc_settings.rest, defaults['LOCATION']+'rest')
        self.assertEqual(ogc_settings.ows, defaults['LOCATION']+'ows')

        # Make sure we get None vs a KeyError when the key does not exist
        self.assertIsNone(ogc_settings.SFDSDFDSF)


