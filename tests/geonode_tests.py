import os
from django.conf import settings
from unittest import TestCase

TEST_DATA = os.path.join(settings.PROJECT_ROOT, 'geonode_test_data')

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

    def test_something(self):
        assert(True)
