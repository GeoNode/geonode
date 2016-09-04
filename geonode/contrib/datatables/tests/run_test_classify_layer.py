"""
Run tests for the WorldMap Shapefile import API

python manage.py test apps.worldmap_connect.tests.test_classify_layer.TestWorldMapClassification

"""

import requests
import json

from os.path import abspath, dirname, isfile, join, isdir, realpath
from unittest import skip

from django.core.urlresolvers import reverse

# Validation forms from https://github.com/IQSS/shared-dataverse-information
#
#from shared_dataverse_information.worldmap_api_helper.forms_api_validate import SIGNATURE_KEY

from shared_dataverse_information.shapefile_import.forms import ShapefileImportDataForm

from shared_dataverse_information.map_layer_metadata.forms import WorldMapToGeoconnectMapLayerMetadataValidationForm
from shared_dataverse_information.layer_classification.forms_api import ClassifyRequestDataForm, LayerAttributeRequestForm
from shared_dataverse_information.dataverse_info.forms_existing_layer import CheckForExistingLayerForm

from geonode.contrib.msg_util import *

from tabular_test_base import TestTabularAPIBase

#from run_test_shapefile_import import TestWorldMapShapefileImport
#from worldmap_base_test import WorldMapBaseTest


class TestWorldMapClassification(TestTabularAPIBase):

    @classmethod
    def tearDownClass(cls):
        # We don't need the initial census shapefiles to work with (tabular does)
        pass

    @classmethod
    def setUpClass(cls):
        cls.createDataverseUserAndGroup(add_user_to_dv_group=False)


    def setUp(self):
        super(TestWorldMapClassification, self).setUp()


        self.TEST_FILE_DIR = join(dirname(realpath(__file__)), 'input')

        # -------------------------------------------
        # Verify/load shapefile test info
        # -------------------------------------------
        shapefile_info_test_fixture_fname = join(self.TEST_FILE_DIR, 'shapefile_info_test_fixture.json')
        assert isfile(shapefile_info_test_fixture_fname), "Shapefile test fixture file not found: %s" % shapefile_info_test_fixture_fname
        self.shapefile_test_info = json.loads(open(shapefile_info_test_fixture_fname, 'r').read())

        # -------------------------------------------
        # Verify that test shapefile exists (good file)
        # -------------------------------------------
        self.test_shapefile_name = join(self.TEST_FILE_DIR, 'social_disorder_in_boston_yqh.zip')
        assert isfile(self.test_shapefile_name), "Test shapefile not found: %s" % self.test_shapefile_name

        # -------------------------------------------
        # Verify/load dataverse test info
        # -------------------------------------------
        #dataverse_info_test_fixture_fname = join(self.TEST_FILE_DIR, 'dataverse_info_test_fixture.json')
        dataverse_info_test_fixture_fname = join(self.TEST_FILE_DIR, 'tab_ma_dv_info.json')
        assert isfile(dataverse_info_test_fixture_fname), "Dataverse test fixture file not found: %s" % dataverse_info_test_fixture_fname
        self.dataverse_test_info = json.loads(open(dataverse_info_test_fixture_fname, 'r').read())


        # -------------------------------------------
        # URLs for classify tests
        # -------------------------------------------
        self.api_layer_info_url = self.base_url + reverse('get_existing_layer_data', kwargs={})
        self.classify_layer_url = self.base_url + reverse('view_create_new_layer_style', kwargs={})

        self.upload_test_shapefile()
        # Add a shapefile - also a test
        #shp_import = TestWorldMapShapefileImport('test02_good_shapefile_import')
        #shp_import.setUp()
        #shp_import.test02_good_shapefile_import()

    def tearDown(self):
        super(TestWorldMapClassification, self).tearDown()              #super().__init__(x,y)

        self.delete_test_shapefile()
        # Remove the shapefile - also a test
        #shp_import = TestWorldMapShapefileImport('test04_good_delete_shapefile_from_worldmap')
        #shp_import.setUp()
        #shp_import.test04_good_delete_shapefile_from_worldmap()


    def upload_test_shapefile(self):

        #-----------------------------------------------------------
        msgt("--- Upload Test Shapefile for Classification Test ---")
        #-----------------------------------------------------------
        api_url = self.add_shapefile_url

        #-----------------------------------------------------------
        # Get basic shapefile info
        #-----------------------------------------------------------
        shapefile_api_form = ShapefileImportDataForm(self.shapefile_test_info)
        self.assertTrue(shapefile_api_form.is_valid())

        test_shapefile_info = shapefile_api_form.cleaned_data

        #-----------------------------------------------------------
        # add dv info
        #-----------------------------------------------------------
        test_shapefile_info.update(self.dataverse_test_info)

        #-----------------------------------------------------------
        # prep file
        #-----------------------------------------------------------
        files = {'file': open( self.test_shapefile_name, 'rb')}

        #-----------------------------------------------------------
        #   Test WorldMap shapefile import API
        #-----------------------------------------------------------
        msg('api url: %s' % api_url)
        try:
            r = requests.post(api_url,
                              data=test_shapefile_info,
                              files=files,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg(r.status_code)
        msg(r.text)

        self.assertEqual(r.status_code, 200, "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


    def delete_test_shapefile(self):
        #-----------------------------------------------------------
        msgt("--- Delete Test Shapefile used for Classification Test ---")
        #-----------------------------------------------------------

        api_prep_form = CheckForExistingLayerForm(self.dataverse_test_info)
        self.assertTrue(api_prep_form.is_valid()\
                        , "Error.  Validation failed. (CheckForExistingLayerForm):\n%s" % api_prep_form.errors)

        data_params = api_prep_form.cleaned_data

        msgt('Delete params {0}'.format(data_params))

        try:
            r = requests.post(self.delete_dataverse_layer_url,
                              data=data_params,
                              auth=self.get_creds_for_http_basic_auth(),
                              timeout=5
                              )
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return
        msg(r.text)
        msg(r.status_code)

        self.assertEqual(r.status_code, 200, "Expected status code 200 but received '%s'" % r.status_code)


    #def test_it(self):

    #    self.assertTrue(True)
    #@skip("skipping test01_good_classification")
    def test01_good_classification(self):

        # Note: This has to be imported AFTER WorldMapBaseTest setUp creates a test table
        #
        #-----------------------------------------------------------
        msgn("(1a) Retrieve layer information based on datafile_id and dv_user_id")
        #-----------------------------------------------------------
        msg('api_layer_info_url: %s' % self.api_layer_info_url)

        f = CheckForExistingLayerForm(self.dataverse_test_info)
        self.assertTrue(f.is_valid(), 'Validation failed using CheckForExistingLayerForm')

        # Retrieve Layer metata using datafile_id and dv_user_id
        # e.g.  {'datafile_id': 1388, 'dv_user_id': 1}
        params = f.cleaned_data #()

        msgn('PARAMS: %s' %params)
        try:
            r = requests.post(self.api_layer_info_url,
                              data=params,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msg('Connection error: %s' % e.message)
            self.assertTrue(False, 'Connection error: %s' % e.message)
        except:
            msg("Unexpected error: %s" % sys.exc_info()[0])
            self.assertTrue(False, "Unexpected error: %s" % sys.exc_info()[0])


        print r.text
        print r.status_code

        self.assertEquals(r.status_code, 200, "Expected status code of 200 but received '%s'" % r.status_code)


        #-----------------------------------------------------------
        msgn("(1b) Convert response to JSON")
        #-----------------------------------------------------------
        try:
            rjson = r.json()
        except:
            self.assertTrue(False, "Failed to convert response text to JSON. Text:\n%s" % r.text)

        #-----------------------------------------------------------
        msgn("(1c) Check for key fields in JSON")
        #-----------------------------------------------------------
        #msg(rjson)
        self.assertTrue(rjson.has_key('success'), "JSON did not have key 'success'. Keys found:\n %s" % rjson.keys())
        self.assertTrue(rjson.has_key('data'), "JSON did not have key 'data'. Keys found:\n %s" % rjson.keys())

        self.assertEquals(rjson.get('success'), True, "Expected 'success' value to be 'True'.  Found: '%s'" % rjson.get('success'))


        #-----------------------------------------------------------
        msgn("(1d) Validate returned data using WorldMapToGeoconnectMapLayerMetadataValidationForm\n(includes layer name)")
        #-----------------------------------------------------------
        f = WorldMapToGeoconnectMapLayerMetadataValidationForm(rjson.get('data', {}))

        self.assertTrue(f.is_valid(), 'Validation failed using WorldMapToGeoconnectMapLayerMetadataValidationForm. Errors: %s' % f.errors)



        #-----------------------------------------------------------
        msgn("(1e) Get layer name from data (confirmed by previous validation)")
        #-----------------------------------------------------------
        self.existing_layer_name  = rjson.get('data', {}).get('layer_name', None)

        self.assertTrue( self.existing_layer_name is not None, 'self.existing_layer_name cannot be None')
        self.assertTrue( len(self.existing_layer_name) > 0, 'self.existing_layer_name cannot be length 0')

        #-----------------------------------------------------------
        msgn("(1f) Prepare classification call")
        #-----------------------------------------------------------
        msg('existing_layer_name: %s' % self.existing_layer_name)
        #self.dataverse_test_info


        classify_params = self.dataverse_test_info

        classify_params.update({'reverse': False,
                                'attribute': u'SocStrif_2',
                                'ramp': 'Blue',
                                'endColor': '#08306b',
                                'intervals': 5,
                                'layer_name': self.existing_layer_name,
                                'startColor': '#f7fbff',
                                'method': u'equalInterval'})

        """
import requests
classify_params =  {'reverse': False,
            'attribute': u'SocStrife1',
            'dataverse_installation_name': u'http://localhost:8000',
            'ramp': u'Custom', 'endColor': u'#f16913',
            'datafile_id': 7775,
            'intervals': 5,
            'layer_name': u'social_disorder_hy4',
            'startColor': u'#fff5eb',
            'method': u'jenks'}

r = requests.post('http://127.0.0.1:8000/dataverse/classify-layer/',data=classify_params, auth=('rp','123'))

print r.text

print r.status_code

        """
        f_classify = ClassifyRequestDataForm(classify_params)
        self.assertTrue(f_classify.is_valid(), 'ClassifyRequestDataForm did not validate. Errors:\n %s' % f_classify.errors)

        formatted_classify_params = f_classify.cleaned_data #get_api_params_with_signature()
        msgt('classify_params: %s' % formatted_classify_params)
        #self.assertTrue(classify_params.has_key(SIGNATURE_KEY)\
        #                , 'classify_params did not have SIGNATURE_KEY: "%s"' % SIGNATURE_KEY)




        #-----------------------------------------------------------
        msgn("(1g) Make classification request")
        #-----------------------------------------------------------
        msg('classify url: %s' % self.classify_layer_url)
        msg('creds: {0}'.format(self.get_creds_for_http_basic_auth()))
        try:
            r = requests.post(self.classify_layer_url,
                              data=formatted_classify_params,
                              auth=self.get_creds_for_http_basic_auth()
                              )
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message)
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        print r.text
        print r.status_code

        self.assertEquals(r.status_code, 200, "Expected status code of 200 but received '%s'" % r.status_code)


        #-----------------------------------------------------------
        msgn("(1h) Convert response to JSON")
        #-----------------------------------------------------------
        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response text to JSON. Text:\n%s" % r.text)

        print 'json_resp: %s' % json_resp

        self.assertTrue(json_resp.has_key('success'), 'JSON should have key "success".  But found keys: %s' % json_resp.keys())
        self.assertEqual(json_resp.get('success'), True, "'success' value should be 'True'")

        f_metadata_check = WorldMapToGeoconnectMapLayerMetadataValidationForm(json_resp.get('data', None))
        self.assertTrue(f_metadata_check.is_valid(), "Validation failed for WorldMapToGeoconnectMapLayerMetadataValidationForm. Errors: %s" % f_metadata_check.errors)


        #-----------------------------------------------------------
        msgn("(1i) Retrieve classification params")
        #-----------------------------------------------------------
        params_for_attr_request = self.dataverse_test_info
        params_for_attr_request['layer_name'] = self.existing_layer_name
        f_attrs = LayerAttributeRequestForm(params_for_attr_request)
        self.assertTrue(f_attrs.is_valid(), 'ClassifyRequestDataForm did not validate. Errors:\n %s' % f_attrs.errors)

        retrieve_attribute_params = f_attrs.cleaned_data  #get_api_params_with_signature()
        #msgt('retrieve_attribute_params: %s' % retrieve_attribute_params)
        #self.assertTrue(retrieve_attribute_params.has_key(SIGNATURE_KEY)\
        #                , 'classify_params did not have SIGNATURE_KEY: "%s"' % SIGNATURE_KEY)


        #-----------------------------------------------------------
        msgn("(1i) Make classification param request")
        #-----------------------------------------------------------
        GET_CLASSIFY_ATTRIBUTES_API_PATH = reverse('view_layer_classification_attributes', args=())
        try:
            r = requests.post(GET_CLASSIFY_ATTRIBUTES_API_PATH,\
                        data=retrieve_attribute_params,\
                        auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message)
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        print r.status_code
        self.assertEquals(r.status_code, 200, "Expected status code of 200 but received '%s'" % r.status_code)

        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response text to JSON. Text:\n%s" % r.text)

        self.assertTrue(json_resp.has_key('success'), 'JSON should have key "success".  But found keys: %s' % json_resp.keys())
        self.assertEqual(json_resp.get('success'), True, "'success' value should be 'True'")

        self.assertTrue(json_resp.has_key('data'), 'JSON should have key "success".  But found keys: %s' % json_resp.keys())

        attribute_info = json_resp['data'].get('attribute_info', None)
        self.assertTrue(attribute_info is not None, "attribute_info was None")

        attribute_info = eval(attribute_info)
        msgt('attribute_info')
        msg(attribute_info)
        self.assertEqual(len(attribute_info), 53,\
            "Should be 54 attributes but found %s" % len(attribute_info))
