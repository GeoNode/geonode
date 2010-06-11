from django.test.client import Client
from django.test import TestCase
import os

class GeoNodeClientTests(TestCase):
    
    fixtures = ['test_data.json', 'map_data.json']
    GEOSERVER = False

    def setUp(self):
        # If Geoserver and GeoNetwork are not running
        # avoid running tests that call those views.
        if "GEOSERVER" in os.environ.keys():
            self.GEOSERVER = True

    def tearDown(self):
        pass


    def test_HomePage(self):
        '''Test if the homepage renders.'''
        c = Client()
        response = c.get('/')
        self.failUnlessEqual(response.status_code, 200)

    def test_Data(self):
        'Test if the data page renders.'
        c = Client()
        response = c.get('/data/')
        self.failUnlessEqual(response.status_code, 200)

    def test_Curated(self):
        'Test if the curated maps page renders.'
        c = Client()
        response = c.get('/curated/')

        self.failUnlessEqual(response.status_code, 200)

    def test_Community(self):
        '''Test community page renders.'''

        c = Client()
        response = c.get('/community/')
        self.failUnlessEqual(response.status_code, 200)

    def test_Help(self):
        '''Test help page renders.'''

        c = Client()
        response = c.get('/help/')
        self.failUnlessEqual(response.status_code, 200)

    def test_Files(self):
        '''Test the files page renders.'''
 
        c = Client()
        response = c.get('/files/')
        self.failUnlessEqual(response.status_code, 200)
    
    def test_Profiles(self):
        '''Test the profiles page renders.'''

        c = Client()
        response = c.get('/profiles/')
        self.failUnlessEqual(response.status_code, 200)
   
    def test_DescribeData(self):
        ''' Test accessing the description of a layer'''
        
        c = Client()
        response = c.get('/data/base:CA?describe')
        # Since we are not authenticated, we should not be able to access it
        self.failUnlessEqual(response.status_code, 403)
        # but if we log in ...
        c.login(username='bobby', password='bob')
        # ... all should be good
        if self.GEOSERVER:
            response = c.get('/data/base:CA?describe')
            self.failUnlessEqual(response.status_code, 200)
        else:
            # If Geoserver is not running, this should give a runtime error
            try:
                c.get('/data/base:CA?describe')
            except RuntimeError:
                pass
        
