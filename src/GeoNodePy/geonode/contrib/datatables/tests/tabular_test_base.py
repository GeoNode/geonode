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

import json
from os.path import realpath, dirname, isfile, join
from requests.exceptions import ConnectionError as RequestsConnectionError
import requests

from django.utils import unittest

from django.core.urlresolvers import reverse
from geonode.contrib.dataverse_connect.forms import ShapefileImportDataForm
from geonode.contrib.msg_util import *

from geonode.contrib.datatables.forms import TableJoinRequestForm,\
                                        TableUploadAndJoinRequestForm,\
                                        DataTableUploadForm,\
                                        DataTableUploadFormLatLng,\
                                        DataTableResponseForm,\
                                        TableJoinResultForm

from geonode.contrib.dataverse_connect.forms import DataverseLayerIndentityForm

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


class TestTabularAPIBase(unittest.TestCase):


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
