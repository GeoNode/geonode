"""
Run tests for the WorldMap Tabular API

python manage.py test datatables.TestWorldMapTabularAPI --settings=geonode.no_db_settings

What these tests do:
    (Note: Setup takes several seconds)

    Setup at the ~class~ level: Uploads a shapefile to use as an existing Layer

        Test:
        - Try JoinTarget API with good and bad params
        - Try the Upload and Join API with bad params
            test_01a_fail_upload_join_with_no_file
            test_01b_fail_upload_join_with_blank_title
            test_01c_fail_upload_join_with_blank_abstract
        - Use the Upload and Join API with good params
        - Try to retrieve details and delete TableJoin object with bad params
            test_04_non_existent_tablejoin

    Teardown at the ~class~ level: Deletes the shapefile used as an existing Layer

"""
from os.path import realpath, dirname, isfile, join
from requests.exceptions import ConnectionError as RequestsConnectionError

from unittest import skip
from geonode.contrib.msg_util import *

from geonode.contrib.datatables.forms import DataTableResponseForm,\
                                        TableJoinResultForm

from tabular_test_base import TestTabularAPIBase


class TestWorldMapTabularAPI(TestTabularAPIBase):


    #@skip('test_get_join_targets')
    def test_get_join_targets(self):
        """
        Return the JoinTargets.

        Expect a 200 response, may be empty list or whatever is in db, so don't check exact content

        :return:
        """
        msgn('test_get_join_targets')

        try:
            r = self.client.get(self.join_target_url, auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        #msg(r.text)
        #msg(r.status_code)
        self.assertTrue(r.status_code == 200,
                "Expected status code of 200.  Received: %s\n%s" % (r.status_code, r.text))

        rjson = r.json()
        self.assertTrue('success' in rjson,
                        "'success' key not found in rjson. Found: %s" % rjson)
        self.assertTrue(rjson.get('success') is True,
                        "rjson.get('success') was not True, instead was: %s" % rjson.get('success'))
        self.assertTrue('data' in rjson,
                        "'data' key not found in rjson. Found: %s" % rjson)

        # ------------------------------
        # Bad info...end_year before start_year
        # ------------------------------
        try:
            r = self.client.get(self.join_target_url + '/?start_year=1982&end_year=1967',
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        #msg(r.text)
        #msg(r.status_code)
        rjson = r.json()
        self.assertTrue(r.status_code == 400,
                "Expected status code of 400.  Received: %s\n%s" % (r.status_code, r.text))

        self.assertTrue('success' in rjson,
                        "'success' key not found in rjson. Found: %s" % rjson)
        self.assertTrue(rjson.get('success') is False,
                        "rjson.get('success') was not False, instead was: %s" % rjson.get('success'))

    @skip('(not a real test) test_grab_detail')
    def test_grab_detail(self):
        msgn('(not a real test) test_grab_detail')
        """
        Working on changing datatable detail response
        """
        table_id = 39
        api_detail_url = self.datatable_detail.replace(self.URL_ID_ATTR, str(table_id))

        try:
            r = self.client.get(api_detail_url, auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        msg(r.text)
        msg(r.status_code)
        self.assertTrue(r.status_code == 200,
                "Expected status code of 200.  Received: %s\n%s" % (r.status_code, r.text))

        rjson = r.json()

        self.assertTrue('data' in rjson,
                        "'data' key not found in rjson. Found: %s" % rjson)

        f = DataTableResponseForm(rjson['data'])

        self.assertTrue(f.is_valid(), "DataTableResponseForm validation failed: %s" % f.errors)



    #@skip('skipping test_01a_fail_upload_join_with_no_file')
    def test_01a_fail_upload_join_with_no_file(self):

        msgt('(1) test_01_datatable_fail_tests')

        # --------------------------------
        # Initial test params
        # --------------------------------
        fname_to_upload = join(self.TEST_FILE_DIR, 'boston-income.csv')
        assert isfile(fname_to_upload), "File not found: %s" % fname_to_upload

        params = self.get_join_datatable_params()


        # -----------------------------------------------------------
        msgn('(1a) Fail with no file')
        # -----------------------------------------------------------

        try:
            r = self.client.post(self.upload_and_join_datatable_url,
                                 data=params,
                                 auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except Exception as e:
            msgx("Unexpected error: %s" % str(e)); return

        msgn(r.status_code)
        msgn(r.text)

        self.assertTrue(r.status_code == 400,
                "Status code should be 400.  Found: %s" % r.status_code)

        try:
            rjson = r.json()
        except:
            self.assertTrue(False,  "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return


        self.assertTrue('success' in rjson,
                "JSON 'success' attribute not found in JSON result: %s" % rjson)

        self.assertTrue(rjson.get('success', None) is False,
                "JSON 'success' attribute should be 'false'. Found: %s" % rjson)

        self.assertTrue('data' in rjson,
                "JSON 'data' attribute not found in JSON result: %s" % rjson)

        self.assertTrue('uploaded_file' in rjson.get('data', {}),
                "JSON 'data' attribute have an 'uploaded_file' key. Found: %s" % rjson)

        self.assertTrue(r.text.find('This field is required.') > -1,
                "Response text should have error of 'This field is required.'  Found: %s" % rjson)


    #@skip('skipping test_01b_fail_upload_join_with_blank_title')
    def test_01b_fail_upload_join_with_blank_title(self):
        # -----------------------------------------------------------
        msgn('(1b) Fail with blank title')
        # -----------------------------------------------------------
        fname_to_upload = join(self.TEST_FILE_DIR, 'boston-income.csv')
        assert isfile(fname_to_upload), "File not found: %s" % fname_to_upload

        params = self.get_join_datatable_params(title='')

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url,
                                 data=params,
                                 files=files,
                                 auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])


        msg(r.text)
        msg(r.status_code)

        self.assertTrue(r.status_code == 400, "Status code should be 400.  Found: %s" % r.status_code)


        try:
            rjson = r.json()
        except:
            self.assertTrue(False,  "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return

        msg(r.text)
        msg(r.status_code)
        self.assertTrue('success' in rjson,
                "JSON 'success' attribute not found in JSON result: %s" % rjson)

        self.assertTrue(rjson.get('success', None) is False,
                "JSON 'success' attribute should be 'false'. Found: %s" % rjson)

        self.assertTrue(rjson.has_key('data'),
                "JSON 'data' attribute not found in JSON result: %s" % rjson)

        self.assertTrue(rjson.get('data', {}).has_key('title')\
                        , "JSON 'data' attribute have an 'file' key. Found: %s" % rjson)

        self.assertTrue(r.text.find('This field is required.') > -1\
                        , "Response text should have error of 'This field is required.'  Found: %s" % rjson)

    #@skip('skipping test_01c_fail_upload_join_with_blank_abstract')
    def test_01c_fail_upload_join_with_blank_abstract(self):
        # -----------------------------------------------------------
        msgn('(1c) Fail with blank title')
        # -----------------------------------------------------------
        fname_to_upload = join(self.TEST_FILE_DIR, 'boston-income.csv')
        assert isfile(fname_to_upload), "File not found: %s" % fname_to_upload

        params = self.get_join_datatable_params(abstract='')

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url,
                                data=params,
                                files=files,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])


        msg(r.text)
        msg(r.status_code)

        self.assertTrue(r.status_code == 400, "Status code should be 400.  Found: %s" % r.status_code)


        try:
            rjson = r.json()
        except:
            self.assertTrue(False,  "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return

        msg(r.text)
        msg(r.status_code)
        self.assertTrue('success' in rjson,
                "JSON 'success' attribute not found in JSON result: %s" % rjson)

        self.assertTrue(rjson.get('success', None) is False,
                "JSON 'success' attribute should be 'false'. Found: %s" % rjson)

        self.assertTrue(rjson.has_key('data'),
                "JSON 'data' attribute not found in JSON result: %s" % rjson)

        self.assertTrue(rjson.get('data', {}).has_key('abstract')\
                        , "JSON 'data' attribute have an 'file' key. Found: %s" % rjson)

        self.assertTrue(r.text.find('This field is required.') > -1\
                        , "Response text should have error of 'This field is required.'  Found: %s" % rjson)


    #@skip('test_04_non_existent_tablejoin')
    def test_04_non_existent_tablejoin(self):

        # -----------------------------------------------------------
        msgn("(4) TableJoin - try to see details and delete with bad id")
        # -----------------------------------------------------------
        table_join_id = 8723552 # test will fail if this id exists

        # -----------------------------------------------------------
        msgn("(4a) Try to view with bad id")
        # -----------------------------------------------------------
        api_tj_detail_url = self.tablejoin_detail.replace(self.URL_ID_ATTR, str(table_join_id))
        msg('api_tj_detail_url: %s' % api_tj_detail_url)

        try:
            r = self.client.get(api_tj_detail_url,
                                auth=self.get_creds_for_http_basic_auth())

        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg(r.text)
        msg('status_code: %s' % r.status_code)


        if r.status_code == 404:
            msg('(success) TableJoin id not found')
        else:
            self.assertTrue(False,
                "Should receive 404 message.  Received: %s\n%s" % (r.status_code, r.text))

        # -----------------------------------------------------------
        msgn("(4b) Try to delete with bad id")
        # -----------------------------------------------------------
        api_del_tablejoin_url = self.delete_tablejoin_url.replace(self.URL_ID_ATTR, str(table_join_id))
        msg('api_del_tablejoin_url: %s' % api_del_tablejoin_url)

        try:
            r = self.client.get(api_del_tablejoin_url,
                               auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg(r.text)
        msg('status_code: %s' % r.status_code)


        if r.status_code == 404:
            msg('(success) TableJoin id not found')
        else:
            self.assertTrue(False\
                   , "Should receive 404 message.  Received: %s\n%s" % (r.status_code, r.text))


    #@skip('skipping test_02_upload_join_boston_income')
    def test_02_upload_join_boston_income(self):

        msgt('(2) Good Upload and Join - Delete TableJoin (test_02_upload_join_boston_income)')

        fname_to_upload = join(self.TEST_FILE_DIR, 'boston-income.csv')
        assert isfile(fname_to_upload), "File not found: %s" % fname_to_upload

        layer_attribute_name = 'TRACTCE'
        self.assertTrue(self.is_attribute_in_ma_layer(layer_attribute_name)\
                    , "Attribute '%s' not found in layer '%s'" % (layer_attribute_name, self.existing_layer_name))

        params = self.get_join_datatable_params()


        # -----------------------------------------------------------
        msgn('(2a) Upload table and join layer')
        # -----------------------------------------------------------
        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url
                                        , data=params
                                        , files=files,
                                        auth=self.get_creds_for_http_basic_auth())

        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        msg(r.status_code)
        msg('r.text: %s' % r.text)

        if r.status_code == 200:
            msg('DataTable uploaded and joined!')
        else:
            self.assertTrue(False,
                "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


        try:
            rjson = r.json()
        except:
            self.assertTrue(False,  "Failed to convert response text to JSON. Text:\n%s" % r.text)
            return

        msg(rjson)

        f = TableJoinResultForm(rjson)
        self.assertTrue(f.is_valid(), "Validation failed with TableJoinResultForm: %s" % f.errors)


        # -----------------------------------------------------------
        # Pull out table_id and tablejoin_id
        #   for detail and delete tests
        # -----------------------------------------------------------
        table_id = f.cleaned_data.get('table_id', None)
        self.assertTrue(table_id is not None,
                "table_id should not be None. cleaned form data: %s" % f.cleaned_data)

        tablejoin_id = f.cleaned_data.get('tablejoin_id', None)
        self.assertTrue(tablejoin_id is not None,
                "tablejoin_id should not be None. cleaned form data: %s" % f.cleaned_data)


        # -----------------------------------------------------------
        msgn('(2b) DataTable Detail')
        # -----------------------------------------------------------
        api_detail_url = self.datatable_detail.replace(self.URL_ID_ATTR, str(table_id))

        try:
            r = self.client.get(api_detail_url, auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        self.assertTrue(r.status_code == 200,
                "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))

        if r.status_code == 200:
            msg('DataTable detail: %s' % r.text)
        else:
            self.assertTrue(False,
                "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


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
        msgn('(2c) TableJoin Detail')
        # -----------------------------------------------------------
        api_detail_url = self.tablejoin_detail.replace(self.URL_ID_ATTR, str(tablejoin_id))

        try:
            r = self.client.get(api_detail_url,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        self.assertTrue(r.status_code == 200,
                "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))

        if r.status_code == 200:
            msg('TableJoin detail: %s' % r.text)
        else:
            self.assertTrue(False,
                "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


       # -----------------------------------------------------------
        msgn('(2d) TableJoin Delete (Fail: nonexistent username)')
        # -----------------------------------------------------------

        api_del_tablejoin_url = self.delete_tablejoin_url.replace(self.URL_ID_ATTR, str(tablejoin_id))
        msg('api_del_tablejoin_url: %s' % api_del_tablejoin_url)

        try:
            r = self.client.get(api_del_tablejoin_url,
                                auth=self.get_creds_for_http_basic_auth(custom_username='user-456-doesnt-exist')
                                )
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg('status_code: %s' % r.status_code)

        self.assertTrue(r.status_code == 401,
                "Expected status code 401, not: %s\nError: %s" % (r.status_code, r.text))

        try:
            rjson = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON: %s" % r.text)


        self.assertTrue('success' in rjson,
                 "Expected to find 'success' key in JSON response: %s" % r.text)

        self.assertTrue(rjson['success'] == False,
                 "Expected to find 'success' with value of 'false' in JSON response: %s" % r.text)

        self.assertTrue('message' in rjson,
                 "Expected to find 'message' key in JSON response: %s" % r.text)


        # -----------------------------------------------------------
        msgn('(2e) TableJoin Delete (Fail: User w/o perms)')
        # -----------------------------------------------------------
        api_del_tablejoin_url = self.delete_tablejoin_url.replace(self.URL_ID_ATTR, str(tablejoin_id))
        msg('api_del_tablejoin_url: %s' % api_del_tablejoin_url)


        try:
            r = self.client.get(api_del_tablejoin_url,
                                auth=self.get_creds_for_http_basic_auth(custom_username='pubuser'))
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        msg('status_code: %s' % r.status_code)

        self.assertTrue(r.status_code==401,
            "Expected status code 401, not: %s.  MAKE SURE YOU HAVE A 'pubuser' WITHOUT DELETE PERMISSIONS.\nError: %s" %
            (r.status_code, r.text))

        # -----------------------------------------------------------
        msgn('(2g) TableJoin Delete -- also deletes TableJoin')
        # -----------------------------------------------------------

        api_del_tablejoin_url = self.delete_tablejoin_url.replace(self.URL_ID_ATTR, str(tablejoin_id))
        msg('api_del_tablejoin_url: %s' % api_del_tablejoin_url)

        try:
            r = self.client.get(api_del_tablejoin_url,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg(r.text)
        msg('status_code: %s' % r.status_code)

        if r.status_code == 200:
            msg('TableJoin deleted: %s' % r.text)
        else:
            self.assertTrue(False,
                    "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))





    #@skip('skipping test_03_upload_join_boston_income')
    def test_03_upload_join_boston_income(self):
        """
        Upload DataTable, Join it to a Layer, and Delete it

        """
        msgt('(3) Good Upload and Join - Delete DataTable (test_03_upload_join_boston_income)')

        fname_to_upload = join(self.TEST_FILE_DIR, 'boston-income.csv')
        assert isfile(fname_to_upload), "File not found: %s" % fname_to_upload

        layer_attribute_name = 'TRACTCE'
        self.assertTrue(self.is_attribute_in_ma_layer(layer_attribute_name),
                        "Attribute '%s' not found in layer '%s'"
                          % (layer_attribute_name, self.existing_layer_name))

        params = self.get_join_datatable_params()


        # -----------------------------------------------------------
        msgn('(3a) Upload table and join layer')
        # -----------------------------------------------------------
        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url,
                                    data=params,
                                    files=files,
                                    auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg(r.status_code)
        #msg(r.text)

        if r.status_code == 200:
            msg('DataTable uploaded and joined!')
        else:
            self.assertTrue(False,
                    "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))

        try:
            rjson = r.json()
        except:
            self.assertTrue(False,
                    "Failed to convert response text to JSON. Text:\n%s" % r.text)

        msg(rjson)

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

        try:
            r = self.client.get(api_detail_url,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        self.assertTrue(r.status_code == 200,
                    "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))
        msg('DataTable detail: %s' % r.text)

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

        try:
            r = self.client.get(api_detail_url,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return

        self.assertTrue(r.status_code == 200,
                   "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))
        msg('TableJoin detail: %s' % r.text)


       # -----------------------------------------------------------
        msgn('(3d) Delete DataTable with Bad ID')
        # -----------------------------------------------------------
        bad_table_id = 4239458
        api_del_url = self.delete_datatable_url.replace(self.URL_ID_ATTR, str(bad_table_id))
        msg('api_del_url: %s' % api_del_url)

        try:
            r = self.client.get(api_del_url,
                                auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0]); return


        self.assertTrue(r.status_code == 404
                        , "Should receive 404 message.  Received: %s\n%s" % (r.status_code, r.text))



        # -----------------------------------------------------------
        msgn('(3e) Delete DataTable with Bad Username')
        # -----------------------------------------------------------
        api_del_url = self.delete_datatable_url.replace(self.URL_ID_ATTR, str(table_id))
        msg('api_del_url: %s' % api_del_url)

        try:
            r = self.client.get(api_del_url,
                                auth=self.get_creds_for_http_basic_auth(custom_username='pubuser'))

        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        self.assertTrue(r.status_code==401,
            "Expected status code 401, not: %s. MAKE SURE YOU HAVE A 'pubuser' WITHOUT DELETE PERMISSIONS.\nError: %s" % (r.status_code, r.text))

        msg(r.text)
        msg(r.status_code)

        try:
            rjson = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON: %s" % r.text)

        expected_msg = "Login failed"
        other_expected_msg = "You are not permitted to delete this DataTable object"
        self.assertTrue(r.text.find(expected_msg) > -1 or r.text.find(other_expected_msg) > -1
            , "Expected message not found: '%s'\nActual response: %s" % (expected_msg, r.text))



        # -----------------------------------------------------------
        msgn('(3f) Delete DataTable')
        # -----------------------------------------------------------
        api_del_url = self.delete_datatable_url.replace(self.URL_ID_ATTR, str(table_id))
        msg('api_del_url: %s' % api_del_url)

        try:
            r = self.client.get(api_del_url, auth=self.get_creds_for_http_basic_auth())
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        #msg(r.status_code)
        #msg(r.text)

        self.assertTrue(r.status_code == 200
                        , "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))

        msg('DataTable deleted: %s' % r.text)
