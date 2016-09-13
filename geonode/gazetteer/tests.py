import json
from lxml import etree
from django.conf import settings
from django.test import TestCase, Client
from geonode.gazetteer.utils import getGazetteerEntry


class GazetteerTest(TestCase):

    fixtures = ['gazetteer_data.json'] if settings.USE_GAZETTEER else []


    def test_get_gazetteer_entry(self):
        if settings.USE_GAZETTEER:
            results = getGazetteerEntry(5)
            self.assertEquals(1, len(results))
            entry = results[0]
            self.assertEquals(5, entry["id"])
            self.assertEquals("Paradise5", entry["placename"])

    def test_gazetteer_placename(self):
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise2")
            placenames = json.loads(response.content)
            self.assertEquals(1, len(placenames))
            self.assertEquals("Paradise2", placenames[0]["placename"])

    def test_gazetteer_placename_xml(self):
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise2/xml")
            result_xml = etree.fromstring(response.content)
            rootdoc = etree.ElementTree(result_xml)
            placenames = rootdoc.findall('.//resource')
            self.assertEquals(1, len(placenames))
            self.assertEquals("Paradise2", placenames[0].find("placename").text)

    def test_gazetteer_layer(self):
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise/Layer/CA1")
            placenames = json.loads(response.content)
            self.assertEquals(3, len(placenames))
            self.assertContains(response, text="base:CA1", html=False, status_code=200)
            self.assertNotContains(response, text="base:CA2", html=False, status_code=200)

    def test_gazetteer_map(self):
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise/Map/1")
            placenames = json.loads(response.content)
            self.assertEquals(5, len(placenames))
            self.assertContains(response, text="base:CA1", html=False, status_code=200)
            self.assertContains(response, text="base:CA2", html=False, status_code=200)

    def test_gazetteer_project(self):
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise/Project/test")
            placenames = json.loads(response.content)
            self.assertEquals(4, len(placenames))
            self.assertNotContains(response, text="Paradise5", html=False, status_code=200)

    def test_gazetteer_startdate(self):
        """
        Verify that only placenames that existed on or after the input date are returned
        """
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise/StartDate/2011-07-21")
            placenames = json.loads(response.content)
            self.assertEquals(3, len(placenames))
            self.assertContains(response, text="Paradise2", html=False, status_code=200)
            self.assertContains(response, text="Paradise5", html=False, status_code=200)

    def test_gazetteer_startdate_BC(self):
        """
        Verify that only placenames that existed on or after the input BC date are returned
        """
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise/StartDate/2011-07-21 BC")
            placenames = json.loads(response.content)
            self.assertEquals(3, len(placenames))
            self.assertNotContains(response, text="Paradise3", html=False, status_code=200)


    def test_gazetteer_enddate(self):
        """
        Verify that only placenames that existed on or before the input date are returned
        """
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise/EndDate/2009-07-21")
            placenames = json.loads(response.content)
            self.assertEquals(3, len(placenames))
            self.assertContains(response, text="Paradise3", html=False, status_code=200)
            self.assertContains(response, text="Paradise5", html=False, status_code=200)

    def test_gazetteer_enddate_BC(self):
        """
        Verify that only placenames that existed on or before the input BC date are returned
        """
        if settings.USE_GAZETTEER:
            c = Client()
            response = c.get("/gazetteer/Paradise/EndDate/2013-08-20 BC")
            placenames = json.loads(response.content)
            print response.content
            self.assertEquals(1, len(placenames))
            self.assertContains(response, text="Paradise3", html=False, status_code=200)
