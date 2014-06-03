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

from django.utils.translation import ugettext_lazy as _

from geonode.security.enumerations import ANONYMOUS_USERS, AUTHENTICATED_USERS

from django.utils import simplejson as json
from django.core.exceptions import PermissionDenied
from geonode.utils import resolve_object
from django.http import HttpResponse, HttpResponseRedirect
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase

def _view_perms_context(obj):

    ctx =  obj.get_all_level_info()
    def lname(l):
        return level_names.get(l, _("???"))
    ctx[ANONYMOUS_USERS] = lname(ctx.get(ANONYMOUS_USERS, obj.LEVEL_NONE))
    ctx[AUTHENTICATED_USERS] = lname(ctx.get(AUTHENTICATED_USERS, obj.LEVEL_NONE))

    ulevs = []
    for u, l in ctx['users'].items():
        ulevs.append([u, lname(l)])
    ulevs.sort()
    ctx['users'] = ulevs

    return ctx

def _perms_info(obj):
    info = obj.get_all_level_info()
    
    return info


def _perms_info_json(obj):
    info = _perms_info(obj)
    info['users'] = dict([(u.username, perms) for u, perms in info['users'].items()])
    info['groups'] = dict([(g.name, perms) for g, perms in info['groups'].items()])

    return json.dumps(info)

def resource_permissions(request, resource_id):
    try:
        resource = resolve_object(request, ResourceBase, {'id':resource_id}, 'base.change_resourcebase_permissions')

    except PermissionDenied:
        # we are handling this in a non-standard way
        return HttpResponse(
            'You are not allowed to change permissions for this resource',
            status=401,
            mimetype='text/plain')

    if request.method == 'POST':
        permission_spec = json.loads(request.body)
        resource.set_permissions(permission_spec)

        return HttpResponse(
            json.dumps({'success': True}),
            status=200,
            mimetype='text/plain'
        )

    elif request.method == 'GET':
        permission_spec = json.dumps(resource.get_all_level_info())
        return HttpResponse(
            json.dumps({'success': True, 'permissions': permission_spec}),
            status=200,
            mimetype='text/plain'
        )
    else:
        return HttpResponse(
            'No methods other than get and post are allowed',
            status=401,
            mimetype='text/plain')
