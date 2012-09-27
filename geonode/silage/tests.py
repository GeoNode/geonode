from django.test import TestCase
from django.test.client import Client
import json
import logging

logging.getLogger('south').setLevel(logging.INFO)

class SilageTest(TestCase):

    c = Client()
    
    fixtures = ['initial_data.json', 'silage_testdata.json']
    
    @classmethod
    def setUpClass(cls):
        "Hook method for setting up class fixture before running tests in the class."
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

    def request(self, query=None, **options):
        query_dict = dict(q=query) if query else {}
        get_params = dict(query_dict, **options)
        return self.c.get('/search/api', get_params)

    def assert_results_contain_title(self, jsonvalue, title, _type=None):
        matcher = (lambda doc: doc['title'] == title if _type is None else
                   lambda doc: doc['title'] == title and doc['_type'] == _type)
        matches = filter(matcher, jsonvalue['results'])
        self.assertTrue(matches, "No results match %s" % title)

    def search_assert(self, response, **options):
        jsonvalue = json.loads(response.content)
        self.assertFalse(jsonvalue.get('errors'))
        self.assertTrue(jsonvalue.get('success'))

        contains_maptitle = options.pop('contains_maptitle', None)
        if contains_maptitle:
            self.assert_results_contain_title(jsonvalue, contains_maptitle, 'map')

        contains_layertitle = options.pop('contains_layertitle', None)
        if contains_layertitle:
            self.assert_results_contain_title(jsonvalue, contains_layertitle, 'layer')

        contains_username = options.pop('contains_username', None)
        if contains_username:
            self.assert_results_contain_title(jsonvalue, contains_username, 'owner')

        n_results = options.pop('n_results', None)
        if n_results:
            self.assertEquals(n_results, len(jsonvalue['results']))
            
        n_total = options.pop('n_total', None)
        if n_total:
            self.assertEquals(n_total, jsonvalue['total'])


    def test_limit(self):
        self.search_assert(self.request(limit=1), n_results=1)

    def test_query_map_title(self):
        self.search_assert(self.request('unique'), contains_maptitle='map one')

    def test_query_layer_title(self):
        self.search_assert(self.request('uniquetitle'),
                           contains_layerid='uniquetitle')

    def test_username(self):
        self.search_assert(self.request('jblaze'), contains_username='jblaze')

    def test_profile(self):
        self.search_assert(self.request("some other information"),
                           contains_username='jblaze')

    def test_text_across_types(self):
        self.search_assert(self.request('foo'), n_results=7)

    def test_bbox_query(self):
        # @todo since maps and users are excluded at the moment, this will have
        # to be revisited
        self.search_assert(self.request(extent='-180,180,-90,90'), n_results=8)
        self.search_assert(self.request(extent='0,10,0,10'), n_results=3)
        self.search_assert(self.request(extent='0,1,0,1'), n_results=1)

    def test_date_query(self):
        self.search_assert(self.request(period='1980-01-01T00:00:00Z,1995-01-01T00:00:00Z'),
                           n_results=3)
