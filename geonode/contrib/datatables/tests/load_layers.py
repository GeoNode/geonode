import sys
import json
import requests

client = requests.session()

base_url = "http://localhost:8000"
login_url = base_url + "/account/login/"

# Retrieve the CSRF token first
client.get(login_url)  # sets the cookie
csrftoken = client.cookies['csrftoken']

login_data = dict(username="admin", password="admin", csrfmiddlewaretoken=csrftoken)
client.post(login_url, data=login_data, headers={"Referer": "test-client"})



files = {
    'base_file': open('input/tl_2014_25_tract/tl_2014_25_tract.shp','rb'),
    'dbf_file': open('input/tl_2014_25_tract/tl_2014_25_tract.dbf','rb'),
    'prj_file': open('input/tl_2014_25_tract/tl_2014_25_tract.prj','rb'),
    'shx_file': open('input/tl_2014_25_tract/tl_2014_25_tract.shx','rb'),
    'xml_file': open('input/tl_2014_25_tract/tl_2014_25_tract.shp.xml','rb')
    }

# Retrieve the CSRF token first
client.get(base_url + '/layers/upload')  # sets the cookie
csrftoken = client.cookies['csrftoken']
perms = '{"users":{"AnonymousUser":["view_resourcebase","download_resourcebase"]},"groups":{}}'

response = client.post(base_url + '/layers/upload', files=files, data={'csrfmiddlewaretoken':csrftoken, 'permissions':perms})

print response.content
