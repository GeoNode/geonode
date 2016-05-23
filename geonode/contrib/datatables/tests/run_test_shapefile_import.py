from os.path import realpath, dirname, isfile, join, isdir
import requests
import json

from unittest import skip

#   Base test class
#
from tabular_test_base import TestTabularAPIBase

# Validation forms from https://github.com/IQSS/shared-dataverse-information
#
from shared_dataverse_information.shapefile_import.forms import ShapefileImportDataForm
from shared_dataverse_information.dataverse_info.forms_existing_layer import CheckForExistingLayerForm
from shared_dataverse_information.map_layer_metadata.forms import MapLayerMetadataValidationForm

from geonode.contrib.msg_util import *


class TestWorldMapShapefileImport(TestTabularAPIBase):

    @classmethod
    def tearDownClass(cls):
        # We don't need the initial shapefile to work with (tabular does)
        pass

    @classmethod
    def setUpClass(cls):
        cls.createDataverseUserAndGroup(add_user_to_dv_group=False)


    def setUp(self):
        super(TestWorldMapShapefileImport, self).setUp()

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

        # Verify/load geotiff test information
        geotiff_info_test_fixture_fname = join(self.TEST_FILE_DIR, 'geotiff_info_test.json')
        assert isfile(geotiff_info_test_fixture_fname), "GeoTiff test fixture file not found: %s" % geotiff_info_test_fixture_fname
        self.geotiff_test_info = json.loads(open(geotiff_info_test_fixture_fname, 'r').read())

        # Verify that test geotiff exists (good file)
        #
        self.test_geotiff_fname = join(self.TEST_FILE_DIR, 'Neighborhoods_BRA_1.tiff')
        assert isfile(self.test_geotiff_fname), "Test geotiff not found: %s" % self.test_geotiff_fname




    def tearDown(self):
        pass
        #os.remove(realpath(join('test-scratch', 'scratch.db3')))

    #@skip("skipping")
    def test01_bad_shapefile_imports(self):

        #-----------------------------------------------------------
        msgt("--- Shapefile imports (that should fail) ---")
        #-----------------------------------------------------------
        api_url = self.add_shapefile_url

        #-----------------------------------------------------------
        msgn("(1a) Test WorldMap shapefile import API but without any payload (GET instead of POST)")
        #-----------------------------------------------------------
        msg('api_url: %s' % api_url)
        try:
            r = requests.post(api_url,
                        auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg(r.status_code)

        self.assertEqual(r.status_code, 401, "Should receive 401 error.  Received: %s\n%s" % (r.status_code, r.text))
        expected_msg = 'The request must be a POST.'
        self.assertEqual(r.json().get('message'), expected_msg\
                , 'Should receive message: "%s".  Received: %s' % (expected_msg, r.text))


        #-----------------------------------------------------------
        msgn("(1b) Test WorldMap shapefile import API but use a BAD credentials")
        #-----------------------------------------------------------

        #   Test WorldMap shapefile import API but use a BAD TOKEN
        #
        #r = requests.post(api_url, data=json.dumps( self.get_worldmap_random_token_dict() ))
        try:
            r = requests.post(api_url,
                              auth=('not-a-real-user-789', 'with-not-a-real-password-123'))
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg(r.status_code)

        self.assertEqual(r.status_code, 401, "Should receive 401 error.  Received: %s\n%s" % (r.status_code, r.text))
        try:
            json_resp = r.json()
        except:
            self.assertTrue(False,  "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return

        expected_msg = 'Login failed'
        self.assertEqual(json_resp.get('message'), expected_msg,
                'Should receive message: "%s".  Received: %s' % (expected_msg, r.text))


        #-----------------------------------------------------------
        msgn("(1c) Test WorldMap shapefile import API but FAIL to include a file")
        #-----------------------------------------------------------
        # Get basic shapefile info
        shapefile_api_form = ShapefileImportDataForm(self.shapefile_test_info)
        self.assertTrue(shapefile_api_form.is_valid())
        params = shapefile_api_form.cleaned_data
        test_shapefile_info = params.copy()
        # add dv info
        params.update(self.dataverse_test_info)

        #   Test WorldMap shapefile import API but FAIL to include a file
        #
        msg('api url: %s' % api_url)
        try:
            r = requests.post(api_url,
                              data=params,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg(r.status_code)
        #msg(r.text)
        self.assertEqual(r.status_code, 400, "Should receive 400 error.  Received: %s\n%s" % (r.status_code, r.text))
        expected_msg = 'File not found.  Did you send a file?'
        self.assertEqual(r.json().get('message'), expected_msg\
                    , 'Should receive message: "%s".  Received: %s' % (expected_msg, r.text))

        #-----------------------------------------------------------
        msgn("(1d) Test WorldMap shapefile import API but send 2 files instead of 1")
        #-----------------------------------------------------------
        files = {   'file': open( self.test_shapefile_name, 'rb')\
                    , 'file1': open( self.test_shapefile_name, 'rb')\
                }

        #   Test WorldMap shapefile import API but send 2 files instead of 1
        #
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

        self.assertEqual(r.status_code, 400, "Should receive 400 error.  Received: %s\n%s" % (r.status_code, r.text))

        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON. Received: %s" % r.text)


        expected_msg = 'This request only accepts a single file'
        self.assertTrue(json_resp.get('message','').startswith(expected_msg),
                'Should receive message: "%s".  Received: %s' % (expected_msg, r.text))



        #-----------------------------------------------------------
        msgn("(1e) Test WorldMap shapefile import API with payload except file (metadata is not given)")
        #-----------------------------------------------------------
        # prep file
        files = {'file': open( self.test_shapefile_name, 'rb')}

        test_shapefile_info_missing_pieces = test_shapefile_info.copy()
        test_shapefile_info_missing_pieces.pop('dv_user_email')
        test_shapefile_info_missing_pieces.pop('abstract')
        test_shapefile_info_missing_pieces.pop('shapefile_name')
        test_shapefile_info_missing_pieces.pop('title')

        #   Test WorldMap shapefile import API with payload except file (metadata is not given)
        #
        try:
            r = requests.post(api_url,
                              data=test_shapefile_info_missing_pieces,
                              files=files,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg(r.status_code)

        self.assertEqual(r.status_code, 400, "Should receive 400 error.  Received: %s\n%s" % (r.status_code, r.text))
        expected_msg = "Incorrect params for ShapefileImportDataForm: <br /><ul class=\"errorlist\"><li>dv_user_email<ul class=\"errorlist\"><li>This field is required.</li></ul></li><li>abstract<ul class=\"errorlist\"><li>This field is required.</li></ul></li><li>shapefile_name<ul class=\"errorlist\"><li>This field is required.</li></ul></li><li>title<ul class=\"errorlist\"><li>This field is required.</li></ul></li></ul>"
        self.assertEqual(r.json().get('message'), expected_msg\
                , 'Should receive message: "%s".  Received: %s' % (expected_msg, r.text))



        #-----------------------------------------------------------
        msgn("(1f) Test ShapefileImportDataForm. Use data missing the 'title' attribute")
        #-----------------------------------------------------------
        # Pop 'title' from shapefile info
        #
        test_shapefile_info_missing_pieces = test_shapefile_info.copy()
        test_shapefile_info_missing_pieces.pop('title')

        # Form should mark data as invalid
        #
        f1_shapefile_info = ShapefileImportDataForm(test_shapefile_info_missing_pieces)
        self.assertEqual(f1_shapefile_info.is_valid(), False, "Data should be invalid")
        self.assertTrue(len(f1_shapefile_info.errors.values()) == 1, "Form should have one error")
        self.assertTrue(f1_shapefile_info.errors.has_key('title'), "Error keys should contain 'title'")
        self.assertEqual(f1_shapefile_info.errors.values(), [[u'This field is required.']]\
                        , "Error for 'title' field should be: [[u'This field is required.']]")


        #-----------------------------------------------------------
        msgn("(1g) Test ShapefileImportDataForm. Use good data")
        #-----------------------------------------------------------
        #test_shapefile_info = self.shapefile_test_info.copy()

        f2_shapefile_info = ShapefileImportDataForm(test_shapefile_info)
        self.assertTrue(f2_shapefile_info.is_valid(), "Data should be valid")

        #-----------------------------------------------------------
        msgn("(1h) Test WorldMap shapefile import API without credentials.")
        #-----------------------------------------------------------
        # Get basic shapefile info
        shapefile_api_form = ShapefileImportDataForm(self.shapefile_test_info)
        self.assertTrue(shapefile_api_form.is_valid())

        test_shapefile_info = shapefile_api_form.cleaned_data

        # add dv info
        test_shapefile_info.update(self.dataverse_test_info)

        # prep file
        files = {'file': open( self.test_shapefile_name, 'rb')}

        #   Test WorldMap shapefile import API but dataverse_info is missing
        #
        msg('api url: %s' % api_url)
        try:
            r = requests.post(api_url,
                              data=test_shapefile_info,
                              files=files)
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg(r.status_code)
        msg(r.text)

        self.assertEqual(r.status_code, 401, "Should receive 401 error.  Received: %s\n%s" % (r.status_code, r.text))


        #-----------------------------------------------------------
        msgn("(1i) Test WorldMap shapefile import API but file is NOT a shapefile")
        #-----------------------------------------------------------
        # Get basic shapefile info
        shapefile_api_form = ShapefileImportDataForm(self.shapefile_test_info)
        self.assertTrue(shapefile_api_form.is_valid())

        test_shapefile_info = shapefile_api_form.cleaned_data

        # add dv info
        test_shapefile_info.update(self.dataverse_test_info)
        test_shapefile_info['datafile_id'] = 4001999


        # prep file
        files = {'file': open(self.test_bad_file, 'rb')}


        #   Test WorldMap shapefile import API but file is NOT a shapefile
        #
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

        self.assertEqual(r.status_code, 500, "Should receive 500 message.  Received: %s\n%s" % (r.status_code, r.text))
        expected_err = 'Unexpected error during upload:'
        self.assertTrue(r.text.find(expected_err) > -1\
                    , "Should have message containing %s\nFound: %s" \
                        % (expected_err, r.text)\
                    )

    #@skip("skipping")
    def test02_good_shapefile_import(self):

        #-----------------------------------------------------------
        msgt("--- Shapefile import (good) ---")
        #-----------------------------------------------------------
        api_url = self.add_shapefile_url

        #-----------------------------------------------------------
        msgn("(2a) Test WorldMap shapefile import API -- with GOOD data/file")
        #-----------------------------------------------------------
        # Get basic shapefile info
        shapefile_api_form = ShapefileImportDataForm(self.shapefile_test_info)
        self.assertTrue(shapefile_api_form.is_valid())

        test_shapefile_info = shapefile_api_form.cleaned_data

        # add dv info
        test_shapefile_info.update(self.dataverse_test_info)

        # prep file
        files = {'file': open( self.test_shapefile_name, 'rb')}

        #   Test WorldMap shapefile import API
        #
        msg('api url: %s' % api_url)
        #r = requests.post(api_url\
        #                    , data=test_shapefile_info\
        #                    , files=files)

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

        #open('/Users/rmp553/Desktop/page_out.html', 'w').write(r.text)
        #return
        #   Expect HTTP 200 - success
        #
        self.assertEqual(r.status_code, 200, "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


        #-----------------------------------------------------------
        msgn("(2b) Examine JSON result from WorldMap shapefile import API")
        #-----------------------------------------------------------
        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON. Received: %s" % r.text)

        #   Expect 'success' key to be True
        #
        self.assertTrue('success' in json_resp, 'JSON should have key "success".  But found keys: %s' % json_resp.keys())
        self.assertEqual(json_resp.get('success'), True, "'success' value should be 'true'")

        #   Expect data key in JSON
        #
        self.assertTrue('data' in json_resp, 'JSON should have key "data".  But found keys: %s' % json_resp.keys())

        #-----------------------------------------------------------
        msgn("(2c) Use MapLayerMetadataValidationForm to validate JSON result from WorldMap shapefile import API")
        #-----------------------------------------------------------
        #   Validate JSON data using MapLayerMetadataValidationForm
        #
        map_layer_metadata_data = json_resp.get('data')
        f3_dataverse_info = MapLayerMetadataValidationForm(map_layer_metadata_data)

        self.assertTrue(f3_dataverse_info.is_valid(),
                        "Failed to validate JSON data using MapLayerMetadataValidationForm.  Found errors: %s" \
                        % f3_dataverse_info.errors
                )

        #-----------------------------------------------------------
        msgn("(2d) Retrieve layer details - successfully")
        #-----------------------------------------------------------
        #   Validate JSON data using MapLayerMetadataValidationForm
        #
        existing_layer_form = CheckForExistingLayerForm(self.dataverse_test_info)
        self.assertTrue(existing_layer_form.is_valid()\
                        , "Error.  Validation failed:\n%s" % existing_layer_form.errors)

        data_params = existing_layer_form.cleaned_data

        try:
            r = requests.post(self.dataverse_map_layer_detail,
                              data=data_params,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        msg(r.text)

        self.assertEqual(r.status_code, 200, "Expected status code 200 but received '%s'" % r.status_code)

        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON. Received: %s" % r.text)

        self.assertTrue('success' in json_resp, 'JSON should include key "success".  But found keys: %s' % json_resp.keys())
        self.assertTrue(json_resp.get('success', False) is True, "'success' value should be 'True'")
        self.assertTrue('data' in json_resp, 'JSON should include key "data".  But found keys: %s' % json_resp.keys())

    #@skip("skipping")
    def test03_bad_delete_shapefile_from_worldmap(self):
        #-----------------------------------------------------------
        msgt("--- Delete shapefile ---")
        #-----------------------------------------------------------

        #-----------------------------------------------------------
        msgn("(3a) Send delete request - Missing parameter")
        #-----------------------------------------------------------
        existing_layer_form = CheckForExistingLayerForm(self.dataverse_test_info)
        self.assertTrue(existing_layer_form.is_valid()\
                        , "Error.  Validation failed. (CheckForExistingLayerForm):\n%s" % existing_layer_form.errors)

        data_params = existing_layer_form.cleaned_data
        data_params.pop('datafile_id')

        try:
            r = requests.post(self.delete_dataverse_layer_url,
                              data=data_params,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        self.assertEqual(r.status_code, 400, "Expected status code 400 but received '%s'" % r.status_code)

        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON. Received: %s" % r.text)

            #   Expect 'success' key to be False
        #
        self.assertTrue(json_resp.has_key('success'), 'JSON should have key "success".  But found keys: %s' % json_resp.keys())
        self.assertEqual(json_resp.get('success'), False, "'success' value should be 'False'")
        expected_msg = 'Invalid data for delete request.'
        self.assertEqual(json_resp.get('message'), expected_msg, 'Message should be "%s"' % expected_msg)


        #-----------------------------------------------------------
        msgn("(3b) Send delete request - Bad dataverse_installation_name")
        #-----------------------------------------------------------
        api_prep_form = CheckForExistingLayerForm(self.dataverse_test_info)
        self.assertTrue(api_prep_form.is_valid()\
                        , "Error.  Validation failed. (CheckForExistingLayerForm):\n%s" % api_prep_form.errors)

        data_params = api_prep_form.cleaned_data

        # Chnange key used to search for map layer
        #
        data_params['dataverse_installation_name'] = 'bah bah black sheep'

        try:
            r = requests.post(self.delete_dataverse_layer_url,
                              data=data_params,
                              auth=self.get_creds_for_http_basic_auth()
                              )
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        self.assertEqual(r.status_code, 404, "Expected status code 404 but received '%s'" % r.status_code)

    #@skip("skipping")
    def test04_good_delete_shapefile_from_worldmap(self):

        #-----------------------------------------------------------
        msgn("(4a) Send delete request - Good parameters")
        #-----------------------------------------------------------
        api_prep_form = CheckForExistingLayerForm(self.dataverse_test_info)
        self.assertTrue(api_prep_form.is_valid()\
                        , "Error.  Validation failed. (CheckForExistingLayerForm):\n%s" % api_prep_form.errors)

        data_params = api_prep_form.cleaned_data

        try:
            r = requests.post(self.delete_dataverse_layer_url,
                              data=data_params,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message)
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        self.assertEqual(r.status_code, 200, "Expected status code 200 but received '%s'" % r.status_code)


        #-----------------------------------------------------------
        msgn("(4b) Examine JSON result from WorldMap shapefile delete API")
        #-----------------------------------------------------------
        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON. Received: %s" % r.text)

        #   Expect 'success' key to be True
        #
        self.assertTrue(json_resp.has_key('success'), 'JSON should have key "success".  But found keys: %s' % json_resp.keys())
        self.assertEqual(json_resp.get('success'), True, "'success' value should be 'True'")
        expected_msg = "Layer deleted"
        self.assertEqual(json_resp.get('message'), expected_msg, 'Message should be "%s"'% expected_msg)


    #@skip("skipping")
    def test_05_good_geotiff_import(self):
        """
        Test GeoTIFF import API

        Note: It is the same endpoint as the shapefiles.
        This test is simply adding a valid file.
        """
        api_url = self.add_geotiff_url

        #-----------------------------------------------------------
        msgn("(5) Test WorldMap GeoTIFF import API -- with GOOD data/file")
        #-----------------------------------------------------------
        # Get basic GeoTIFF info
        geotiff_api_form = ShapefileImportDataForm(self.geotiff_test_info)
        self.assertTrue(geotiff_api_form.is_valid())

        cleaned_geotiff_info = geotiff_api_form.cleaned_data

        # add dv info
        cleaned_geotiff_info.update(self.geotiff_test_info)

        # prep file
        files = {'file': open( self.test_geotiff_fname, 'rb')}

        # Send it over!
        msg('api url: %s' % api_url)
        try:
            r = requests.post(api_url,
                              data=cleaned_geotiff_info,
                              files=files,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg(r.status_code)
        msg(r.text)

        #open('/Users/rmp553/Desktop/page_out.html', 'w').write(r.text)
        #return
        #   Expect HTTP 200 - success
        #
        self.assertEqual(r.status_code, 200, "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


    #@skip("skipping")
    def test_06_good_delete_geotiff_from_worldmap(self):

        #-----------------------------------------------------------
        msgn("(6a) Send GeoTIFF delete request - Good parameters")
        #-----------------------------------------------------------
        api_prep_form = CheckForExistingLayerForm(self.geotiff_test_info)
        self.assertTrue(api_prep_form.is_valid()\
                        , "Error.  Validation failed. (CheckForExistingLayerForm):\n%s" % api_prep_form.errors)

        data_params = api_prep_form.cleaned_data

        try:
            r = requests.post(self.delete_dataverse_layer_url,
                              data=data_params,
                              auth=self.get_creds_for_http_basic_auth())
        except requests.exceptions.ConnectionError as e:
            msgx('Connection error: %s' % e.message)
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        self.assertEqual(r.status_code, 200, "Expected status code 200 but received '%s'" % r.status_code)


        msg(r.status_code)
        msg(r.text)

        #-----------------------------------------------------------
        msgn("(6b) Examine JSON result from WorldMap GeoTIFF delete API")
        #-----------------------------------------------------------
        try:
            json_resp = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON. Received: %s" % r.text)

        msg(r.status_code)

        #   Expect 'success' key to be True
        #
        self.assertTrue(json_resp.has_key('success'), 'JSON should have key "success".  But found keys: %s' % json_resp.keys())
        self.assertEqual(json_resp.get('success'), True, "'success' value should be 'True'")
        expected_msg = "Layer deleted"
        self.assertEqual(json_resp.get('message'), expected_msg, 'Message should be "%s"'% expected_msg)
