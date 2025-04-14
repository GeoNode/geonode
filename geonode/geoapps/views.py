#########################################################################
#
# Copyright (C) 2020 OSGeo
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
import ast
import json
import logging

from django.conf import settings
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.core.exceptions import PermissionDenied

from geonode.client.hooks import hookset
from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.security.views import _perms_info_json
from geonode.geoapps.models import GeoApp
from geonode.resource.manager import resource_manager

from geonode.utils import resolve_object
from geonode.security.registry import permissions_registry


logger = logging.getLogger("geonode.geoapps.views")

_PERMISSION_MSG_GENERIC = _("You do not have permissions for this app.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this app.")


def _resolve_geoapp(request, id, permission="base.change_resourcebase", msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the GeoApp by the provided typename and check the optional permission.
    """

    return resolve_object(request, GeoApp, {"pk": id}, permission=permission, permission_msg=msg, **kwargs)


@login_required
def new_geoapp(request, template="apps/app_new.html"):
    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    if request.method == "GET":
        _ctx = {
            "user": request.user,
            "access_token": access_token,
        }
        return render(request, template, context=_ctx)

    return HttpResponseRedirect(hookset.geoapp_list_url())


@xframe_options_sameorigin
def geoapp_edit(request, geoappid, template="apps/app_edit.html"):
    """
    The view that returns the app composer opened to
    the app with the given app ID.
    """
    try:
        geoapp_obj = _resolve_geoapp(request, geoappid, "base.view_resourcebase", _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not geoapp_obj:
        raise Http404(_("Not found"))

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(geoapp_obj)

    perms_list = permissions_registry.get_perms(instance=geoapp_obj, user=request.user)

    group = None
    if geoapp_obj.group:
        try:
            group = GroupProfile.objects.get(slug=geoapp_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    r = geoapp_obj
    if request.method in ("POST", "PATCH", "PUT"):
        r = resource_manager.update(geoapp_obj.uuid, instance=geoapp_obj, notify=True)

        resource_manager.set_permissions(
            geoapp_obj.uuid, instance=geoapp_obj, permissions=ast.literal_eval(permissions_json)
        )

        resource_manager.set_thumbnail(geoapp_obj.uuid, instance=geoapp_obj, overwrite=False)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    _config = json.dumps(r.blob)
    _ctx = {
        "appId": geoappid,
        "appType": geoapp_obj.resource_type,
        "config": _config,
        "user": request.user,
        "access_token": access_token,
        "resource": geoapp_obj,
        "group": group,
        "perms_list": perms_list,
        "permissions_json": permissions_json,
        "preview": getattr(settings, "GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY", "mapstore"),
    }

    return render(request, template, context=_ctx)
