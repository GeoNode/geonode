from django.test import TestCase
from django.test import Client

import json


class SearchTest(TestCase):
    """Tests geonode.searc app/module
    """

    def test_first(self):
        pass

    def test_query(self):
        """
        Test a simple search with no query
        """
        """
        right now all layers are uploaded beforehand
        """

        ## Retrieve Query Params
        #id = request.REQUEST.get("id", None) ...DONE
        #query = request.REQUEST.get('q',None) ...DONE
        #name = request.REQUEST.get("name", None)
        #category = request.REQUEST.get("cat", None) ...DONE
        #limit = int(request.REQUEST.get("limit", getattr(settings, "HAYSTACK_SEARCH_RESULTS_PER_PAGE", 20))) ...DONE
        #startIndex = int(request.REQUEST.get("startIndex", 0)) ...DONE
        #startPage = int(request.REQUEST.get("startPage", 0))
        #sort = request.REQUEST.get("sort", "relevance")
        #order = request.REQUEST.get("order", "asc")
        #type = request.REQUEST.get("type", None) ...DONE
        #fields = request.REQUEST.get("fields", None)
        #fieldset = request.REQUEST.get("fieldset", None)
        #format = request.REQUEST.get("format", "json")
        ## Geospatial Elements
        #bbox = request.REQUEST.get("bbox", None)

    def test_empty_search(self):
        # Test Empty Search [returns all results, should match len(Layer.objects.all())+5]
        test_url = "/search/api/?q=%s&start=%d&limit=%d"  % ("", 0, 1)
        client = Client()
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 18)
           
    def test_random_search(self):
        # Test n0ch@nc3 Search (returns no results)
        test_url = "/search/api/?q=%s&start=%d&limit=%d"  % ("n0ch@nc3", 0, 10)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 0)
                
    def test_keyword_search(self):
        # Test Keyword Search (various search terms)
        test_url = "/search/api/?q=%s"  % ("san_andres_y_providencia_location")
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 1)
    
    def test_id_search(self):
        # Test id Search
        test_url = "/search/api/?id=%d"  % (3)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 1)
        
    def test_id_search_2(self):    
        # Test id Search (when id=1, two layers will be selected)
        test_url = "/search/api/?id=%d"  % (1)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 2)
        
    def test_name_search(self):
        # TODO: Test name Search
        test_url = "/search/api/?name=%s"  % ('san_andres_y_providencia_location')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        #self.assertEquals(results["total"], 2)

    def test_limit_search(self):
        # Test limit Search
        test_url = "/search/api/?limit=%d"  % (10)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(len(results["results"]), 10)

    def test_startIndex_search(self):
        # Test startIndex Search
        test_url = "/search/api/?startIndex=%d"  % (5)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        #print resp
        self.assertEquals(len(results["results"]), 13)

    def test_startPage_search(self):
        # TODO: Test startPage Search
        test_url = "/search/api/?startPage=%d"  % (1)
        resp = client.get(test_url)
        results = json.loads(resp.content)
        #print resp
        #self.assertEquals(results["total"], 2)

    def test_type_search(self):
        # Test type Search: layer
        test_url = "/search/api/?type=%s"  % ('layer')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 16)

        # Test type Search: contact
        test_url = "/search/api/?type=%s"  % ('contact')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 2)

        # Test type Search: map
        test_url = "/search/api/?type=%s"  % ('map')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 0)

        # Test type Search: vector
        test_url = "/search/api/?type=%s"  % ('vector')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 14)

        # Test type Search: raster
        test_url = "/search/api/?type=%s"  % ('raster')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 2)

    def test_category_search(self):
        # Test category Search
        test_url = "/search/api/?cat=%s"  % ('location')
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 16)

    def test_sort_search(self):
        # TODO: Test sort Search
        test_url = "/search/api/?sort=%s"  % ('newest') #oldest, alphaaz, alphaza
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(results["total"], 16)

        """
        # This Section should be greatly expanded upon after uploading several
        # Test layers. Issues found with GeoNetwork search should be 'documented'
        # here with a Test Case

        # Test BBOX Search (various bbox)
        
        # - Test with an empty query string and Global BBOX and validate that total is correct
        test_url = "/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % ("", 0, 10, "-180,-90,180,90")
        resp = client.get(test_url)
        results = json.loads(resp.content)
        self.assertEquals(int(results["total"]), Layer.objects.count())

        # - Test with a specific query string and a bbox that is disjoint from its results
        #test_url = "%s/search/api/?q=%s&start=%d&limit=%d&bbox=%s"  % (settings.SITEURL, "NIC", 0, 10, "0,-90,180,90")
        #results = json.loads(get_web_page(test_url))
        #self.assertEquals(int(results["total"]), 0) 

        # - Many more Tests required

        # Test start/limit params (do in unit test?)

        # Test complex/compound Search
        """
