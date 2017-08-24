from os.path import join
from msg_util import *

from tabular_test import TabularTest, INPUT_DIR
        
def upload_boston_income_csv():
    tr = TabularTest()
    tr.login_for_cookie()

    # Upload CSV
    title = 'Boston Income'
    fname_to_upload = join(INPUT_DIR, 'boston_income_73g.csv')
    
    #fname_to_upload = join(INPUT_DIR, 'boston_income_73g-1-row.csv')
    #fname_to_upload = join(INPUT_DIR, '2-ma-counties.csv')
    #fname_to_upload = join(INPUT_DIR, '2-ca-measures.csv')
    
    tr.upload_csv_file(title, fname_to_upload)

    # boston_income_73g

def upload_boston_cenus_csv():
    tr = TabularTest()
    tr.login_for_cookie()

    # Upload CSV
    title = 'Boston Census'
    fname_to_upload = join(INPUT_DIR, 'c_bra_CSV-of-SHAPE.csv')
    tr.upload_csv_file(title, fname_to_upload)



def upload_ma_tigerlines():
    tr = TabularTest()
    tr.login_for_cookie()

    # Upload Shapefile parts
    shp_fname_prefix = 'tl_2014_25_tract'
    shp_dirname = join(INPUT_DIR, 'tl_2014_25_tract')
    tr.add_shapefile_layer(shp_dirname, shp_fname_prefix)
    
    # geonode:tl_2014_25_tract
def upload_ma_tigerlines_csv():
    tr = TabularTest()
    tr.login_for_cookie()

    # Upload CSV
    title = 'MA tigerlines Census'
    fname_to_upload = join(INPUT_DIR, 'tl_2014_25_tract.csv')
    tr.upload_csv_file(title, fname_to_upload)
    
    #{"datatable_id": 34, "datatable_name": "tl_2014_25_tract"}

    
def join_boston_census():

    join_props = {
        'layer_typename' : 'geonode:c_bra_bl',  # underlying layer (orig shp)
        'layer_attribute': 'TRACT', # underlying layer - attribute
        'table_name': 'c_bra_csv_of_shape', # data table (orig csv)
        'table_attribute': 'TRACT', # data table - attribute
    }

    tr = TabularTest()
    tr.login_for_cookie()
    tr.join_datatable_to_layer(join_props)

def join_boston_income():
     
    join_props = {
        'layer_typename' : 'geonode:tl_2014_25_tract',  # underlying layer (orig shp)
        'layer_attribute': 'TRACTCE', # underlying layer - attribute
        'table_name': 'boston_income_73g_luwf5pu', # data table (orig csv)
        'table_attribute': 'TRACT', # data table - attribute
    }
   
   
    tr = TabularTest()
    tr.login_for_cookie()
    tr.join_datatable_to_layer(join_props)
    
    
if __name__=='__main__':
    
    #-----------------------------
    # Join boston income to census
    #-----------------------------
    # (1) Add MA tigerlines: 
    #result: {"url": "/layers/geonode%3Atl_2014_25_tract", "success": true}
    #upload_ma_tigerlines()
    
    # (2) Add boston income csv
    #   result: {"datatable_id": 45, "datatable_name": "boston_income_73g_hsilxjb"}
    #upload_boston_income_csv()
    
    # (3) Try table join
    join_boston_income()
