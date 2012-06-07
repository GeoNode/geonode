import os
import math
from django.test.client import Client
from django.test import TestCase
from mock import patch

from geonode import GeoNodeException
from maps.utils import forward_mercator, inverse_mercator

class GeoNodeClientTests(TestCase):
    
    fixtures = ['test_data.json']
    GEOSERVER = False

    def setUp(self):
        # If Geoserver and GeoNetwork are not running
        # avoid running tests that call those views.
        if "GEOSERVER" in os.environ.keys():
            self.GEOSERVER = True

    def tearDown(self):
        pass

    #### Basic Pages ####

    def test_home_page(self):
        '''Test if the homepage renders.'''
        c = Client()
        response = c.get('/')
        self.failUnlessEqual(response.status_code, 200)

    def test_help_page(self):
        '''Test help page renders.'''

        c = Client()
        response = c.get('/help/')
        self.failUnlessEqual(response.status_code, 200)
    
    def test_developer_page(self):
        '''Test help page renders.'''

        c = Client()
        response = c.get('/help/')
        self.failUnlessEqual(response.status_code, 200)
    
    #### Data/Layer Pages ####
    
    def test_data_page(self):
        'Test if the data page renders.'
        c = Client()
        response = c.get('/data/')
        self.failUnlessEqual(response.status_code, 200)

    def test_data_acls(self):
        'Test if the data page renders.'
        c = Client()
        response = c.get('/data/acls')
        self.failUnlessEqual(response.status_code, 200)

    def test_data_search(self):
        'Test if the data page renders.'
        c = Client()
        response = c.get('/data/search')
        self.failUnlessEqual(response.status_code, 200)

    def test_data_search_api(self):
        'Test if the data page renders.'
        c = Client()
        response = c.get('/data/search/api')
        self.failUnlessEqual(response.status_code, 200)

    #### Maps Pages ####

    def test_maps_page(self):
        '''Test Maps page renders.'''

        c = Client()
        response = c.get('/maps/')
        self.failUnlessEqual(response.status_code, 200)

    def test_maps_search_page(self):
        '''Test Maps Search page renders.'''

        c = Client()
        response = c.get('/maps/search/')
        self.failUnlessEqual(response.status_code, 200)

    def test_maps_search_api(self):
        '''Test Maps Search API page renders.'''

        c = Client()
        response = c.get('/maps/search/api/')
        self.failUnlessEqual(response.status_code, 200)
    
    def test_new_map_page(self):
        '''Test New Map page renders.'''

        c = Client()
        response = c.get('/maps/new/')
        self.failUnlessEqual(response.status_code, 200)

    #### People Pages ####

    def test_profiles(self):
        '''Test the profiles page renders.'''

        c = Client()
        response = c.get('/profiles/')
        self.failUnlessEqual(response.status_code, 200)

    ### Some other Stuff

    def test_check_geonode_is_up(self):
        from contextlib import nested
        from geonode.maps.utils import check_geonode_is_up

        def blowup():
            raise Exception("BOOM")

        with patch('geonode.maps.models.Layer.objects.gs_catalog') as mock_gs:
            mock_gs.get_workspaces.side_effect = blowup

            self.assertRaises(GeoNodeException, check_geonode_is_up)

        with nested(
            patch('geonode.maps.models.Layer.objects.gs_catalog'),
            patch('geonode.maps.models.Layer.objects.geonetwork')
        ) as (mock_gs, mock_gn):
            mock_gn.login.side_effect = blowup
            self.assertRaises(GeoNodeException, check_geonode_is_up)
            self.assertTrue(mock_gs.get_workspaces.called)

        with nested(
            patch('geonode.maps.models.Layer.objects.gs_catalog'),
            patch('geonode.maps.models.Layer.objects.geonetwork')
        ) as (mock_gs, mock_gn):
            # no assertion, this should just run without error
            check_geonode_is_up()


    def test_forward_mercator(self):
        arctic = forward_mercator((0, 85))
        antarctic = forward_mercator((0, -85))
        hawaii = forward_mercator((-180, 0))
        phillipines = forward_mercator((180, 0))
        ne = forward_mercator((180, 90))
        sw = forward_mercator((-180, -90))

        self.assertEqual(round(arctic[0]), 0, "Arctic longitude is correct")
        self.assertEqual(round(arctic[1]), 19971869, "Arctic latitude is correct")

        self.assertEqual(round(antarctic[0]), 0, "Antarctic longitude is correct")
        self.assertEqual(round(antarctic[1]), -19971869, "Antarctic latitude is correct")

        self.assertEqual(round(hawaii[0]), -20037508, "Hawaiian lon is correct")
        self.assertEqual(round(hawaii[1]), 0, "Hawaiian lat is correct")

        self.assertEqual(round(phillipines[0]), 20037508, "Phillipines lon is correct")
        self.assertEqual(round(phillipines[1]), 0, "Phillipines lat is correct")

        self.assertEqual(round(ne[0]), 20037508, "NE lon is correct")
        self.assertTrue(ne[1] > 50000000, "NE lat is correct")

        self.assertEqual(round(sw[0]), -20037508, "SW lon is correct")
        self.assertTrue(math.isinf(sw[1]), "SW lat is correct")
        
        # verify behavior for invalid y values
        self.assertEqual(float('-inf'), forward_mercator((0, 135))[1])
        self.assertEqual(float('-inf'), forward_mercator((0, -135))[1])

    def test_inverse_mercator(self):
        arctic = inverse_mercator(forward_mercator((0, 85)))
        antarctic = inverse_mercator(forward_mercator((0, -85)))
        hawaii = inverse_mercator(forward_mercator((-180, 0)))
        phillipines = inverse_mercator(forward_mercator((180, 0)))
        ne = inverse_mercator(forward_mercator((180, 90)))
        sw = inverse_mercator(forward_mercator((-180, -90)))

        self.assertAlmostEqual(arctic[0], 0.0, msg="Arctic longitude is correct")
        self.assertAlmostEqual(arctic[1], 85.0, msg="Arctic latitude is correct")

        self.assertAlmostEqual(antarctic[0], 0.0, msg="Antarctic longitude is correct")
        self.assertAlmostEqual(antarctic[1], -85.0, msg="Antarctic latitude is correct")

        self.assertAlmostEqual(hawaii[0], -180.0, msg="Hawaiian lon is correct")
        self.assertAlmostEqual(hawaii[1], 0.0, msg="Hawaiian lat is correct")

        self.assertAlmostEqual(phillipines[0], 180.0, msg="Phillipines lon is correct")
        self.assertAlmostEqual(phillipines[1], 0.0, msg="Phillipines lat is correct")

        self.assertAlmostEqual(ne[0], 180.0, msg="NE lon is correct")
        self.assertAlmostEqual(ne[1], 90.0, msg="NE lat is correct")

        self.assertAlmostEqual(sw[0], -180.0, msg="SW lon is correct")
        self.assertAlmostEqual(sw[1], -90.0, msg="SW lat is correct")

    def test_split_query(self):
        query = 'alpha "beta gamma"   delta  '
        from geonode.maps.views import _split_query
        keywords = _split_query(query)
        self.assertEqual(keywords[0], "alpha")
        self.assertEqual(keywords[1], "beta gamma")
        self.assertEqual(keywords[2], "delta")


