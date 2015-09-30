from os.path import realpath, dirname, isfile, join
from requests.exceptions import ConnectionError as RequestsConnectionError

from unittest import skip
from geonode.contrib.msg_util import *

from geonode.contrib.datatables.forms import DataTableResponseForm#,\


from tabular_test_base import TestTabularAPIBase

class TestLatLngTabularAPI(TestTabularAPIBase):
    """
    @classmethod
    def tearDownClass(cls):
        pass

    @classmethod
    def setUpClass(cls):
        pass
    """
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

        fname_to_upload = join(self.TEST_FILE_DIR, 'coded_data_2008_10-tab.txt')
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

        self.assertTrue(rjson.get('success', False) is True,
                   "Should receive as 'success' value of True.  Found: %s" % r.text
                   )
        self.assertTrue('data' in rjson,
                   "'data' section not found in returned JSON .  Found: %s" % r.text
                   )

        #        data": {"layer_link": "/data/geonode:coded_data_2008_10_tab_1", "unmapped_record_count": 0, "layer_typename": "geonode:coded_data_2008_10_tab_1", "layer_name": "coded_data_2008_10_tab_1", "datatable": "coded_data_2008_10_tab_1", "mapped_record_count": 0, "lng_attribute": {

