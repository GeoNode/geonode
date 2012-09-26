from django.core import management
from django.test import TestCase
from django.test.client import Client
from geonode.silage.query import query_from_request
import json
import logging


class SilageTest(TestCase):

    c = Client()
    
    fixtures = ['initial_data.json','silage_testdata.json']
    
    @classmethod
    def setUpClass(cls):
        "Hook method for setting up class fixture before running tests in the class."
        logging.getLogger('south').setLevel(logging.INFO)
        SilageTest('_fixture_setup')._fixture_setup(True)

    @classmethod
    def tearDownClass(cls):
        "Hook method for deconstructing the class fixture after running all tests in the class."
        SilageTest('_fixture_teardown')._fixture_teardown(True)
        logging.getLogger('south').setLevel(logging.DEBUG)

    def _fixture_setup(self, a=False):
        if a:
            super(SilageTest, self)._fixture_setup()
        
    def _fixture_teardown(self, a=False):
        if a:
            super(SilageTest, self)._fixture_teardown()

    def test_basic(self):
        response = self.c.get('/search/api',{'limit': 100})
        jsonvalue = json.loads(response.content)

        self.assertFalse(jsonvalue.get('errors'))
        self.assertTrue(jsonvalue.get('success'))
        self.assertEquals(28,jsonvalue.get('total'))
        
    def test_layers(self):
        obj = self.request(type='layer',limit=100)
        self.assertEquals(8,obj.get('total'))
        
    def test_maps(self):
        obj = self.request(type='map',limit=100)
        self.assertEquals(9, obj.get('total'))
        
    def test_owners(self):
        obj = self.request(type='owner',limit=100)
        self.assertEquals(11, obj.get('total'))

    def request(self, **kw):
        return json.loads(self.c.get('/search/api', kw).content)
    
    
    
class QueryTest(TestCase):
    
    def test_empty(self):
        q = query_from_request()
        self.assertTrue(q.cache)