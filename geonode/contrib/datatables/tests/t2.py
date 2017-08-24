from os.path import join
import sys
import json
import requests
from msg_util import *
#from django.contrib.auth import get_user_model
#from django.core.urlresolvers import reverse

INPUT_DIR = '../input'

class TestRun:
    
    def __init__(self):
        self.client = requests.session()
        self.base_url = "http://23.23.180.177"
        #self.datatable_name = None
        
    def login_for_cookie(self):

        login_url = self.base_url + "/account/login/"

        # Retrieve the CSRF token first
        self.client.get(login_url)  # sets the cookie
        csrftoken = self.client.cookies['csrftoken']

        login_data = dict(username="admin", password="admin", csrfmiddlewaretoken=csrftoken)
        msgt('Login: %s' % login_url)
        r = self.client.post(login_url, data=login_data, headers={"Referer": "test-client"})

        #print r.text
        print r.status_code

        
    def upload_one(self, title, fname_to_upload):

        upload_url = self.base_url + '/datatables/api/upload'

        msgt('upload 1: %s' % upload_url)

        files = {'uploaded_file': open(fname_to_upload,'rb')}
        response = self.client.post(upload_url\
                    , data={'title' : title }\
                    , files=files)

        #print response.content

        print response.text
        print response.status_code
        resp_dict = json.loads(response.content)
        datatable_name = resp_dict['datatable_name']
        print datatable_name
        return

    def upload_two(self, datatable_name):

        layer_upload_url = self.base_url + '/layers/upload'

        msgt('upload_two: %s' % layer_upload_url)


        files = {
            'base_file': open(join(INPUT_DIR, 'c_bra_bl.shp'), 'rb'),
            'dbf_file': open(join(INPUT_DIR, 'c_bra_bl.dbf'), 'rb'),
            'prj_file': open(join(INPUT_DIR, 'c_bra_bl.prj'), 'rb'),
            'shx_file': open(join(INPUT_DIR, 'c_bra_bl.shx'), 'rb'),
            }
        #     'base_file': open('scratch/tl_2013_06_tract.shp','rb'),
        #    'dbf_file': open('scratch/tl_2013_06_tract.dbf','rb'),
        #    'prj_file': open('scratch/tl_2013_06_tract.prj','rb'),
        #    'shx_file': open('scratch/tl_2013_06_tract.shx','rb'),
        #    'xml_file': open('scratch/tl_2013_06_tract.shp.xml','rb')

        # Retrieve the CSRF token first
        #self.client.get()  # sets the cookie
    
        csrftoken = self.client.cookies['csrftoken']
        perms = '{"users":{"AnonymousUser":["view_resourcebase","download_resourcebase"]},"groups":{}}'

        response = self.client.post(layer_upload_url\
                        , files=files\
                        , data={'csrfmiddlewaretoken':csrftoken\
                                    , 'permissions':perms\
                                }\
                        )

        print response.content
        new_layer_name = json.loads(response.content)['url'].split('/')[2].replace('%3A', ':')
        print new_layer_name
        
    def upload_three(self, datatable_name, layer_name):
    
        api_join_url = self.base_url + '/datatables/api/join'
        msgt('upload_three: %s' % api_join_url)
        
        xjoin_props = {
        'table_name': 'ca_tracts_pop_002',
        'table_attribute': 'GEO.id2',
        'layer_typename': 'geonode:tl_2013_06_tract',
        'layer_attribute': 'GEOID'
        }
        
        join_props = {
        'table_name': 'ca_tracts_pop_002',
        'table_attribute': 'GEO.id2',
        'layer_typename': 'geonode:tl_2013_06_tract',
        'layer_attribute': 'GEOID'
        }
        
        '''
        join_props = {
            'table_name': datatable_name, # social disorder
            'table_attribute': 'Tract', 
            'layer_typename' : 'c_bra_bl',
            #'layer_typename': layer_name,   # CA census blocks
            'layer_attribute': 'TRACT'
        }
        '''
        print join_props

        response = self.client.post(api_join_url, data=join_props)
        print response.content
        
        
        
if __name__=='__main__':
    tr = TestRun()
    tr.login_for_cookie()
    
    # Upload CSV
    title = 'California Pop Test'
    fname_to_upload = join(INPUT_DIR, 'ca_tracts_pop_002.csv')
    #tr.upload_one(title, fname_to_upload)
    # {"datatable_id": 28, "datatable_name": "ca_tracts_pop_002"}
    
    # Join CSV to existing layer
    tr.upload_three('---', '----')
    # {'layer_typename': 'geonode:tl_2013_06_tract', 'table_name': 'ca_tracts_pop_002', 'table_attribute': 'GEO.id2', 'layer_attribute': 'GEOID'}
    #{"join_layer": "geonode:view_join_tl_2013_06_tract_ca_tracts_pop_002", "source_layer": "geonode:tl_2013_06_tract", "view_name": "view_join_tl_2013_06_tract_ca_tracts_pop_002", "table_attribute": "GEO.id2", "layer_attribute": "GEOID", "layer_url": "/layers/geonode%3Aview_join_tl_2013_06_tract_ca_tracts_pop_002", "datatable": "ca_tracts_pop_002", "join_id": 8}
    #tr.upload_two('social_disorder_in_boston_yqh_zip_411')
    
    
    #tr.upload_three('social_disorder_in_boston_yqh_zip_411', 'geonode:c_bra_bl')
    
"""
National zip codes:
    - tl_2014_us_zcta510.zip

"""