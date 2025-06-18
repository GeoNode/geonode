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
import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt

from geonode.base import register_event
from geonode.base.auth import get_or_create_token
from geonode.base.enumerations import EventType
from geonode.maps.contants import (
    _PERMISSION_MSG_GENERIC,
    _PERMISSION_MSG_VIEW,
    MSG_NOT_ALLOWED,
    MSG_NOT_FOUND,
)
from geonode.maps.models import Map
from geonode.utils import resolve_object

logger = logging.getLogger("geonode.maps.views")


def _resolve_map(request, id, permission="base.change_resourcebase", msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the Map by the provided typename and check the optional permission.
    """
    key = "urlsuffix" if Map.objects.filter(urlsuffix=id).exists() else "pk"

    map_obj = resolve_object(request, Map, {key: id}, permission=permission, permission_msg=msg, **kwargs)
    return map_obj


@xframe_options_exempt
def map_embed(request, mapid=None, template="maps/map_embed.html"):
    try:
        map_obj = _resolve_map(request, mapid, "base.view_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(MSG_NOT_ALLOWED, status=403)
    except Exception:
        raise Http404(MSG_NOT_FOUND)

    if not map_obj:
        raise Http404(MSG_NOT_FOUND)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        "access_token": access_token,
        "resource": map_obj,
    }

    register_event(request, EventType.EVENT_VIEW, map_obj)
    return render(request, template, context=context_dict)
