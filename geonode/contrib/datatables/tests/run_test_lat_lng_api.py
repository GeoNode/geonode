from os.path import realpath, dirname, isfile, join
import json
from requests.exceptions import ConnectionError as RequestsConnectionError

from unittest import skip
from geonode.contrib.msg_util import *

from geonode.contrib.datatables.forms import DataTableResponseForm#,\


from tabular_test_base import TestTabularAPIBase

class TestLatLngTabularAPI(TestTabularAPIBase):

    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        tab_ma_dataverse_info_fname = join(cls.TEST_FILE_DIR, 'tab_ma_dv_info.json')
        assert isfile(tab_ma_dataverse_info_fname),\
            "MA tigerlines test fixture file not found: %s" % tab_ma_dataverse_info_fname
        cls.tab_ma_dv_info = json.loads(open(tab_ma_dataverse_info_fname, 'r').read())
        cls.createDataverseUserAndGroup(add_user_to_dv_group=False)

    def get_lat_lng_upload_params(self):
        return dict(title="New Haven, CT Crime, October 2008",
                    abstract="Data with unchecked geocoding",
                    delimiter='\t',
                    lng_attribute='Longitude',
                    lat_attribute='Latitude'
        )


    def test_01_upload_lat_lng_table(self):
        """
        Upload DataTable, Join it to a Layer, and Delete it

        """
        msgt('(1) Upload Good Lat/Lng File')

        #fname_to_upload = join(self.TEST_FILE_DIR, 'coded_data_2008_10-tab.txt')
        fname_to_upload = join(self.TEST_FILE_DIR, 'coded_data_2007_09.txt')

        assert isfile(fname_to_upload), "File not found: %s" % fname_to_upload

        params = self.get_lat_lng_upload_params()

        #self.login_for_cookie()

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_lat_lng_url,
                                    data=params,
                                    auth=(self.geonode_username, self.geonode_password),
                                    files=files)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        msg(r.status_code)
        msg(r.text)

        self.assertTrue(r.status_code==200,
            "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))

        try:
            rjson = r.json()
        except:
            self.assertTrue(False,
                    "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return

        self.assertTrue(rjson.get('success', False) is True,
                   "Should receive as 'success' value of True.  Found: %s" % r.text
                   )
        self.assertTrue('data' in rjson,
                   "'data' section not found in returned JSON .  Found: %s" % r.text
                   )

        self.assertTrue('lat_lng_record_id' in rjson.get('data', {}),
                   "lat_lng_record_id not found in 'data' section of returned JSON .  Found: %s" % r.text
                   )

        lat_lng_record_id = rjson.get('data', {}).get('lat_lng_record_id')

        num_matched_records = rjson.get('data', {}).get('mapped_record_count', 0)
        self.assertTrue(num_matched_records == 6157,\
                    "The 'mapped_record_count' should be 6157")

        unmapped_record_count = rjson.get('data', {}).get('unmapped_record_count', 0)
        self.assertTrue(unmapped_record_count == 18,\
                    "The 'mapped_record_count' should be 18")

        unmapped_records_list = rjson.get('data', {}).get('unmapped_records_list', 0)
        self.assertTrue(len(unmapped_records_list) == 18,\
                    "The 'unmapped_records_list' should have 18 entries")

        #        data": {"layer_link": "/data/geonode:coded_data_2008_10_tab_1", "unmapped_record_count": 0, "layer_typename": "geonode:coded_data_2008_10_tab_1", "layer_name": "coded_data_2008_10_tab_1", "datatable": "coded_data_2008_10_tab_1", "mapped_record_count": 0, "lng_attribute": {

        msgt('2 - Delete Datatable Lat/Lng Record')
        api_del_url = self.delete_datatable_lat_lon_url.replace(self.URL_ID_ATTR, str(lat_lng_record_id))
        msg('Delete lat/lng datatable url: %s' % api_del_url)


        try:
            r = self.client.get(api_del_url, auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        msg(r.status_code)
        msg(r.text)

        self.assertTrue(r.status_code == 200
                        , "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))

        msg('Datatable Lat/Lng Record deleted: %s' % r.text)
