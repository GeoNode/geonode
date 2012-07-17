from django.test import TestCase
from geonode.catalogue import get_catalogue

class CatalogueTest(TestCase):
    def test_get_catalog(self):
        """
        Tests the get_catalogue function works.
        """
        c = get_catalogue()
