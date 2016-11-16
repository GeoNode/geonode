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
from django import forms
from django.contrib.auth import authenticate, login, get_user_model
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.utils import simplejson as json
from django.db.models import Q
from django.template.response import TemplateResponse
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.template import RequestContext

from pprint import pprint

from actstream.models import Action
from geonode.eula.models import AnonDownloader

def report_layer(request, template='report_layers.html'):
    layer_count = {}
    layer_count['jan'] = {
        "cov": 0,
        "doc": 0,
        "fhm": 0,
        "dtm": 0,
        "dsm": 0,
        "laz": 0,
        "ortho": 0,
        "sar": 0,
        "others": 0,
    }
    auth_list = Action.objects.filter(verb='downloaded').order_by('timestamp')
    for auth in auth_list:
        if auth.timestamp.strftime('%b') not in layer_count:
            layer_count[auth.timestamp.strftime('%b')] = {
                "cov": 0,
                "doc": 0,
                "fhm": 0,
                "dtm": 0,
                "dsm": 0,
                "laz": 0,
                "ortho": 0,
                "sar": 0,
                "others": 0,
            }
        if auth.action_object.csw_type == 'document':
            layer_count[auth.timestamp.strftime('%b')]['doc'] += 1
        else:
            if 'coverage' in auth.action_object.typename:
                layer_count[auth.timestamp.strftime('%b')]['cov'] += 1
            elif 'fh' in auth.action_object.typename:
                layer_count[auth.timestamp.strftime('%b')]['fhm'] += 1
            elif 'dtm' in auth.action_object.typename:
                layer_count[auth.timestamp.strftime('%b')]['dtm'] += 1
            elif 'dsm' in auth.action_object.typename:
                layer_count[auth.timestamp.strftime('%b')]['dsm'] += 1
            elif 'laz' in auth.action_object.typename:
                layer_count[auth.timestamp.strftime('%b')]['laz'] += 1
            elif 'ortho' in auth.action_object.typename:
                layer_count[auth.timestamp.strftime('%b')]['ortho'] += 1
            elif 'sar' in auth.action_object.typename:
                layer_count[auth.timestamp.strftime('%b')]['sar'] += 1
            else:
                layer_count[auth.timestamp.strftime('%b')]['others'] += 1

    anon_list = AnonDownloader.objects.all().order_by('date')
    for anon in anon_list:
        if anon.date.strftime('%b') not in layer_count:
            layer_count[anon.date.strftime('%b')] = {
                "cov": 0,
                "doc": 0,
                "fhm": 0,
                "dtm": 0,
                "dsm": 0,
                "laz": 0,
                "ortho": 0,
                "sar": 0,
                "others": 0,
            }
        if anon.anon_document:
            layer_count[anon.date.strftime('%b')]['doc'] += 1
        else:
            if 'coverage' in anon.anon_layer.typename:
                layer_count[anon.date.strftime('%b')]['cov'] += 1
            elif 'fh' in anon.anon_layer.typename:
                layer_count[anon.date.strftime('%b')]['fhm'] += 1
            elif 'dtm' in anon.anon_layer.typename:
                layer_count[anon.date.strftime('%b')]['dtm'] += 1
            elif 'dsm' in anon.anon_layer.typename:
                layer_count[anon.date.strftime('%b')]['dsm'] += 1
            elif 'laz' in anon.anon_layer.typename:
                layer_count[anon.date.strftime('%b')]['laz'] += 1
            elif 'ortho' in anon.anon_layer.typename:
                layer_count[anon.date.strftime('%b')]['ortho'] += 1
            elif 'sar' in anon.anon_layer.typename:
                layer_count[anon.date.strftime('%b')]['sar'] += 1
            else:
                layer_count[anon.date.strftime('%b')]['others'] += 1
    pprint(layer_count)

    context_dict = {
        "layer_count": layer_count,
    }
    return render_to_response(template, RequestContext(request, context_dict))
