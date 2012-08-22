from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from mock import Mock, patch
from django.contrib.gis.geos import Point
from geonode.gazetteer.models import GazetteerEntry
from geonode.gazetteer.utils import getGazetteerResults, parseDate

class GazetteerTest(TestCase):
    multi_db = True
    fixtures = ['gazetteer_data.json']

    def testGazetteerQueryNoDatesOneResult(self):
        if settings.USE_GAZETTEER:
            results = getGazetteerResults('Paradise1')
            self.assertEqual(len(results), 1)

    def testGazetteerQueryNoDatesNoResult(self):
        if settings.USE_GAZETTEER:
            results = getGazetteerResults('Paradiso')
            self.assertEqual(len(results), 0)

    def testGazetteerQueryNoDatesAllResults(self):
        if settings.USE_GAZETTEER:
            results = getGazetteerResults('Paradis')
            self.assertEqual(len(results), 5)

    def testGazetteerQueryWithStartDateAD(self):
        if settings.USE_GAZETTEER:
            results = GazetteerEntry.objects.all()
            # Return all places that existed on this date -
            # Should be two [Paradise1, Paradise5)
            results = getGazetteerResults('Paradis', start_date = '2011-01-01')
            self.assertEqual(len(results), 2)
            for result in results:
                self.assertTrue(result["placename"] in ["Paradise1","Paradise5"])

    def testGazetteerQueryWithStartDateBC(self):
        if settings.USE_GAZETTEER:
            results = GazetteerEntry.objects.all()
            # Return all places that existed on this date -
            # Should be one [Paradise3)
            results = getGazetteerResults('Paradis', start_date = '2010-07-20 BC')
            self.assertEqual(len(results), 1)
            for result in results:
                self.assertTrue(result["placename"] in ["Paradise4"])

    def testGazetteerQueryWithStartDateEndDateAD(self):
        if settings.USE_GAZETTEER:
            results = GazetteerEntry.objects.all()
            # Return all places that existed at some point between these dates -
            # Should be three [Paradise1, Paradise2, Paradise5)
            results = getGazetteerResults('Paradis', start_date = '2010-01-01', end_date= '2011-07-21')
            for result in results:
                self.assertTrue(result["placename"] in ["Paradise1","Paradise2","Paradise5"])
            self.assertEqual(len(results), 3)