# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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


from geoserver.catalog import Catalog

from collections import OrderedDict
import requests
import re
import time

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
#from django.http import HttpResponse, HttpResponseRedirect
from django.http import JsonResponse
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.conf import settings

from geonode.layers.views import _resolve_layer, _PERMISSION_MSG_MODIFY
from .utils import *


@login_required
def display_data(request, layername, template='edit_data/edit_data.html'):

    #start_time = time.time()
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_MODIFY)
    workspace, name = layer.typename.split(':')
    #initialize context_dict
    context_dict = {}
    context_dict["resource"] = layer
    # get layer's attributes with display_order gt 0
    layers_attributes = []
    attr_to_display = layer.attribute_set.filter(display_order__gt=0)
    for values in attr_to_display.values('attribute'):
        layers_attributes.append(values['attribute'])

    # get the metadata description
    attribute_description = {}
    display_order_dict = {}

    wfs, filtered_attributes, context_dict = data_display_schema( name, layers_attributes, context_dict )

    for idx, value in enumerate(filtered_attributes):
        description = layer.attribute_set.values('description').filter(attribute=value)
        display_order = layer.attribute_set.values('display_order').filter(attribute=value)
        attribute_description[value] = description[0]['description']
        display_order_dict[value] = display_order[0]['display_order']

    context_dict = data_display( name, wfs, layers_attributes, attribute_description, display_order_dict, filtered_attributes, context_dict )

    #print("--- %s seconds ---" % (time.time() - start_time))
    return render(request, template, context_dict )



@login_required
def delete_edits(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    feature_id = data_dict['feature_id']
    layer_name = data_dict['layer_name']

    xml_path = "edit_data/wfs_delete_row.xml"
    xmlstr = get_template(xml_path).render({
            'layer_name': layer_name,
            'feature_id': feature_id}).strip()

    url = settings.OGC_SERVER['default']['LOCATION'] + 'wfs'
    headers = {'Content-Type': 'application/xml'}  # set what your server accepts
    status_code = requests.post(url, data=xmlstr, headers=headers, auth=(settings.OGC_SERVER['default']['USER'], settings.OGC_SERVER['default']['PASSWORD'])).status_code

    if (status_code != 200):
        message = "Failed to delete row."
        success = False
        return JsonResponse({'success': success, 'message': message})
    else:
        message = "Row was deleted successfully."
        success = True
        return JsonResponse({'success': success, 'message': message})

    return JsonResponse({'success': success, 'message': message})



@login_required
def save_edits(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    feature_id = data_dict['feature_id']
    layer_name = data_dict['layer_name']
    data = data_dict['data']
    data = data.split(",")
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
        message = "Failed to save edited data."
        success = False
        return JsonResponse({'success': success, 'message': message})
    else:
        message = "Edits were saved successfully."
        success = True
        return JsonResponse({'success': success, 'message': message})


@login_required
def save_geom_edits(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    feature_id = data_dict['feature_id']
    layer_name = data_dict['layer_name']
    coords = ' '.join(map(str, data_dict['coords']))

    full_layer_name = "geonode:" + layer_name
    layer = _resolve_layer(
        request,
        full_layer_name)

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
        message = "Error saving the geometry."
        success = False
        return JsonResponse({'success': success, 'message': message})
    else:
        message = "Edits were saved successfully."
        success = True
        update_bbox_in_CSW(layer, layer_name)
        return JsonResponse({'success': success,  'message': message})



@login_required
def save_added_row(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    feature_type = data_dict['feature_type']
    layer_name = data_dict['layer_name']
    full_layer_name = "geonode:" + layer_name
    data = data_dict['data'].split(",")

    layer = _resolve_layer(
        request,
        full_layer_name)

    success, message, status_code = add_row(layer_name, feature_type, data, data_dict)

    if (status_code == 200):
        update_bbox_in_CSW(layer, layer_name)
    return JsonResponse({'success': success,  'message': message})
