# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

"""Utilities for managing GeoNode edit data
"""
from collections import OrderedDict
import requests
import operator
import json

from owslib.wfs import WebFeatureService
from owslib.feature.schema import get_schema

from django.conf import settings
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from geonode.base.models import ResourceBase
from geonode.utils import bbox_to_wkt

from geoserver.catalog import Catalog


# the data_edit_schema and the data_edit functions are used in edit_data front page in order to display all data
def data_display_schema(name, layers_attributes, context_dict):
    # geoserver parameters
    username = settings.OGC_SERVER['default']['USER']
    password = settings.OGC_SERVER['default']['PASSWORD']
    location = "{location}{service}".format(** {
        'location': settings.OGC_SERVER['default']['LOCATION'],
        'service': 'wms',
    })

    wfs = WebFeatureService(location, version='1.1.0', username=username, password=password)
    schema = get_schema(location, name, username=username, password=password)

    # acquire the geometry of layer - requires improvement
    geom_dict = {
        'Point': 'Point',
        'MultiPoint': 'Point',
        'MultiSurfacePropertyType': 'Polygon',
        'MultiPolygon': 'Polygon',
        'MultiLineString': 'Linestring'
    }
    geom_type = schema.get('geometry') or schema['properties'].get('the_geom')
    context_dict["layer_geom"] = json.dumps(geom_dict.get(geom_type, 'unknown'))
    schema.pop("geometry")
    # remove the_geom/geom parameter
    if 'the_geom' in schema['properties']:
        schema['properties'].pop('the_geom', None)

    # filter the schema dict based on the values of layers_attributes
    layer_attributes_schema = []
    for key in schema['properties'].keys():
        if key in layers_attributes:
            layer_attributes_schema.append(key)
        else:
            schema['properties'].pop(key, None)

    context_dict["schema"] = schema
    filtered_attributes = list(set(layers_attributes).intersection(layer_attributes_schema))

    return wfs, filtered_attributes, context_dict


def data_display(name, wfs, layers_attributes, attribute_description, display_order_dict, filtered_attributes, context_dict):
    response = wfs.getfeature(typename=name, propertyname=filtered_attributes, outputFormat='application/json')
    features_response = json.dumps(json.loads(response.read()))
    decoded = json.loads(features_response)
    decoded_features = decoded['features']

    # order the list and create ordered dictionary
    display_order_list_sorted = sorted(display_order_dict.items(), key=operator.itemgetter(1))
    display_order_dict_sorted = OrderedDict(display_order_list_sorted)

    # display_order_dict_sorted = dict(display_order_list_sorted)
    context_dict["feature_properties"] = json.dumps(decoded_features)
    context_dict["attribute_description"] = json.dumps(attribute_description)
    context_dict["display_order_dict_sorted"] = json.dumps(display_order_dict_sorted)
    context_dict["layer_name"] = json.dumps(name)
    context_dict["name"] = name
    context_dict["url"] = json.dumps(settings.OGC_SERVER['default']['LOCATION'])
    context_dict["site_url"] = json.dumps(settings.SITEURL)
    context_dict["default_workspace"] = json.dumps(settings.DEFAULT_WORKSPACE)

    return context_dict


def save_added_row(layer_name, feature_type, data, data_dict):

    # concatenate all the properties
    property_element = ""
    for i, val in enumerate(data):
        attribute, value = data[i].split("=")
        if value == "":
            continue
        # xml string with property element
        property_element_1 = """<{}>{}</{}>\n\t\t""".format(attribute, value, attribute)
        property_element = property_element + property_element_1


    # Make a Describe Feature request to get the correct link for the xmlns:geonode
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    xml_path = "edit_data/wfs_describe_feature.xml"
    xmlstr = get_template(xml_path).render({
            'layer_name': layer_name}).strip()
    url = settings.OGC_SERVER['default']['LOCATION'] + 'wfs'
    describe_feature_response = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).text

    from lxml import etree
    xml = bytes(bytearray(describe_feature_response, encoding='utf-8'))  # encode it and force the same encoder in the parser
    doc = etree.XML(xml)
    nsmap = {}
    for ns in doc.xpath('//namespace::*'):
        nsmap[ns[0]] = ns[1]
    if nsmap['geonode']:
        geonode_url = nsmap['geonode']

    # Prepare the WFS-T insert request depending on the geometry
    if feature_type == 'Point':
        coords = ','.join(map(str, data_dict['coords']))
        coords = coords.replace(",", " ")
        xml_path = "edit_data/wfs_add_new_point.xml"
    elif feature_type == 'LineString':
        coords = ','.join(map(str, data_dict['coords']))
        coords = re.sub('(,[^,]*),', r'\1 ', coords)
        xml_path = "edit_data/wfs_add_new_line.xml"
    elif feature_type == 'Polygon':
        coords = [item for sublist in data_dict['coords'] for item in sublist]
        coords = ','.join(map(str, coords))
        coords = coords.replace(",", " ")
        xml_path = "edit_data/wfs_add_new_polygon.xml"

    store_name, geometry_clm = get_store_name(layer_name)
    geometry_clm = "the_geom"
    xmlstr = get_template(xml_path).render({
            'geonode_url': geonode_url,
            'layer_name': layer_name,
            'coords': coords,
            'property_element': mark_safe(property_element),
            'geometry_clm': geometry_clm}).strip()

    url = settings.OGC_SERVER['default']['LOCATION'] + 'geonode/wfs'
    status_code = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code

    status_code_bbox, status_code_seed = update_bbox_and_seed(headers, layer_name, store_name)

    if (status_code != 200):
        message = "Error adding data."
        success = False
        return success, message, status_code
    else:
        message = "New data were added succesfully."
        success = True
        return success, message, status_code


