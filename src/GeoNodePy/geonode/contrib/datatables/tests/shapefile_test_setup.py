"""
Base test class for testing the WorldMap API used by GeoConnect

"""
import os
from os.path import isfile, join, dirname, realpath

from django.utils import unittest

import json
import string
import random

from django.conf import settings

#------------------

from geonode.contrib.msg_util import *

WORLMAP_TOKEN_NAME = settings.WORLDMAP_TOKEN_NAME_FOR_DV    #'geoconnect_token'
WORLDMAP_TOKEN_VALUE = settings.WORLDMAP_TOKEN_FOR_DATAVERSE    #load_settings_dict()['WORLDMAP_TOKEN_VALUE']

class ShapefileTestSetup(unittest.TestCase):

    def setUp(self):
        msgt('........ set up 1 (base) ................')
        
        # Create database
        #
        #call_command('syncdb', interactive = False)
        
        self.TEST_FILE_DIR = join(dirname(realpath(__file__)), 'input')
        
        # Verify/load dataverse test info
        #
        dataverse_info_test_fixture_fname = join(self.TEST_FILE_DIR, 'dataverse_info_test_fixture.json')
        assert isfile(dataverse_info_test_fixture_fname), "Dataverse test fixture file not found: %s" % dataverse_info_test_fixture_fname
        self.dataverse_test_info = json.loads(open(dataverse_info_test_fixture_fname, 'r').read())
        
        # Verify/load shapefile test info
        #
        shapefile_info_test_fixture_fname = join(self.TEST_FILE_DIR, 'shapefile_info_test_fixture.json')
        assert isfile(shapefile_info_test_fixture_fname), "Shapefile test fixture file not found: %s" % shapefile_info_test_fixture_fname
        self.shapefile_test_info = json.loads(open(shapefile_info_test_fixture_fname, 'r').read())
        
        # Verify that test shapefile exists (good file)
        #
        self.test_shapefile_name = join(self.TEST_FILE_DIR, 'social_disorder_in_boston_yqh.zip')
        assert isfile(self.test_shapefile_name), "Test shapefile not found: %s" % self.test_shapefile_name
    
        # Verify that test shapefile exists (bad file)
        #
        self.test_bad_file = join(self.TEST_FILE_DIR, 'meditation-gray-matter-rebuild.pdf')
        assert isfile(self.test_bad_file), '"Bad"" test shapefile not found: %s' % self.test_bad_file
    


    def tearDown(self):
        pass
        #os.remove(realpath(join('test-scratch', 'scratch.db3')))
