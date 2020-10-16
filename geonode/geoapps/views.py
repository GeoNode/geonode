# -*- coding: utf-8 -*-
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
import logging

from django.conf import settings
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.clickjacking import xframe_options_sameorigin

from geonode.geoapps.models import GeoApp, GeoAppData
from geonode.utils import (
    resolve_object
)

logger = logging.getLogger("geonode.geoapps.views")

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this app.")
_PERMISSION_MSG_GENERIC = _("You do not have permissions for this app.")
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this app")
_PERMISSION_MSG_SAVE = _("You are not permitted to save or edit this app.")
_PERMISSION_MSG_METADATA = _(
    "You are not allowed to modify this app's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this app.")
_PERMISSION_MSG_UNKNOWN = _("An unknown error has occured.")


def _resolve_geoapp(request, id, permission='base.change_resourcebase',
                    msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the GeoApp by the provided typename and check the optional permission.
    '''
    if GeoApp.objects.filter(urlsuffix=id).count() > 0:
        key = 'urlsuffix'
    else:
        key = 'pk'

    return resolve_object(request, GeoApp, {key: id}, permission=permission,
                          permission_msg=msg, **kwargs)


@login_required
def new_geoapp(request, template='apps/app_new.html'):
    if request.method == 'GET':
        ctx = {}
        return render(request, template, context=ctx)

    return HttpResponseRedirect(reverse("apps_browse"))


def geoapp_detail(request, layername, template='layers/layer_detail.html'):
    # layer = _resolve_layer(
    #     request,
    #     layername,
    #     'base.view_resourcebase',
    #     _PERMISSION_MSG_VIEW)

    # permission_manager = ManageResourceOwnerPermissions(layer)
    # permission_manager.set_owner_permissions_according_to_workflow()

    # # Add metadata_author or poc if missing
    # layer.add_missing_metadata_author_or_poc()
    pass


@xframe_options_sameorigin
def geoapp_edit(request, geoappid, template='apps/app_edit.html'):
    """
    The view that returns the app composer opened to
    the app with the given app ID.
    """
    geoapp_obj = _resolve_geoapp(
        request,
        geoappid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    _data = GeoAppData.objects.filter(resource__id=geoappid).first()
    _config = _data.blob if _data else {}
    _ctx = {
        'appId': geoappid,
        'appType': geoapp_obj.type,
        'config': _config,
        'app': geoapp_obj,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore')
    }

    return render(request, template, context=_ctx)
