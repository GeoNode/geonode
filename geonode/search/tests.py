#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.test.client import Client
from django.test import TestCase
from geonode.security.models import AUTHENTICATED_USERS
from geonode.security.models import ANONYMOUS_USERS
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.people.models import Profile
from geonode.search import search
from geonode.search import util
from geonode.search.populate_search_test_data import create_models
from geonode.search.query import query_from_request
from agon_ratings.models import OverallRating
import json
import logging

# quack
MockRequest = lambda **kw: type('xyz',(object,),{'REQUEST':kw,'user':None})

def all_public():
    '''ensure all layers, maps and documents are publicly viewable'''
    for l in Layer.objects.all():
        l.set_default_permissions()
    for m in Map.objects.all():
        m.set_default_permissions()
    for d in Document.objects.all():
        d.set_default_permissions()

class searchTest(TestCase):

    c = Client()

    fixtures = ['initial_data.json']

    @classmethod
    def setUpClass(cls):
        "Hook method for setting up class fixture before running tests in the class."
        from django.core.cache import cache
        cache.clear()
        searchTest('_fixture_setup')._fixture_setup(True)
        create_models()
        all_public()

    @classmethod
    def tearDownClass(cls):
        "Hook method for deconstructing the class fixture after running all tests in the class."
        searchTest('_fixture_teardown')._fixture_teardown(True)
        logging.getLogger('south').setLevel(logging.DEBUG)

    def _fixture_setup(self, a=False):
        if a:
            super(searchTest, self)._fixture_setup()

    def _fixture_teardown(self, a=False):
        if a:
            super(searchTest, self)._fixture_teardown()

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

        facets = jsonvalue['facets']
        if 'layer' in facets:
            self.assertEquals(facets['raster'] + facets['vector'], facets['layer'])

