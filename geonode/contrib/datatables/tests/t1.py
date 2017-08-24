from os.path import join, isfile, isdir
import os
import sys
import requests

"""
https://github.com/jj0hns0n/geonode/blob/table-join/geonode/contrib/datatables/tests/integration.py
"""

INPUT_DIR = join('..', 'input')
assert isdir(INPUT_DIR), "Directory %s not found" % INPUT_DIR

#   http://23.23.180.177:8000/datatables/api/upload
#   http://23.23.180.177:8000/datatables/api/join

SERVER_BASE = 'http://23.23.180.177'
AUTH_PARAMS = ('admin', 'admin')

def try_upload(title, fname):
    global SERVER_BASE, AUTH_PARAMS
    #assert isfile(fname), "File not found: %s" % fname
    assert title is not None, "title cannot be None"
    
    payload = dict(title=title)
    #files = {'file': open(fname, 'rb')}
    
    api_url = SERVER_BASE + '/datatables/api/upload'
    
    r = requests.get(api_url\
                    , data=payload\
                    , auth=AUTH_PARAMS\
                    #, files=files\
                    )
    
    print r.text
    print r.status_code
    
    resp_dict = r.json()
    print resp_dict
    
    #  Invalid HTTP_HOST header: 'testserver'.You may need to add u'testserver' to ALLOWED_HOSTS.

if __name__=='__main__':
    test_csv = join(INPUT_DIR, 'all_140_in_06.P1.csv')
    try_upload('Tab Test 001', test_csv)
