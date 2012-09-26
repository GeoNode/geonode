from django.core import management
from django.test import TestCase
from django.test.client import Client
import json
import logging

logging.getLogger('south').setLevel(logging.INFO)
setup_ran = False

class SilageTest(TestCase):

    c = Client()
    
    fixtures = ['initial_data.json','silage_testdata.json']

    def _fixture_setup(self):
        global setup_ran
        if setup_ran:
            return
        super(SilageTest, self)._fixture_setup()
        setup_ran = True
        
    def _fixture_teardown(self):
        #logging.getLogger('south').setLevel(logging.DEBUG)
        return

    def test_basic(self):
        response = self.c.get('/search/api',{'limit': 100})
        jsonvalue = json.loads(response.content)

        self.assertFalse(jsonvalue.get('errors'))
        self.assertTrue(jsonvalue.get('success'))
