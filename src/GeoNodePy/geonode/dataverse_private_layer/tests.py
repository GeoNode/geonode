"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

"""
django-admin.py shell --settings=geonode.settings

import autocomplete_light
autocomplete_light.autodiscover()
from geonode.maps.models import Layer
from geonode.dataverse_private_layer.permissions_helper import make_layer_private, make_layer_public
#make_layer_private

n = 'bari_q1y'
layer = Layer.objects.get(name=n)

make_layer_private(layer)

make_layer_public(layer)


"""