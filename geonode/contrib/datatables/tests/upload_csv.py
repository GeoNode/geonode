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
r = client.post(login_url, data=login_data, headers={"Referer": "test-client"})
print r

files = {'uploaded_file': open('scratch/ca_tracts_pop.csv','rb')}
response = client.post(base_url + '/datatables/api/upload', data={'title':'test'}, files=files)
print response.content

#
resp_dict = json.loads(response.content)
datatable_name = resp_dict['datatable_name']
print datatable_name
