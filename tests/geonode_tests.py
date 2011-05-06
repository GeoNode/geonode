import os, sys
from django.conf import settings
#from django.test import TestCase
from unittest import TestCase
from django.contrib.auth.models import AnonymousUser
import contextlib 

import urllib2
import json

from tests.utils import get_web_page
from geonode.maps.models import Layer

from geonode.maps.views import set_layer_permissions
from geonode.core.models import *

TEST_DATA = os.path.join(settings.PROJECT_ROOT, 'geonode_test_data')

LOGIN_URL=settings.SITEURL + "accounts/login/"

class GeoNodeCoreTest(TestCase):
    """Tests geonode.core app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        assert(True)
    
class GeoNodeProxyTest(TestCase):
    """Tests geonode.proxy app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_something(self):
        assert(True)

class GeoNodeMapTest(TestCase):
    """Tests geonode.maps app/module
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # geonode.maps.views

    # Search Tests
    
    def test_metadata_search(self):
        
        # Test Empty Search [returns all results, should match len(Layer.objects.all())+5]
        # +5 is for the 5 'default' records in GeoNetwork
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "", 0, 10)
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), len(Layer.objects.all())+5)
        
        # Test n0ch@nc3 Search (returns no results)
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "n0ch@nc3", 0, 10)
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), 0)
        
        # Test Keyword Search (various search terms)
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL, "NIC", 0, 10)
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), 3)

        # This Section should be greatly expanded upon after uploading several
        # Test layers. Issues found with GeoNetwork search should be 'documented'
        # here with a Test Case

        # Test BBOX Search (various bbox)
        
        # - Test with an empty query string and Global BBOX and validate that total is correct
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % (settings.SITEURL, "", 0, 10, "-180,-90,180,90")
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), len(Layer.objects.all())+5)

        # - Test with a specific query string and a bbox that is disjoint from its results
        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % (settings.SITEURL, "NIC", 0, 10, "0,-90,180,90")
        results = json.loads(get_web_page(test_url))
        self.assertEquals(int(results["total"]), 0) 

        # - Many more Tests required

        # Test start/limit params (do in unit test?)

        # Test complex/compound Search

        # Test Permissions applied to search from ACLs

        # TODO Write a method to accept a perm_spec and query params and test that query results are returned respecting the perm_spec

        # - Test with Anonymous User
        perm_spec = {"anonymous":"_none","authenticated":"_none","users":[["admin","layer_readwrite"]]}
        for layer in Layer.objects.all():
            set_layer_permissions(layer, perm_spec)

        test_url = "%sdata/search/api/?q=%s&start=%d&limit=%d"  % (settings.SITEURL,"", 0, 10)

        results = json.loads(get_web_page(test_url))
        
        for layer in results["rows"]:
            if layer["_local"] == False:
                # Ignore non-local layers
                pass
            else:
                self.assertEquals(layer["_permissions"]["view"], False)
                self.assertEquals(layer["_permissions"]["change"], False)
                self.assertEquals(layer["_permissions"]["delete"], False)
                self.assertEquals(layer["_permissions"]["change_permissions"], False)

        # - Test with Authenticated User
        results = json.loads(get_web_page(test_url, username="admin", password="@dm1n", login_url=LOGIN_URL))
        
        for layer in results["rows"]:
            if layer["_local"] == False:
                # Ignore non-local layers
                pass
            else:
                self.assertEquals(layer["_permissions"]["view"], True)
                self.assertEquals(layer["_permissions"]["change"], True)
                self.assertEquals(layer["_permissions"]["delete"], True)
                self.assertEquals(layer["_permissions"]["change_permissions"], True)
        
        # Test that MAX_SEARCH_BATCH_SIZE is respected (in unit test?)
    
    def test_search_result_detail(self):
        # Test with a valid UUID
        uuid=Layer.objects.all()[0].uuid
        test_url = "%sdata/search/detail/?uuid=%s"  % (settings.SITEURL, uuid)
        results = get_web_page(test_url)
        
        # Test with an invalid UUID (should return 404, but currently does not)
        uuid="xyz"
        test_url = "%sdata/search/detail/?uuid=%s"  % (settings.SITEURL, uuid)
        # Should use assertRaisesRegexp here, but new in 2.7
        self.assertRaises(urllib2.HTTPError,
            lambda: get_web_page(test_url)) 

    def test_maps_search(self):
        pass

    # geonode.maps.models

    # geonode.maps.gs_helpers
