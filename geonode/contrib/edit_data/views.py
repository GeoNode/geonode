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
def add_row(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    feature_type = data_dict['feature_type']
    layer_name = data_dict['layer_name']
    full_layer_name = "geonode:" + layer_name

    layer = _resolve_layer(
        request,
        full_layer_name)

    success, message, status_code = save_added_row(layer_name, feature_type, data_dict)

    if (status_code == 200):
        update_bbox_in_CSW(layer, layer_name)
    return JsonResponse({'success': success,  'message': message})


@login_required
def edits(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    feature_id = data_dict['feature_id']
    layer_name = data_dict['layer_name']

    success, message, status_code = save_edits(layer_name, feature_id, data_dict)
    return JsonResponse({'success': success,  'message': message})

@login_required
def geom_edits(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    coords = ' '.join(map(str, data_dict['coords']))
    feature_id = data_dict['feature_id']
    layer_name = data_dict['layer_name']
    full_layer_name = "geonode:" + layer_name

    layer = _resolve_layer(
        request,
        full_layer_name)

    success, message, status_code = save_geom_edits(layer_name, feature_id, coords)

    if (status_code == 200):
        update_bbox_in_CSW(layer, layer_name)
    return JsonResponse({'success': success,  'message': message})

@login_required
def delete_row(request, template='edit_data/edit_data.html'):

    data_dict = json.loads(request.POST.get('json_data'))
    feature_id = data_dict['feature_id']
    layer_name = data_dict['layer_name']

    success, message, status_code = delete_selected_row(layer_name, feature_id)

    return JsonResponse({'success': success, 'message': message})
