"""
Run tests for the WorldMap Tabular API

python manage.py test datatables.TestWorldMapTabularAPI --settings=geonode.no_db_settings

What these tests do:
    (Note: Setup takes several seconds)

    Setup at the ~class~ level: Uploads a shapefile to use as an existing Layer

        Test:


"""
from os.path import realpath, dirname, isfile, join
from requests.exceptions import ConnectionError as RequestsConnectionError

from unittest import skip
from geonode.contrib.msg_util import *

from geonode.contrib.datatables.forms import DataTableResponseForm,\
                                        TableJoinResultForm

from tabular_test_base import TestTabularAPIBase
from shared_dataverse_information.map_layer_metadata.forms import MapLayerMetadataValidationForm

import time


class TestDataverseTabularAPI(TestTabularAPIBase):


    #@classmethod
    #def tearDownClass(cls):
    #    pass

    @classmethod
    def setUpClass(cls):
        super(TestDataverseTabularAPI, cls).setUpClass()
        pause_time = 5 # seconds
        time.sleep(pause_time)
        msgt("""Sleeping %d seconds - needed for Geoserver to calculate bbox other shapefile stats""" % pause_time)

    @classmethod
    def tearDownClass(cls):
        super(TestDataverseTabularAPI, cls).tearDownClass()

    def setUp(self):
        super(TestDataverseTabularAPI, self).setUp()

    def tearDown(self):
        super(TestDataverseTabularAPI, self).tearDown()

    def get_dataverse_csv_test_info(self):
        return {
            "datafile_content_type": "text/comma-separated-values",
            "datafile_create_datetime": "2015-09-24 10:00:54.544",
            "datafile_expected_md5_checksum": "87df5ed0314ba91d300e2c19e40e847a",
            "datafile_download_url": "http://localhost:8080/api/access/datafile/727",
            "datafile_filesize": 39587,
            "datafile_id": 727,
            "datafile_label": "boston-income.csv",

            "dataset_id": 1383,
             "dataset_name": "Boston Income",
             "dataset_semantic_version": "DRAFT",
             "dataset_citation": "A BARI User 2014, \"social disorder\", http://dx.doi.org/10.5072/FK2/1383,  Root Dataverse,  DRAFT VERSION ",
             "dataset_description": "",
             "dataset_version_id": 362,

            "dataverse_id": 1,
            "dataverse_name": "Root",
            "dataverse_installation_name": "Harvard Test Dataverse",
            "dataverse_description": "For testing only.",

            "dv_user_id": 1,
            "dv_user_email": "bari@bari.com",
            "dv_username": "BARI USER",
            "return_to_dataverse_url": "http://localhost:8080/dataset.xhtml?id=727"
        }

    #@skip('skipping test_02_upload_join_boston_income')
    def test_01_upload_join_boston_income(self):

        msgt('(1) Good Upload and Join - Delete TableJoin (test_01_upload_join_boston_income)')

        fname_to_upload = join(self.TEST_FILE_DIR, 'boston-income.csv')
        assert isfile(fname_to_upload), "File not found: %s" % fname_to_upload

        layer_attribute_name = 'TRACTCE'
        self.assertTrue(self.is_attribute_in_ma_layer(layer_attribute_name),
                    "Attribute '%s' not found in layer '%s'" % (layer_attribute_name, self.existing_layer_name))

        params = self.get_join_datatable_params()
        params.update(self.get_dataverse_csv_test_info())

        # -----------------------------------------------------------
        msgn('(1a) Upload table and join layer')
        # -----------------------------------------------------------
        print 'dataverse_upload_and_join_datatable_url',  self.dataverse_upload_and_join_datatable_url
        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.dataverse_upload_and_join_datatable_url,
                                data=params,
                                files=files,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        msg(r.status_code)
        msg('r.text: %s' % r.text)

        self.assertEqual(r.status_code, 200, "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))
        msg('DataTable uploaded and joined!')



        # -----------------------------------------------------------
        msgn('(1b) Check result of join')
        # -----------------------------------------------------------

        try:
            json_resp = r.json()
        except:
            self.assertTrue(False,  "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return

        #------------
        #   Expect 'success' key to be True
        #
        self.assertTrue(json_resp.has_key('success'), 'JSON should have key "success".  But found keys: %s' % json_resp.keys())
        self.assertEqual(json_resp.get('success'), True, "'success' value should be 'true'")

        #   Expect data key in JSON
        #
        self.assertTrue(json_resp.has_key('data'), 'JSON should have key "data".  But found keys: %s' % json_resp.keys())

        self.assertTrue('table_id' in json_resp.get('data', {}), 'JSON should have key "data[\'table_id\']".  But found keys: %s' % json_resp.get('data', {}).keys())

        new_table_id = json_resp['data']['table_id']

        #-----------------------------------------------------------
        msgn("(1c) Use MapLayerMetadataValidationForm to validate JSON result from WorldMap shapefile import API")
        #-----------------------------------------------------------
        #   Validate JSON data using MapLayerMetadataValidationForm
        #
        map_layer_metadata_data = json_resp.get('data')
        f3_dataverse_info = MapLayerMetadataValidationForm(map_layer_metadata_data)

        self.assertTrue(f3_dataverse_info.is_valid(),
                        "Failed to validate JSON data using MapLayerMetadataValidationForm.  Found errors: %s"
                        % f3_dataverse_info.errors)


        datatable_id = json_resp.get('data').get('table_id', None)
        self.assertTrue(datatable_id is not None, "The JSON response did not include data['table_id']")

        #-----------------------------------------------------------
        msgt('(1d) Delete dataverse created layer (test_02_delete_dataverse_created_layer)')
        #-----------------------------------------------------------

        params = dict(dataverse_installation_name=self.get_dataverse_csv_test_info()['dataverse_installation_name'],
                      datafile_id=self.get_dataverse_csv_test_info()['datafile_id'])

        try:
            r = self.client.post(self.delete_dataverse_layer_url,
                                data=params,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return


        self.assertEqual(r.status_code, 200, "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))
        msgn('Delete successful.')

        #-----------------------------------------------------------
        msgt('(1e) Delete the uploaded table')
        #-----------------------------------------------------------

        api_del_url = self.delete_datatable_url.replace(self.URL_ID_ATTR, str(datatable_id))
        msg('Delete datatable url: %s' % api_del_url)

        try:
            r = self.client.get(api_del_url,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        self.assertEqual(r.status_code, 200, "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))
        msgn('Datatable Delete successful.')
        msg('returned json: %s' % r.text)
