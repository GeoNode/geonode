#!/usr/bin/env python

from __future__ import print_function
from geonode.settings import GEONODE_APPS
import geonode.settings as settings
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'geonode.settings')

from geonode.layers.models import Layer
import copy
import requests

json_template = {
    'layerGroup': {
        'name': '',
        'title': '',
        'mode': 'SINGLE',
        'workspace': {
            'name': 'geonode'
        },
        'publishables': {
            'published': []
        },
        'styles': {
            'style': []
        }
    }
}

layer_json_template = {
    '@type': 'layer',
    # 'name': 'san_juan_fh5yr_10m',
    'name': '',
    # 'href': 'http:\/\/localhost\/geoserver\/rest\/layers\/san_juan_fh5yr_10m.json'
    'href': ''
}

fhm_style_json = {
    'name': 'fhm',
    'href': 'http:\/\/localhost\/geoserver\/rest\/styles\/fhm.json'
}

for yr in ['5', '25', '100']:

    print('FHM ' + yr + 'yr...')

    # Create json object
    print('Creating json object...', end='')
    layers = Layer.objects.filter(name__icontains='fh' + yr)
    json_data = copy.deepcopy(json_template)

    for layer in layers:
        lj = copy.deepcopy(layer_json_template)
        lj['name'] = layer.name
        lj['href'] = 'http:\/\/localhost\/geoserver\/rest\/layers\/' + \
            layer.name + '.json'
        json_data['layerGroup']['publishables']['published'].append(lj)
        json_data['layerGroup']['styles']['style'].append(fhm_style_json)

    json_data['layerGroup']['name'] = 'fhms_' + yr + 'yr'
    json_data['layerGroup']['title'] = 'Flood Hazard Maps ' + yr + 'yr'
    # print json.dumps(json_data, indent=4, sort_keys=True)
    print('Done!')

    # Delete existing layer group if exists
    lgs_url = settings.SITEURL + 'geoserver/rest/workspaces/geonode/layergroups.json'
    _auth = (settings.OGC_SERVER['default']['USER'],
             settings.OGC_SERVER['default']['PASSWORD'])
    r = requests.get(lgs_url, auth=_auth)
    for lg in r.json()['layerGroups']['layerGroup']:
        if lg['name'] == json_data['layerGroup']['name']:
            print('Deleting existing layer group...', end='')
            lg_url = settings.SITEURL + \
                'geoserver/rest/workspaces/geonode/layergroups/' + \
                lg['name'] + '.json'
            r = requests.delete(lg_url, auth=_auth)
            if r.status_code != 200:
                print('Error deleting layer group' + lg['name'] + '! Exiting.')
                print('r.status_code:', r.status_code)
                print('r.text:', r.text)
                exit(1)
            print('Done!')
            break

    # Create new layer group
    print('Creating layer group...', end='')
    r = requests.post(lgs_url, auth=_auth, json=json_data)
    if r.status_code != 201:
        print('Error creating layer group! Exiting.')
        print('r.status_code:', r.status_code)
        print('r.text:', r.text)
        exit(1)
    print('Done!')
    # break
