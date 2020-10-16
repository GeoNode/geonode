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
from django.db.models import F
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.views.decorators.clickjacking import xframe_options_sameorigin

from guardian.shortcuts import get_perms

from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.security.views import _perms_info_json
from geonode.geoapps.models import GeoApp, GeoAppData
from geonode.monitoring import register_event
from geonode.monitoring.models import EventType
from geonode.utils import (
    resolve_object,
    build_social_links
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

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    if request.method == 'GET':
        _ctx = {
            'user': request.user,
            'access_token': access_token,
        }
        return render(request, template, context=_ctx)

    return HttpResponseRedirect(reverse("apps_browse"))


def geoapp_detail(request, geoappid, template='apps/app_detail.html'):
    """
    The view that returns the app composer opened to
    the app with the given app ID.
    """
    geoapp_obj = _resolve_geoapp(
        request,
        geoappid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    # Add metadata_author or poc if missing
    geoapp_obj.add_missing_metadata_author_or_poc()

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != geoapp_obj.owner and not request.user.is_superuser:
        GeoApp.objects.filter(
            id=geoapp_obj.id).update(
            popular_count=F('popular_count') + 1)

    _data = GeoAppData.objects.filter(resource__id=geoappid).first()
    _config = _data.blob if _data else {}

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(geoapp_obj)

    perms_list = get_perms(
        request.user,
        geoapp_obj.get_self_resource()) + get_perms(request.user, geoapp_obj)

    group = None
    if geoapp_obj.group:
        try:
            group = GroupProfile.objects.get(slug=geoapp_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        'appId': geoappid,
        'appType': geoapp_obj.type,
        'config': _config,
        'user': request.user,
        'access_token': access_token,
        'resource': geoapp_obj,
        'group': group,
        'perms_list': perms_list,
        'permissions_json': permissions_json,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore'),
        'crs': getattr(
            settings,
            'DEFAULT_MAP_CRS',
            'EPSG:3857')
    }

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, geoapp_obj)

    if request.user.is_authenticated:
        if getattr(settings, 'FAVORITE_ENABLED', False):
            from geonode.favorite.utils import get_favorite_info
            context_dict["favorite_info"] = get_favorite_info(request.user, geoapp_obj)

    register_event(request, EventType.EVENT_VIEW, request.path)

    return render(request, template, context=context_dict)


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

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(geoapp_obj)

    perms_list = get_perms(
        request.user,
        geoapp_obj.get_self_resource()) + get_perms(request.user, geoapp_obj)

    group = None
    if geoapp_obj.group:
        try:
            group = GroupProfile.objects.get(slug=geoapp_obj.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    _data = GeoAppData.objects.filter(resource__id=geoappid).first()
    _config = _data.blob if _data else {}
    _ctx = {
        'appId': geoappid,
        'appType': geoapp_obj.type,
        'config': _config,
        'user': request.user,
        'access_token': access_token,
        'resource': geoapp_obj,
        'group': group,
        'perms_list': perms_list,
        "permissions_json": permissions_json,
        'preview': getattr(
            settings,
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
            'mapstore')
    }

    return render(request, template, context=_ctx)
