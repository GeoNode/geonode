"""
For developing tabular api
"""
import os
from os.path import join
import sys
import json
import requests
import glob
from msg_util import *

INPUT_DIR = '/Users/ortelius/projects/geonode-dev/geonode/scratch/boston/Tracts'

class TabularTest:
    
    def __init__(self, base_url="http://localhost:8000"):
        self.client = requests.session()
        self.base_url = base_url
        self.login_url =  self.base_url + "/account/login/"
        self.csv_upload_url  = self.base_url + '/datatables/api/upload'
        self.upload_and_join_url = self.base_url + '/datatables/api/upload_and_join'
        self.upload_lat_lon_url = self.base_url + '/datatables/api/upload_lat_lon'
        self.shp_layer_upload_url = self.base_url + '/layers/upload'
        self.join_datatable_url = self.base_url + '/datatables/api/join'
        
        #self.datatable_name = None
        
    def login_for_cookie(self):

        msgt('login_for_cookie: %s' % self.login_url)

        # Retrieve the CSRF token first
        resp = self.client.get(self.login_url)  # sets the cookie
        print resp
        csrftoken = self.client.cookies['csrftoken']

        login_data = dict(username="admin", password="admin", csrfmiddlewaretoken=csrftoken)
        r = self.client.post(self.login_url, data=login_data, headers={"Referer": "test-client"})

        print r.status_code

        
    def upload_csv_file(self, title, fname_to_upload, delimiter_type='COMMA', no_header_row=False):

        msgt('upload_csv_file: %s' % self.csv_upload_url)

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        response = self.client.post(self.csv_upload_url\
                    , data={'title' : title
                    , 'delimiter_type':delimiter_type
                    , 'no_header_row':no_header_row}\
                    , files=files)

        if response.status_code == 200:
            try:
                resp_dict = json.loads(response.content)
                datatable_name = resp_dict['datatable_name']
                return datatable_name
            except:
                print sys.exc_info()[0]
                return None 
        else:
            print response.content
            resp_dict = json.loads(response.content)
            print "Server Error: " + resp_dict['msg']
            return None

    def upload_and_join(self, fname_to_upload, join_props):
        msgt('upload_and_join: %s' % self.upload_and_join_url)

        files = {'uploaded_file': open(fname_to_upload,'rb')}

        response = self.client.post(self.upload_and_join_url\
                    , data=join_props
                    , files=files)

        print response.content
        if response.status_code == 200:
            try:
                resp_dict = json.loads(response.content)
                datatable = resp_dict['datatable']
                join_layer = resp_dict['join_layer']
                return datatable, join_layer
            except:
                print sys.exc_info()[0]
                return None
        else:
            resp_dict = json.loads(response.content)
            print "Server Error: " + resp_dict['msg']
            return None

    def add_shapefile_layer(self, shp_dirname, shp_fname_prefix):

        msgt('add_shapefile_layer: %s' % self.shp_layer_upload_url)

        files = {
            'base_file': open(join(shp_dirname, '%s.shp' % shp_fname_prefix), 'rb'),
            'dbf_file': open(join(shp_dirname, '%s.dbf' % shp_fname_prefix), 'rb'),
            'prj_file': open(join(shp_dirname, '%s.prj' % shp_fname_prefix), 'rb'),
            'shx_file': open(join(shp_dirname, '%s.shx' % shp_fname_prefix), 'rb'),
            }

        # Retrieve the CSRF token first
        #self.client.get()  # sets the cookie
    
        csrftoken = self.client.cookies['csrftoken']
        perms = '{"users":{"AnonymousUser":["view_resourcebase","download_resourcebase"]},"groups":{}}'

        response = self.client.post(self.shp_layer_upload_url\
                        , files=files\
                        , data={'csrfmiddlewaretoken':csrftoken\
                                    , 'permissions':perms\
                                    , 'charset': 'UTF-8'\
                                }\
                        )

        print response.content
        try:
            new_layer_name = json.loads(response.content)['url'].split('/')[2].replace('%3A', ':')
            print new_layer_name
            return new_layer_name
        except:
            return None
        
    def join_datatable_to_layer(self, join_props):
        """        
        Join a layer to a csv data table.  Example:
        
            join_props = {
                'table_name': 'ca_tracts_pop_002',
                'table_attribute': 'GEO.id2',
                'layer_typename': 'geonode:tl_2013_06_tract',
                'layer_attribute': 'GEOID'
            }
        """
        msgt('join_datatable_to_layer: %s' % self.join_datatable_url)
        
        assert isinstance(join_props, dict), "join_props must be a dict {}"
        for k in ('table_name', 'table_attribute', 'layer_typename', 'layer_attribute'):
            assert join_props.has_key(k), "join_props is missing key: %s" % k
         
        msg(join_props)

        response = self.client.post(self.join_datatable_url, data=join_props)
        print response.content

    def upload_csv_with_lat_lon(self, fname_to_upload, layer_props):
        msgt('upload_lat_lon: %s' % self.upload_lat_lon_url)

        files = {'uploaded_file': open(fname_to_upload,'rb')}

        response = self.client.post(self.upload_lat_lon_url\
                    , data=layer_props
                    , files=files)

        print response.content
        if response.status_code == 200:
            try:
                resp_dict = json.loads(response.content)
                datatable = resp_dict['datatable_name']
                print datatable
            except:
                print sys.exc_info()[0]
                return None
        else:
            resp_dict = json.loads(response.content)
            print "Server Error: " + resp_dict['msg']
            return None

    def load_csv_directory():
        file_list = glob.glob(INPUT_DIR + "/*.csv")
   
        for file in file_list:
            # Upload CSV
            print "file = " + file
            title = os.path.splitext(os.path.split(file)[1])[0]
            dt_name = tr.upload_csv_file(title, file)
            if dt_name:
                print dt_name
            else:
                print "Error: " + file
        
