# Django settings for GeoNode Integration Test project.
from urllib import urlencode
import os
import geonode

from geonode.settings import *

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
GEONODE_ROOT = os.path.dirname(geonode.__file__)

TEST_RUNNER = 'tests.runner.GeoNodeTestRunner'

NOSE_ARGS = [
        "--verbosity=2",
        "--with-doctest",
        "--nocapture",
        "--detailed-errors",
        "--with-coverage",
        "--cover-package=geonode",
        "--with-xunit"
        # , "tests.geonode_tests:GeoNodeMapTest.test_tiff"
        ]

try:
    from local_settings import *
except ImportError:
    pass
