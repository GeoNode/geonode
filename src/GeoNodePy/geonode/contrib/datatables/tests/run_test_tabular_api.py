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
"""
import os, sys
if __name__=='__main__':
    sys.path.append('/Users/rmp553/Documents/github-worldmap/cga-worldmap/src/GeoNodePy')
    sys.path.append('/Users/rmp553/Documents/github-worldmap/cga-worldmap/src/GeoNodePy/geonode')
    #from django_conf import settings
    from django.core.management import setup_environ
    os.environ['DJANGO_SETTINGS_MODULE'] = 'geonode.settings'
    #setup_environ(settings)
"""

import json
from os.path import realpath, dirname, isfile, join
from requests.exceptions import ConnectionError as RequestsConnectionError
import requests
from unittest import skip

from django.utils import unittest

from django.core.urlresolvers import reverse
from geonode.contrib.dataverse_connect.forms import ShapefileImportDataForm
from geonode.contrib.msg_util import *

from geonode.contrib.datatables.forms import TableJoinRequestForm,\
                                        TableUploadAndJoinRequestForm,\
                                        DataTableUploadForm,\
                                        DataTableResponseForm

from geonode.contrib.dataverse_connect.forms import DataverseLayerIndentityForm

# need to remove these:
from shared_dataverse_information.worldmap_datatables.forms import TableJoinResultForm
        #TableUploadAndJoinRequestForm
        #DataTableUploadForm
        #DataTableResponseForm,\
from shared_dataverse_information.map_layer_metadata.forms import WorldMapToGeoconnectMapLayerMetadataValidationForm



# --------------------------------------------------
# Load up the Worldmap server url and username
# --------------------------------------------------
GEONODE_CREDS_FNAME = join(dirname(realpath(__file__)), 'server_creds.json')
assert isfile(GEONODE_CREDS_FNAME), 'Server credentials file not found: %s' % GEONODE_CREDS_FNAME
try:
    GEONODE_CREDS_JSON = json.loads(open(GEONODE_CREDS_FNAME, 'r').read())
except:
    raise Exception('Could not parse tabular credentials JSON file: %s' % 'server_creds.json')

GEONODE_SERVER = GEONODE_CREDS_JSON['SERVER_URL']
GEONODE_USERNAME = GEONODE_CREDS_JSON['USERNAME']
GEONODE_PASSWORD = GEONODE_CREDS_JSON['PASSWORD']

def setUpModule():
    """
    Module Set Up placeholder
    """
    pass


def tearDownModule():
    """
    Module tear down placeholder
    """
    pass