if __name__=='__main__':
    tr = TabularTest()
    tr.login_for_cookie()

    # --Upload Layers to test with--
    #layer = tr.add_shapefile_layer('tabular-api/input/tl_2014_25_tract/', 'tl_2014_25_tract')
    #layer = tr.add_shapefile_layer('scratch/shape/', 'tl_2013_06_tract')
    #print layer

    # --Upload csv files to test with--
    #dt = tr.upload_csv_file('Boston Income', 'tabular-api/input/boston_income_73g.csv')
    #dt = tr.upload_csv_file('Boston Income', 'tabular-api/input/boston_income_73g.tab', delimiter_type='TAB')
    #dt = tr.upload_csv_file('Boston Income', 'tabular-api/input/boston_income_73g.tab', delimiter_type='TAB', no_header_row=True)
    
    # --Join CSV to existing layer--
    # Invalid Props
    #join_props = {'table_name':'xyz', 'layer_typename':'abc', 'table_attribute':'hij', 'layer_attribute':'qrs'} 
    # Missing table_name 
    #join_props = {'layer_typename':'abc', 'table_attribute':'hij', 'layer_attribute':'qrs'} 
    # Type Mismatch 
    #join_props = {'layer_typename': 'geonode:tl_2014_25_tract', 'table_name': 'boston_income_73g', 'table_attribute': 'tract', 'layer_attribute': 'TRACTCE'} 
    #tr.join_datatable_to_layer(join_props)

    # --Upload and Join--
    #join_props = {'title': 'CA Population', 'layer_typename': 'geonode:tl_2013_06_tract_whv', 'table_attribute': 'geoid2', 'layer_attribute': 'GEOID'} 
    #datatable, joinlayer = tr.upload_and_join('scratch/ca_tracts_pop.csv', join_props)
    #print datatable, joinlayer

    # --Upload CSV with Lat/Lon--
    #layer_props = {'title': 'Sierra Leone Health Facilities', 'lat_column':'Latitude', 'lon_column':'Longitude'}
    #layer = tr.upload_csv_with_lat_lon('scratch/csv/sle_heal_pt_unmeer_ccc.csv', layer_props)
