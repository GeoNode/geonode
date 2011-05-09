# Django settings for GeoNode Integration Test project.
from urllib import urlencode
import os
import geonode

from geonode.settings import *

TEST_RUNNER = 'tests.runner.GeoNodeTestRunner'

NOSE_ARGS = [
        "--verbosity=2",
        "--with-doctest",
        "--nocapture",
        "--detailed-errors"
        ]

try:
    from local_settings import *
except ImportError:
    pass
