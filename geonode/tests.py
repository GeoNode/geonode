from django.test.client import Client
from django.test import TestCase
import os

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
