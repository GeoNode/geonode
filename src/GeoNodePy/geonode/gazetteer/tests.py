#from django.conf import settings
#from django.test import TestCase
#from django.test.client import Client
#from mock import Mock, patch
#from django.contrib.gis.geos import Point
#from geonode.gazetteer.models import GazetteerEntry
#from geonode.gazetteer.utils import getGazetteerResults
#
#
##_gaz_entry1 = Mock()
##_gaz_entry1.layer_name = 'test1_gaz'
##_gaz_entry1.layer_attribute = 'la1'
##_gaz_entry1.feature_type = 'POINT'
##_gaz_entry1.feature_fid = 100
##_gaz_entry1.latitude = 40.0
##_gaz_entry1.longitude = -70.0
##_gaz_entry1.place_name = 'gazName1'
##_gaz_entry1.start_date = None
##_gaz_entry1.end_date = None
##_gaz_entry1.project = None
##_gaz_entry1.feature = Point(-70.0,40.0)
#
##getGazetteerResults.return_value = _gaz_entry
#
#
#
#
#class GazetteerTest(TestCase):
#    fixtures = ['test_data.json', 'gazetteer_data.json']
#
#    def testGazetteerQueryNoDates(self):
#        results = getGazetteerResults('test1')
#        self.assertEqual(results.count(), 1)
