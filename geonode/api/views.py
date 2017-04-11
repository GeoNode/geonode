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

from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.http import HttpResponse, HttpResponseRedirect

import urllib2
from django.core.urlresolvers import resolve
import json
from urlparse import urljoin
from urllib2 import HTTPError

import geonode.settings as settings

def api_combined(request, apiname):
    current_url = request.build_absolute_uri()
    tostrip = 'limit='+str(request.GET.get('limit'))+'&offset='+str(request.GET.get('offset'))
    apiquery = '?'.join(current_url.split('?')[1:]).replace(tostrip,'').rstrip('&').lstrip('&')
    local_url = urljoin(current_url,'../')
    urls_to_visit = settings.LIPAD_INSTANCES
    output = {}
    # output = []
    for each_url in urls_to_visit:
        try:
            # output.append (each_url + 'api/' + apiname + '/?' + apiquery)
            response = urllib2.urlopen(each_url + 'api/' + apiname + '/?' + apiquery)
            data = json.loads(response.read())
            for each_key in data.keys():
                try:
                    if data.keys().index(each_key) == 1: ##dict's key == u'object'
                        for i_object in range(len(data[each_key])):
                            data[each_key][i_object]['thumbnail_url'] = each_url + data[each_key][i_object]['thumbnail_url'][1:] if 'upd.edu.ph/' not in data[each_key][i_object]['thumbnail_url'] else each_url + data[each_key][i_object]['thumbnail_url'].split('up.edu.ph/')[1]
                            data[each_key][i_object]['detail_url'] = each_url + data[each_key][i_object]['detail_url'][1:]
                        output[each_key] += data[each_key]
                    else:##dict's key == u'meta'
                        for each_meta_key in output[each_key].keys():
                            output[each_key][each_meta_key] = int(output[each_key][each_meta_key])+int(data[each_key][each_meta_key])
                except:##dict has no value then assign's u'meta'
                    output[each_key] = data[each_key]
        except HTTPError:
            continue
    return HttpResponse(json.dumps(output),mimetype='application/json',status=200)

def api_autocomplete(request):
    current_url = request.build_absolute_uri()
    apiquery = '?'.join(current_url.split('?')[1:])
    local_url = 'http://'+request.META['HTTP_HOST']+'/'#for lipad.dmz""
    urls_to_visit = [local_url] + settings.LIPAD_INSTANCES
    output = ''

    # output = []
    for each_url in urls_to_visit:
        try:
            # output.append (each_url + 'autocomplete/ResourceBaseAutocomplete/?' + apiquery)
            response = urllib2.urlopen(each_url + 'autocomplete/ResourceBaseAutocomplete/?' + apiquery)
            data = response.read()
            if 'No matches found' not in data:
                output += data
        except:
            pass
    return HttpResponse(output,mimetype='application/json',status=200)