#        import pprint; pprint.pprint(jsonvalue)
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

        first_title = options.pop('first_title', None)
        if first_title:
            self.assertTrue(len(jsonvalue['results']) > 0, 'No results found')
            doc = jsonvalue['results'][0]
            self.assertEquals(first_title, doc['title'])

        sorted_by = options.pop('sorted_by', None)
        if sorted_by:
            reversed = sorted_by[0] == '-'
            sorted_by = sorted_by.replace('-','')
            sorted_fields = [ jv[sorted_by] for jv in jsonvalue['results'] ]
            expected = list(sorted_fields)
            expected.sort(reverse = reversed)
            self.assertEquals(sorted_fields, expected)


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
        self.search_assert(self.request('foo'), n_results=8, n_total=8)
        self.search_assert(self.request('common'), n_results=10, n_total=23)

    def test_pagination(self):
        self.search_assert(self.request('common', start=0), n_results=10, n_total=23)
        self.search_assert(self.request('common', start=10), n_results=10, n_total=23)
        self.search_assert(self.request('common', start=20), n_results=3, n_total=23)

    def test_bbox_query(self):
        # @todo since maps and users are excluded at the moment, this will have
        # to be revisited
        self.search_assert(self.request(extent='-180,180,-90,90', limit=None), n_results=26, n_total=26)
        self.search_assert(self.request(extent='0,10,0,10', limit=None), n_results=11)
        self.search_assert(self.request(extent='0,1,0,1', limit=None), n_results=3)
        
    def test_bbox_result(self):
        # grab one and set the bounds
        lyr = Layer.objects.all()[0]
        lyr.bbox_x0 = -100
        lyr.bbox_x1 = -90
        lyr.bbox_y0 = 38
        lyr.bbox_y1 = 40
        lyr.save()
        
        response = json.loads(self.request(lyr.title,type='layer').content)
        self.assertEquals({u'minx': u'-100', u'miny': u'38', u'maxx': u'-90', u'maxy': u'40'},
                          response['results'][0]['bbox'])

    def test_date_query(self):
        self.search_assert(self.request(period='1980-01-01T00:00:00Z,1995-01-01T00:00:00Z'),
                           n_results=3)
        self.search_assert(self.request(period=',1995-01-01T00:00:00Z'),
                           n_results=7)
        self.search_assert(self.request(period='1980-01-01T00:00:00Z,'),
                           n_results=10, n_total=22)

    def test_errors(self):
        self.assert_error(self.request(sort='foo'),
            "valid sorting values are: ['alphaaz', 'newest', 'popularity', 'alphaza', 'rel', 'oldest']")
        self.assert_error(self.request(extent='1,2,3'),
            'extent filter must contain x0,x1,y0,y1 comma separated')
        self.assert_error(self.request(extent='a,b,c,d'),
            'extent filter must contain x0,x1,y0,y1 comma separated')
        self.assert_error(self.request(start='x'),
            'startIndex must be valid number')
        self.assert_error(self.request(limit='x'),
            'limit must be valid number')
        self.assert_error(self.request(added='x'),
            'valid added filter values are: today,week,month')

    def assert_error(self, resp, msg):
        obj = json.loads(resp.content)
        self.assertTrue(obj['success'] == False)
        self.assertEquals(msg, obj['errors'][0])

    def test_sort(self):
        self.search_assert(self.request('foo', sort='newest',type='layer'),
                           first_title='common blar', sorted_by='-last_modified')
        self.search_assert(self.request('foo', sort='oldest',type='layer'),
                           first_title='common double time', sorted_by='last_modified')
        self.search_assert(self.request('foo', sort='alphaaz'),
                           first_title='bar baz', sorted_by='title')
        self.search_assert(self.request('foo', sort='alphaza'),
                           first_title='uniquefirst foo', sorted_by='-title')

        # apply some ratings
        ct = ContentType.objects.get_for_model(Layer)
        for l in Layer.objects.all():
            OverallRating.objects.create(content_type=ct, object_id=l.pk, rating=l.pk, category=2)
        ct = ContentType.objects.get_for_model(Map)
        for l in Map.objects.all():
            OverallRating.objects.create(content_type=ct, object_id=l.pk, rating=l.pk, category=1)
        # clear any cached ratings
        from django.core.cache import cache
        cache.clear()
        self.search_assert(self.request('foo', sort='popularity'),
                           first_title='common double time', sorted_by='-rating')

    def test_keywords(self):
        # this tests the matching of the general query to keywords
        self.search_assert(self.request('populartag'), n_results=10, n_total=26)
        self.search_assert(self.request('maptagunique'), n_results=1, n_total=1)
        self.search_assert(self.request('layertagunique'), n_results=1, n_total=1)
        # verify little chunks must entirely match keywords
        # po ma la are the prefixes to the former keywords :)
        self.search_assert(self.request('po ma la'), n_results=0, n_total=0)

    def test_type_query(self):
        self.search_assert(self.request('common', type='map'), n_results=9, n_total=9)
        self.search_assert(self.request('common', type='layer'), n_results=5, n_total=5)
        self.search_assert(self.request('common', type='document'), n_results=9, n_total=9)
        self.search_assert(self.request('foo', type='owner'), n_results=4, n_total=4)
        # there are 8 total layers, half vector, half raster
        self.search_assert(self.request('', type='coverageStore'), n_results=4, n_total=4)
        self.search_assert(self.request('', type='dataStore'), n_results=4, n_total=4)

    def test_kw_query(self):
        # a kw-only query should filter out those not matching the keyword
        self.search_assert(self.request('', kw='here', type='layer'), n_results=1, n_total=1)
        # no matches
        self.search_assert(self.request('', kw='foobar', type='layer'), n_results=0, n_total=0)

    def test_exclude_query(self):
        # exclude one layer
        self.search_assert(self.request('', exclude='layer1'), n_results=10, n_total=31)
        # exclude one general word
        self.search_assert(self.request('', exclude='common'), n_results=10, n_total=27)
        # exclude more than one word
        self.search_assert(self.request('', exclude='common,something'), n_results=10, n_total=23)
        # exclude almost everything
        self.search_assert(self.request('', exclude='common,something,ipsum,quux,morx,one'), n_results=9, n_total=9)

    def test_author_endpoint(self):
        resp = self.c.get('/search/api/authors')
        jsobj = json.loads(resp.content)
        self.assertEquals(6, jsobj['total'])

    def test_search_page(self):
        resp = self.c.get('/search/')
        self.assertEquals(200, resp.status_code)

    def test_util(self):
        jdate = util.iso_str_to_jdate('-5000-01-01T12:00:00Z')
        self.assertEquals(jdate, -105192)
        roundtripped = util.jdate_to_approx_iso_str(jdate)
        self.assertEquals(roundtripped, '-4999-01-03')

    def test_security_trimming(self):
        try:
            self.run_security_trimming()
        finally:
            all_public()

    def run_security_trimming(self):
        # remove permissions on all jblaze layers
        jblaze_layers = Layer.objects.filter(owner__username='jblaze')
        hiding = jblaze_layers.count()
        for l in jblaze_layers:
            l.set_gen_level(ANONYMOUS_USERS, l.LEVEL_NONE)
            l.set_gen_level(AUTHENTICATED_USERS, l.LEVEL_NONE)

        # a (anonymous) layer query should exclude the number of hiding layers
        self.search_assert(self.request(type='layer'), n_results=8 - hiding, n_total=8 - hiding)

        # admin sees all
        self.assertTrue(self.c.login(username='admin', password='admin'))
        self.search_assert(self.request(type='layer'), n_results=8, n_total=8)
        self.c.logout()

        # a logged in jblaze will see his, too
        jblaze = User.objects.get(username='jblaze')
        jblaze.set_password('passwd')
        jblaze.save()
        self.assertTrue(self.c.login(username='jblaze', password='passwd'))
        self.search_assert(self.request(type='layer'), n_results=8, n_total=8)
        self.c.logout()

    def test_relevance(self):
        query = query_from_request(MockRequest(q='foo'), {})

        def assert_rules(rules):
            rank_rules = []
            for model, model_rules in rules:
                rank_rules.extend(search._rank_rules(model, *model_rules))

            sql = search._add_relevance(query, rank_rules)

            for _, model_rules in rules:
                for attr, rank1, rank2 in model_rules:
                    self.assertTrue(('THEN %d ELSE 0' % rank1) in sql)
                    self.assertTrue(('THEN %d ELSE 0' % rank2) in sql)
                    self.assertTrue(attr in sql)

        assert_rules([(Map, [('title', 10, 5), ('abstract', 5, 2)])])
        assert_rules([(Layer,
            [('name', 10, 1), ('title', 10, 5), ('abstract', 5, 2)])])
        assert_rules([(User, [('username', 10, 5)]),
                      (Profile, [('organization', 5, 2)])])
