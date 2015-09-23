from os.path import realpath, dirname, isfile, join
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
        pass

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


        self.login_for_cookie()

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_lat_lng_url,
                                    data=params,
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

        f = TableJoinResultForm(rjson)
        self.assertTrue(f.is_valid(),
                "Validation failed with TableJoinResultForm: %s" % f.errors)
        # -----------------------------------------------------------
        # Pull out table_id and tablejoin_id
        #   for detail and delete tests
        # -----------------------------------------------------------
        table_id = f.cleaned_data.get('table_id', None)
        self.assertTrue(table_id is not None,
                'table_id should not be None. cleaned form data: %s' % (f.cleaned_data))

        tablejoin_id = f.cleaned_data.get('tablejoin_id', None)
        self.assertTrue(tablejoin_id is not None,
                'tablejoin_id should not be None. cleaned form data: %s' % f.cleaned_data)


        # -----------------------------------------------------------
        msgn('(3b) DataTable Detail')
        # -----------------------------------------------------------
        api_detail_url = self.datatable_detail.replace(self.URL_ID_ATTR, str(table_id))

        self.login_for_cookie()

        r = None
        try:
            r = self.client.get(api_detail_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        if r.status_code == 200:
            msg('DataTable detail: %s' % r.text)
        else:
            self.assertTrue(False\
                   , "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))
            return

        try:
            rjson = r.json()
        except:
            self.assertTrue(False,  "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return

        self.assertTrue('data' in rjson,
                        "'data' key not found in rjson. Found: %s" % rjson)

        f = DataTableResponseForm(rjson['data'])
        self.assertTrue(f.is_valid(), "DataTableResponseForm validation failed: %s" % f.errors)


        # -----------------------------------------------------------
        msgn('(3c) TableJoin Detail')
        # -----------------------------------------------------------
        api_detail_url = self.tablejoin_detail.replace(self.URL_ID_ATTR, str(tablejoin_id))

        self.login_for_cookie()

        r = None
        try:
            r = self.client.get(api_detail_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        if r.status_code == 200:
            msg('TableJoin detail: %s' % r.text)
        else:
            self.assertTrue(False
                   , "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


