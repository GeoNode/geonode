from django.core import management
from django.test import TestCase
from django.test.client import Client
import json


def setup():
    print 'setup called'
    management.call_command('loaddata', 'silage_testdata.json', verbosity=0)

def teardown():
    print 'teardown called'
    management.call_command('flush', verbosity=0, interactive=False)


class SilageTest(TestCase):

    c = Client()

    def _fixture_setup(self):
        pass

    def test_basic(self):
        response = self.c.get('/search/api')
        jsonvalue = json.loads(response.content)

        self.assertFalse(jsonvalue.get('errors'))
        self.assertTrue(jsonvalue.get('success'))
