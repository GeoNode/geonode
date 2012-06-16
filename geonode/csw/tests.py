from django.test import TestCase
from geonode.csw import get_catalogue

class CSWTest(TestCase):
    def test_get_catalog(self):
        """
        Tests the get_csw function works.
        """
        c = get_catalogue()
