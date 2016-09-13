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
from django.conf import settings
from django.contrib.auth.models import Group, User

from django.core.urlresolvers import reverse

from geonode.contrib.msg_util import *

from geonode.contrib.datatables.forms import TableJoinRequestForm,\
                                        TableUploadAndJoinRequestForm,\
                                        DataTableUploadForm,\
                                        DataTableUploadFormLatLng,\
                                        DataTableResponseForm,\
                                        TableJoinResultForm

from geonode.contrib.dataverse_connect.forms import DataverseLayerIndentityForm

#from geonode.contrib.dataverse_connect.forms import ShapefileImportDataForm
from shared_dataverse_information.shapefile_import.forms import ShapefileImportDataForm
from shared_dataverse_information.map_layer_metadata.forms import WorldMapToGeoconnectMapLayerMetadataValidationForm



# --------------------------------------------------
# Load up the Worldmap server url and username
# --------------------------------------------------
GEONODE_CREDS_FNAME = join(dirname(realpath(__file__)), 'server_credentials.json')
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

    URL_ID_ATTR = '987654310'


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

        # For table joins, the user must be in the Dataverse group
        # so that the target layer goes to the correct table
        cls.createDataverseUserAndGroup(add_user_to_dv_group=True)

        cls.upload_ma_tigerlines_shapefile()


    @classmethod
    def createDataverseUserAndGroup(cls, add_user_to_dv_group=True):
        """
        Make sure there is a Dataverse Group.
        If appropriate add the test user to this group.
        Note: For tablejoins, the user must be part of this group


        DATAVERSE_GROUP_NAME -> specified in settings.DATAVERSE_GROUP_NAME

        username for test -> specified in server_credentials.json*
            (* See datatables/tests/__init__.py for info on making this file)

        """
        cls.dv_group, group_created = Group.objects.get_or_create(name=settings.DATAVERSE_GROUP_NAME)
        cls.dv_user, user_created = User.objects.get_or_create(username=GEONODE_USERNAME)

        if add_user_to_dv_group:
            cls.dv_group.user_set.add(cls.dv_user)
            cls.dv_group.save()
        else:
            cls.dv_group.user_set.remove(cls.dv_user)
            cls.dv_group.save()

        print '-' * 40
        print 'added to group?', cls.dv_group.user_set.all()

    @classmethod
    def removeDataverseGroupAndUser(cls):
        """
        For local tests, this should be used.

        Commented out b/c we're testing on a remote server right now
        """
        if cls.dv_user and cls.dv_group:
            cls.dv_group.user_set.remove(cls.dv_user)
            cls.dv_group.save()

        """
        # Delete the user
        if User.objects.filter(username=GEONODE_USERNAME).count() > 0:
            User.objects.filter(username=GEONODE_USERNAME).delete()

        # Delete the group
        if Group.objects.filter(name=settings.DATAVERSE_GROUP_NAME).count() > 0:
            Group.objects.filter(name=settings.DATAVERSE_GROUP_NAME).delete()
        """

    def setUp(self):
        global GEONODE_SERVER, GEONODE_USERNAME, GEONODE_PASSWORD

        self.client = requests.session()
        self.base_url = GEONODE_SERVER

        self.geonode_username = GEONODE_USERNAME
        self.geonode_password = GEONODE_PASSWORD

        self.login_url = self.base_url + "/accounts/login/" # WorldMap
        self.csv_upload_url = self.base_url +  reverse('datatable_upload_api', kwargs={})

        self.join_target_url = self.base_url + reverse('jointargets', kwargs={}) #'/datatables/api/jointargets'
        self.join_datatable_url = self.base_url + reverse('tablejoin_api', kwargs={}) #
        self.upload_and_join_datatable_url = self.base_url +  reverse('datatable_upload_and_join_api', kwargs={})
        self.upload_lat_lng_url = self.base_url + reverse('datatable_upload_lat_lon_api', kwargs={})

        self.dataverse_map_layer_detail = self.base_url + reverse('get_existing_layer_data',
                    kwargs={} )

        self.datatable_detail = self.base_url + reverse('datatable_detail',
                    kwargs={'dt_id':self.URL_ID_ATTR} )

        self.delete_datatable_url = self.base_url + reverse('datatable_remove',
                    kwargs={'dt_id':self.URL_ID_ATTR} )

        self.tablejoin_detail = self.base_url + reverse('tablejoin_detail',
                    kwargs={'tj_id':self.URL_ID_ATTR} )

        self.delete_tablejoin_url = self.base_url + reverse('tablejoin_remove',
                    kwargs={'tj_id':self.URL_ID_ATTR} )

        self.delete_datatable_lat_lon_url = self.base_url + reverse('datatable_lat_lon_remove',
                    kwargs={'dt_id':self.URL_ID_ATTR} )

        self.dataverse_upload_and_join_datatable_url = self.base_url + reverse('view_upload_table_and_join_layer', kwargs={})

        self.delete_dataverse_layer_url = self.base_url + reverse('view_delete_dataverse_map_layer', kwargs={})

        self.add_shapefile_url = self.base_url + reverse('view_add_worldmap_shapefile', kwargs={})

        self.add_geotiff_url = self.base_url + reverse('view_add_worldmap_geotiff', kwargs={})

        #ADD_SHAPEFILE_API_PATH, DELETE_LAYER_API_PATH

    def refresh_session(self):
        """
        Start a new requests.session()
        """
        self.client = requests.session()


    def get_creds_for_http_basic_auth(self, custom_username=None):
        if custom_username is not None:
            username = custom_username
        else:
            username = self.geonode_username

        return (username, self.geonode_password)
        #return dict(username=username,
        #          password=self.geonode_password)


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
        #test_shapefile_info.update(dict(username=GEONODE_USERNAME, password=GEONODE_PASSWORD))

        # prep file
        files = {'file': open( cls.tab_shp_ma_tigerlines_fname, 'rb')}

        #   Test WorldMap shapefile import API
        #
        msg('api url: %s' % api_url)


        try:
            r = requests.post(api_url,
                              data=test_shapefile_info,
                              files=files,
                              auth=(GEONODE_USERNAME, GEONODE_PASSWORD)
                              )
        except RequestsConnectionError as e:
            msgx('Connection error: %s' % e.message)
            return
        except Exception, e:
            msgx("Unexpected error: %s" % e)
            return

        msg(r.status_code)
        msg('%s (truncated) ...' % r.text[:50])
        msg(r.text)
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

    """
    def get_join_table_params_temp(self, **kwargs):
        params = dict(title='CGB Annual Measures',
                      abstract='(abstract)',
                      table_attribute='BG_ID_10',

                      layer_name='geonode:ma_census_2010_kyv Layer',
                      layer_attribute='GEOID10',

                      delimiter='\t',
                      no_header_row=False,
                      new_table_owner=None)
        return params
    """

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