def save_edits(layer_name, feature_id, data_dict):
    data = data_dict['data'].split(",")
    data = [x.encode('ascii', 'ignore').decode('ascii') for x in data]

    url = settings.OGC_SERVER['default']['LOCATION'] + 'wfs'
    property_element = ""
    # concatenate all the properties
    for i, val in enumerate(data):
        attribute, value = data[i].split("=")
        # xml string with property element
        property_element_1 = """<wfs:Property>
          <wfs:Name>{}</wfs:Name>
          <wfs:Value>{}</wfs:Value>
        </wfs:Property>\n""".format(attribute, value)
        property_element = property_element + property_element_1
    # build the update wfs-t request
    xml_path = "edit_data/wfs_edit_data.xml"
    xmlstr = get_template(xml_path).render({
            'layer_name': layer_name,
            'feature_id': feature_id,
            'property_element': mark_safe(property_element)}).strip()

    headers = {'Content-Type': 'application/xml'}  # set what your server accepts

    status_code = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code

    if (status_code != 200):
        message = "Error adding data."
        success = False
        return success, message, status_code
    else:
        message = "New data were added succesfully."
        success = True
        return success, message, status_code


def save_geom_edits(layer_name, feature_id, coords):

    store_name, geometry_clm = get_store_name(layer_name)
    geometry_clm = "the_geom"
    xml_path = "edit_data/wfs_edit_point_geom.xml"
    xmlstr = get_template(xml_path).render({
            'layer_name': layer_name,
            'coords': coords,
            'feature_id': feature_id,
            'geometry_clm': geometry_clm}).strip()

    url = settings.OGC_SERVER['default']['LOCATION'] + 'wfs'
    headers = {'Content-Type': 'application/xml'} # set what your server accepts
    status_code = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code

    status_code_bbox, status_code_seed = update_bbox_and_seed(headers, layer_name, store_name)

    if (status_code != 200):
        message = "Error adding data."
        success = False
        return success, message, status_code
    else:
        message = "New data were added succesfully."
        success = True
        return success, message, status_code


def delete_selected_row(layer_name, feature_id):

    xml_path = "edit_data/wfs_delete_row.xml"
    xmlstr = get_template(xml_path).render({
            'layer_name': layer_name,
            'feature_id': feature_id}).strip()

    url = settings.OGC_SERVER['default']['LOCATION'] + 'wfs'
    headers = {'Content-Type': 'application/xml'}  # set what your server accepts
    status_code = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code

    if (status_code != 200):
        message = "Error adding data."
        success = False
        return success, message, status_code
    else:
        message = "New data were added succesfully."
        success = True
        return success, message, status_code

    return success, message, status_code

# Used to update the BBOX of geoserver and send a see request
# Takes as input the headers and the layer_name
# Returns status_code of each request
def update_bbox_and_seed(headers, layer_name, store_name):
    # Update the BBOX of layer in geoserver (use of recalculate)
    url = settings.OGC_SERVER['default']['LOCATION'] + "rest/workspaces/geonode/datastores/{store_name}/featuretypes/{layer_name}.xml?recalculate=nativebbox,latlonbbox".format(** {
        'store_name': store_name.strip(),
        'layer_name': layer_name
    })

    xmlstr = """<featureType><enabled>true</enabled></featureType>"""
    status_code_bbox = requests.put(url, headers=headers, data=xmlstr, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code

    # Seed the cache for this layer
    url = settings.OGC_SERVER['default']['LOCATION'] + "gwc/rest/seed/geonode:{layer_name}.xml".format(** {
        'layer_name': layer_name
    })
    xml_path = "edit_data/seedRequest_geom.xml"
    xmlstr = get_template(xml_path).render({
            'workspace': 'geonode',
            'layer_name': layer_name
            })
    status_code_seed = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code
    return status_code_bbox, status_code_seed


# Update the values for BBOX in CSW with the values calculated in geoserver layer
def update_bbox_in_CSW(layer, layer_name):

    # Get the coords from geoserver layer and update the base_resourceBase table
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest", settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])
    resource = cat.get_resource(layer_name, workspace="geonode")
    # use bbox_to_wkt to convert the BBOX coords to the wkt format
    r = bbox_to_wkt(resource.latlon_bbox[0], resource.latlon_bbox[1], resource.latlon_bbox[2], resource.latlon_bbox[3], "4326")
    csw_wkt_geometry = r.split(";", 1)[1]
    # update the base_resourceBase
    resources = ResourceBase.objects.filter(pk=layer.id)
    resources.update(bbox_x0=resource.latlon_bbox[0], bbox_x1=resource.latlon_bbox[1], bbox_y0=resource.latlon_bbox[2], bbox_y1=resource.latlon_bbox[3], csw_wkt_geometry=csw_wkt_geometry)

    return csw_wkt_geometry


#  Returns the store name based on the workspace and the layer name
def get_store_name(layer_name):
    # get the name of the store
    cat = Catalog(settings.OGC_SERVER['default']['LOCATION'] + "rest", settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])
    resource = cat.get_resource(layer_name, workspace='geonode')
    store_name = resource.store.name

    # select the name of the geometry column based on the store type
    if (store_name == "uploaded"):
        geometry_clm = "the_geom"
    else:
        geometry_clm = "shape"

    return store_name, geometry_clm
