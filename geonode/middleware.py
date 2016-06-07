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

try:
    import json
except ImportError:
    from django.utils import simplejson as json
from django.http import HttpResponse

from geonode.geoserver.helpers import ogc_server_settings
from geonode.security.views import _perms_info_json


class PrintProxyMiddleware(object):
    def process_request(self, request):
        if request.method == 'POST':
            if 'url' in request.GET and 'pdf' in request.GET['url']:
                print_map(request)


def print_map(request):
    from proxy.views import proxy
    from layers.models import Layer

    permissions = {}
    params = json.loads(request.body)
    for layer in params['layers']:
        if ogc_server_settings.LOCATION in layer['baseURL']:
            for layer_name in layer['layers']:
                layer_obj = Layer.objects.get(typename=layer_name)
                permissions[layer_obj] = _perms_info_json(layer_obj)
                layer_obj.set_default_permissions()
    try:
        resp = proxy(request)
    except Exception:
        return HttpResponse('There was an error connecting to the printing server')
    finally:
        for layer_obj in permissions.keys():
            layer_obj.set_permissions(json.loads(permissions[layer_obj]))

    return resp