class TestWorldMapTabularAPI(unittest.TestCase):


    TEST_FILE_DIR = join(dirname(realpath(__file__)), 'input')
    existing_layer_name = None
    existing_layer_data = None
    layer_attribute_info = None

    URL_ID_ATTR = 'URL_ID'


    @classmethod
    def tearDownClass(cls):
        msg('\n>> tearDownClass')

        cls.delete_ma_tigerlines_shapefile()

    @classmethod
    def setUpClass(cls):
        msg('\n>>> setUpClass')
        # Verify/load MA tigerlines test info
        #
        tab_ma_dataverse_info_fname = join(cls.TEST_FILE_DIR, 'tab_ma_dv_info.json')
        assert isfile(tab_ma_dataverse_info_fname),\
            "MA tigerlines test fixture file not found: %s" % tab_ma_dataverse_info_fname
        cls.tab_ma_dv_info = json.loads(open(tab_ma_dataverse_info_fname, 'r').read())


        # Verify/load shapefile test info
        #
        tab_ma_shp_upload_request_fname = join(cls.TEST_FILE_DIR, 'tab_ma_shp_upload_request.json')
        assert isfile(tab_ma_shp_upload_request_fname), "Shapefile test fixture file not found: %s" % tab_ma_shp_upload_request_fname
        cls.tab_ma_shp_upload_request = json.loads(open(tab_ma_shp_upload_request_fname, 'r').read())

        # Verify that test shapefile exists (good file)
        #
        cls.tab_shp_ma_tigerlines_fname = join(cls.TEST_FILE_DIR, 'tab_shp_ma_tigerlines.zip')
        assert isfile(cls.tab_shp_ma_tigerlines_fname),\
             "Test shapefile not found: %s" % cls.tab_shp_ma_tigerlines_fname

        cls.existing_layer_name = 'boohoo'
        cls.existing_layer_data = 'boohoo existing_layer_data'
        cls.layer_attribute_info = 'boohoo layer_attribute_info'

        cls.upload_ma_tigerlines_shapefile()


    def setUp(self):
        global GEONODE_SERVER, GEONODE_USERNAME, GEONODE_PASSWORD

        self.client = requests.session()
        self.base_url = GEONODE_SERVER

        self.geonode_username = GEONODE_USERNAME
        self.geonode_password = GEONODE_PASSWORD

        # self.login_url =  self.base_url + "/account/login/" # GeoNode

        self.login_url = self.base_url + "/accounts/login/" # WorldMap
        self.csv_upload_url = self.base_url + '/datatables/api/upload'
        # self.shp_layer_upload_url = self.base_url + '/layers/upload'

        self.join_target_url = self.base_url + '/datatables/api/jointargets'
        self.join_datatable_url = self.base_url + '/datatables/api/join'
        self.upload_and_join_datatable_url = self.base_url + '/datatables/api/upload_and_join'
        self.upload_lat_lng_url = self.base_url + '/datatables/api/upload_lat_lon'

        self.datatable_detail = self.base_url + '/datatables/api/%s' % self.URL_ID_ATTR
        self.delete_datatable_url = self.base_url + '/datatables/api/%s/remove' % self.URL_ID_ATTR

        self.tablejoin_detail = self.base_url + '/datatables/api/join/%s' % self.URL_ID_ATTR
        self.delete_tablejoin_url = self.base_url + '/datatables/api/join/%s/remove' % self.URL_ID_ATTR


    def refresh_session(self):
        """
        Start a new requests.session()
        """
        self.client = requests.session()


    def login_for_cookie(self, **kwargs):

        msg('login_for_cookie: %s' % self.login_url)


        # -----------------------------------------
        # Set username
        # -----------------------------------------
        if kwargs.get('custom_username', None) is not None:
            username = kwargs['custom_username']
        else:
            username = self.geonode_username

        # -----------------------------------------
        # Refresh session
        # -----------------------------------------
        if kwargs.get('refresh_session', None) is True:
            self.refresh_session()

        # -----------------------------------------
        # Retrieve the CSRF token first
        # -----------------------------------------
        self.client.get(self.login_url)  # sets the cookie
        csrftoken = self.client.cookies['csrftoken']


        login_data = dict(username=username,
                          password=self.geonode_password,
                          csrfmiddlewaretoken=csrftoken)
        r = self.client.post(self.login_url,
                             data=login_data,
                             headers={"Referer": self.login_url})

        self.assertTrue(r.status_code == 200,
            "Login for cookie failed.  Rcvd status code: %s\nText: %s" % (r.status_code, r.text))


    @classmethod
    def upload_ma_tigerlines_shapefile(cls):
        global GEONODE_SERVER, GEONODE_USERNAME, GEONODE_PASSWORD

        # -----------------------------------------------------------
        msgt("--- SET UP:  Upload MA Tigerlines Shapefile ---")
        # -----------------------------------------------------------
        api_url = GEONODE_SERVER +  reverse('view_add_worldmap_shapefile', kwargs={})


        # -----------------------------------------------------------
        msgn("WorldMap shapefile import API -- with GOOD data/file")
        # -----------------------------------------------------------
        # Get basic shapefile info
        shapefile_import_form = ShapefileImportDataForm(cls.tab_ma_shp_upload_request)
        assert shapefile_import_form.is_valid(), "shapefile_import_form not valid: %s" % shapefile_import_form.errors


        test_shapefile_info = shapefile_import_form.cleaned_data#()

        # add dv info
        test_shapefile_info.update(cls.tab_ma_dv_info)

        # prep file
        files = {'file': open( cls.tab_shp_ma_tigerlines_fname, 'rb')}

        #   Test WorldMap shapefile import API
        #
        msg('api url: %s' % api_url)


        #self.login_for_cookie(username='pubuser')
        """
        client = requests.session()
        login_url = GEONODE_SERVER + "/account/login/"
        client.get(login_url)  # sets the cookie
        csrftoken = client.cookies['csrftoken']
        login_data = dict(username=GEONODE_USERNAME, password=GEONODE_PASSWORD, csrfmiddlewaretoken=csrftoken)
        r = client.post(login_url, data=login_data, headers={"Referer": "test-client"})
         'csrfmiddlewaretoken':csrftoken
        """
        #c = Client()
        #response = c.get('/my-protected-url/', **auth_headers)

        try:
            r = requests.post(api_url,
                              data=test_shapefile_info,
                              files=files,
                              auth=(GEONODE_USERNAME, GEONODE_PASSWORD),
                              )
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except Exception, e:
            msgx("Unexpected error: %s" % e)
            return

        msg(r.status_code)
        msg('%s (truncated) ...' % r.text[:50])

        assert r.status_code == 200,\
            "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text)

        try:
            rjson = r.json()
        except Exception as e:
            assert False,\
                "Failed to convert response text to JSON. \nText: %s\nError: %s" % (r.text, str(e))


        msgn("Get name of newly created layer")

        # Validate returned data
        f = WorldMapToGeoconnectMapLayerMetadataValidationForm(rjson.get('data', {}))
        assert f.is_valid(),\
            'Validation fail. WorldMapToGeoconnectMapLayerMetadataValidationForm Errors: %s' % f.errors

        # Retrieve layer_name
        cls.existing_layer_data = rjson.get('data', {})
        cls.existing_layer_name = cls.existing_layer_data.get('layer_name', None)
        cls.layer_attribute_info = json.loads(cls.existing_layer_data.get('attribute_info', None))

        print 'cls.layer_attribute_info', cls.layer_attribute_info, cls.layer_attribute_info.__class__.__name__


        # Make sure layer_name is valid
        assert cls.existing_layer_name is not None, 'self.existing_layer_name cannot be None'
        assert len(cls.existing_layer_name) > 0, 'self.existing_layer_name cannot be length 0'


    @classmethod
    def delete_ma_tigerlines_shapefile(cls):
        global GEONODE_SERVER, GEONODE_USERNAME, GEONODE_PASSWORD

        # -----------------------------------------------------------
        msgt("--- TEAR DOWN: Delete MA Tigerlines Shapefile ---")
        # -----------------------------------------------------------

        api_prep_form = DataverseLayerIndentityForm(cls.tab_ma_dv_info)
        assert api_prep_form.is_valid()\
           , "Error.  Validation failed. (DataverseLayerIndentityForm):\n%s"\
             % api_prep_form.errors

        data_params = api_prep_form.cleaned_data
        #data_params = api_prep_form.get_api_params_with_signature()

        delete_api_url = GEONODE_SERVER + reverse('view_delete_dataverse_map_layer', kwargs={})

        print 'delete_api_url', delete_api_url

        try:
            r = requests.post(delete_api_url,
                              data=data_params,
                              auth=(GEONODE_USERNAME, GEONODE_PASSWORD),
                              )
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])
            return

        print 'status_code', r.status_code
        print 'text', r.text

        assert r.status_code == 200,\
            "Expected status code 200 but received '%s'" % r.status_code
        msg('Layer deleted: %s\n%s' % (r.status_code, r.text))



    #@skip('test_get_join_targets')
    def test_get_join_targets(self):
        """
        Return the JoinTargets.

        Expect a 200 response, may be empty list or whatever is in db, so don't check exact content

        :return:
        """
        msgn('test_get_join_targets')

        self.login_for_cookie()

        try:
            r = self.client.get(self.join_target_url)
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
            r = self.client.get(self.join_target_url + '/?start_year=1982&end_year=1967')
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

        self.login_for_cookie()

        r = None
        try:
            r = self.client.get(api_detail_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg(r.text)
        msg(r.status_code)
        self.assertTrue(r.status_code == 200,
                "Expected status code of 200.  Received: %s\n%s" % (r.status_code, r.text))

        rjson = r.json()

        self.assertTrue('data' in rjson,
                        "'data' key not found in rjson. Found: %s" % rjson)

        f = DataTableResponseForm(rjson['data'])

        self.assertTrue(f.is_valid(), "DataTableResponseForm validation failed: %s" % f.errors)



    def is_attribute_in_ma_layer(self, attr_name):
        if attr_name is None:
            return False

        print 'layer_attribute_info.__class__.__name__', self.layer_attribute_info.__class__.__name__
        print 'layer_attribute_info.__class__.__name__', self.layer_attribute_info
        for attr_dict in self.layer_attribute_info:
            print attr_dict, attr_dict.__class__
            if attr_dict.get('name', None) == attr_name:
                return True
        return False


    def get_join_datatable_params(self, **kwargs):

        params = dict(title='Boston Income',
                      abstract='(abstract)',
                      table_attribute='tract',

                      layer_name=self.existing_layer_name,
                      layer_attribute='TRACTCE',

                      delimiter=',',
                      no_header_row=False,
                      new_table_owner=None)

        for key in TableUploadAndJoinRequestForm().fields.keys():
            if kwargs.get(key, None) is not None:
                params[key] = kwargs[key]

        return params


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
        self.login_for_cookie()

        try:
            r = self.client.post(self.upload_and_join_datatable_url, data=params)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except Exception as e:
            msgx("Unexpected error: %s" % str(e))

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

        self.login_for_cookie()

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url,
                                    data=params,
                                    files=files)
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

        self.login_for_cookie()

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url,
                                    data=params,
                                    files=files)
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

        self.login_for_cookie()

        try:
            r = self.client.get(api_tj_detail_url)
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

        self.login_for_cookie()

        try:
            r = self.client.get(api_del_tablejoin_url)
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
        self.login_for_cookie()

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url\
                                        , data=params\
                                        , files=files\
                                    )
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

        self.login_for_cookie()

        r = None
        try:
            r = self.client.get(api_detail_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

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

        self.login_for_cookie()

        r = None
        try:
            r = self.client.get(api_detail_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

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

        self.login_for_cookie(**dict(custom_username='user-456-doesnt-exist', refresh_session=True))

        try:
            r = self.client.get(api_del_tablejoin_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg('status_code: %s' % r.status_code)

        self.assertTrue(r.status_code == 200,
                "Expected status code 200, not: %s\nError: %s" % (r.status_code, r.text))

        self.assertTrue(r.text.find('<form method="post" action="/accounts/login/">') > -1,
                 "Expected to be redirected to login page")


        # -----------------------------------------------------------
        msgn('(2e) TableJoin Delete (Fail: User w/o perms)')
        # -----------------------------------------------------------
        api_del_tablejoin_url = self.delete_tablejoin_url.replace(self.URL_ID_ATTR, str(tablejoin_id))
        msg('api_del_tablejoin_url: %s' % api_del_tablejoin_url)

        self.login_for_cookie(**dict(custom_username='pubuser', refresh_session=True))

        try:
            r = self.client.get(api_del_tablejoin_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        msg('status_code: %s' % r.status_code)

        self.assertTrue(r.status_code==401,
            "Expected status code 401, not: %s.  MAKE SURE YOU HAVE A 'pubuser' WITHOUT DELETE PERMISSIONS.\nError: %s" %
            (r.status_code, r.text))

        try:
            rjson = r.json()
        except:
            self.assertTrue(False, "Failed to convert response to JSON: %s" % r.text)

        expected_msg = "not permitted to delete this TableJoin object"
        self.assertTrue(r.text.find(expected_msg) > -1
            , "Expected message not found: '%s'\nActual response: %s" % (expected_msg, r.text))

        # -----------------------------------------------------------
        msgn('(2g) TableJoin Delete -- also deletes TableJoin')
        # -----------------------------------------------------------

        api_del_tablejoin_url = self.delete_tablejoin_url.replace(self.URL_ID_ATTR, str(tablejoin_id))
        msg('api_del_tablejoin_url: %s' % api_del_tablejoin_url)

        self.login_for_cookie(**dict(refresh_session=True))

        try:
            r = self.client.get(api_del_tablejoin_url)
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





    @skip('skipping test_03_upload_join_boston_income')
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
        self.login_for_cookie()

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        try:
            r = self.client.post(self.upload_and_join_datatable_url,
                                    data=params,
                                    files=files)
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


       # -----------------------------------------------------------
        msgn('(3d) Delete DataTable with Bad ID')
        # -----------------------------------------------------------
        bad_table_id = 4239458
        api_del_url = self.delete_datatable_url.replace(self.URL_ID_ATTR, str(bad_table_id))
        msg('api_del_url: %s' % api_del_url)

        self.login_for_cookie()
        r = None
        try:
            r = self.client.get(api_del_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])


        self.assertTrue(r.status_code == 404
                        , "Should receive 404 message.  Received: %s\n%s" % (r.status_code, r.text))



        # -----------------------------------------------------------
        msgn('(3e) Delete DataTable with Bad Username')
        # -----------------------------------------------------------
        api_del_url = self.delete_datatable_url.replace(self.URL_ID_ATTR, str(table_id))
        msg('api_del_url: %s' % api_del_url)

        #self.login_for_cookie(username='pubuser')
        #self.login_for_cookie(**dict(custom_username='pubuser', refresh_session=True))
        self.login_for_cookie(custom_username='pubuser', refresh_session=True)

        try:
            r = self.client.get(api_del_url)
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

        expected_msg = "You are not permitted to delete this DataTable object"
        self.assertTrue(r.text.find(expected_msg) > -1
            , "Expected message not found: '%s'\nActual response: %s" % (expected_msg, r.text))



        # -----------------------------------------------------------
        msgn('(3f) Delete DataTable')
        # -----------------------------------------------------------
        api_del_url = self.delete_datatable_url.replace(self.URL_ID_ATTR, str(table_id))
        msg('api_del_url: %s' % api_del_url)

        self.login_for_cookie()
        r = None
        try:
            r = self.client.get(api_del_url)
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message); return
        except:
            msgx("Unexpected error: %s" % sys.exc_info()[0])

        #msg(r.status_code)
        #msg(r.text)

        self.assertTrue(r.status_code == 200
                        , "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))

        if r.status_code == 200:
            msg('DataTable deleted: %s' % r.text)
        else:
            self.assertTrue(False\
                   , "Should receive 200 message.  Received: %s\n%s" % (r.status_code, r.text))


    @skip("skipping")
    def test_it2(self):
        msgt('------------ TEST IT 2------------')
        msg('Still got it? existing_layer_name: %s' % self.existing_layer_name)
        msg('Still got it? ex*isting_layer_data: %s (truncated) ...' % str(self.existing_layer_data)[:100])


#if __name__=='__main__':
#    print dir(TestWorldMapTabularAPI)
#    TestWorldMapTabularAPI.run(TestWorldMapTabularAPI())
    #print 'hi'
    #TestCase.main()