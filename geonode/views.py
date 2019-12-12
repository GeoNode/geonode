########################################################################
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

from geonode.groups.models import GroupProfile

from geonode.cephgeo.models import UserJurisdiction
from geonode.datarequests.models import DataRequestProfile

from pprint import pprint

from geonode.services.models import Service
from django.utils.translation import ugettext as _
from django.conf import settings
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.http import HttpResponse
from django.template import RequestContext
from geonode.utils import GXPMap
from geonode.utils import GXPLayer
from geonode.utils import default_map_config
from geonode.security.views import _perms_info_json
from geonode.documents.models import get_related_documents
from django.utils import simplejson as json
from geonode.utils import resolve_object, llbbox_to_mercator
from geonode.layers.models import Layer

_PERMISSION_MSG_GENERIC = _('You do not have permissions for this layer.')
_PERMISSION_MSG_VIEW = _("You are not permitted to view this layer")


def _resolve_layer(request, typename, permission='base.view_resourcebase',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = typename.split(":", 1)
    print(service_typename)
    service = Service.objects.filter(name=service_typename[0])
    print(service)
    if service.count() > 0:
        return resolve_object(request,
                              Layer,
                              {'service': service[0],
                               'typename': service_typename[1] if service[0].method != "C" else typename},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)
    else:
        return resolve_object(request,
                              Layer,
                              {'typename': typename,
                               'service': None},
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)


def philgrid(request,template='index.html'):
    layername = "geonode:philgrid"
    print('philgird exec')
    layer = _resolve_layer(
        request,
        layername,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)
    config = layer.attribute_config()
    # print "CONFIG 1" + str(config)

    # print layername
    # Add required parameters for GXP lazy-loading
    layer_bbox = layer.bbox
    # print layer_bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    srid = layer.srid

    # Transform WGS84 to Mercator.
    config["srs"] = srid if srid != "EPSG:4326" else "EPSG:900913"
    # print "SRID " + srid
    config["bbox"] = llbbox_to_mercator([float(coord) for coord in bbox])

    config["title"] = layer.title
    config["queryable"] = True

    # print "CONFIG 2" + str(config)
    print('philgrid exec post resolve_layer')
    if layer.storeType == "remoteStore":
        service = layer.service
        source_params = {
            "ptype": service.ptype,
            "remote": True,
            "url": service.base_url,
            "name": service.name}
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params))
    else:
        maplayer = GXPLayer(
            name=layer.typename,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))


    map_obj = GXPMap(projection="EPSG:900913")
    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config()[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    context_dict = {
        "resource": layer,
        "permissions_json": _perms_info_json(layer),
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
        "siteurl": settings.SITEURL + 'geoserver/ows?', # for local osm layergroup
    }

    context_dict["viewer"] = json.dumps(
        map_obj.viewer_json(request.user, * (NON_WMS_BASE_LAYERS + [maplayer])))
    context_dict["preview"] = getattr(
        settings,
        'LAYER_PREVIEW_LIBRARY',
        'leaflet')

    context_dict["layername"] = layername
    # print "CONTEXT DICT" + str(context_dict)
    # print "Layer" + str(layer)
    return render_to_response(template, RequestContext(request, context_dict))


class AjaxLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField()


def ajax_login(request):
    if request.method != 'POST':
        return HttpResponse(
            content="ajax login requires HTTP POST",
            status=405,
            mimetype="text/plain"
        )
    form = AjaxLoginForm(data=request.POST)
    if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse(
                content="bad credentials or disabled user",
                status=400,
                mimetype="text/plain"
            )
        else:
            login(request, user)
            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
            assign_relationships(user)
            return HttpResponse(
                content="successful login",
                status=200,
                mimetype="text/plain"
            )
    else:
        return HttpResponse(
            "The form you submitted doesn't look like a username/password combo.",
            mimetype="text/plain",
            status=400)


def ajax_lookup(request):
    if request.method != 'POST':
        return HttpResponse(
            content='ajax user lookup requires HTTP POST',
            status=405,
            mimetype='text/plain'
        )
    elif 'query' not in request.POST:
        return HttpResponse(
            content='use a field named "query" to specify a prefix to filter usernames',
            mimetype='text/plain')
    keyword = request.POST['query']
    users = get_user_model().objects.filter(Q(username__istartswith=keyword) |
                                            Q(first_name__icontains=keyword) |
                                            Q(organization__icontains=keyword)).exclude(username='AnonymousUser')
    groups = GroupProfile.objects.filter(Q(title__istartswith=keyword) |
                                         Q(description__icontains=keyword))
    json_dict = {
        'users': [({'username': u.username}) for u in users],
        'count': users.count(),
    }

    json_dict['groups'] = [({'name': g.slug, 'title': g.title}) for g in groups]
    return HttpResponse(
        content=json.dumps(json_dict),
        mimetype='text/plain'
    )


def err403(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(
            reverse('account_login') +
            '?next=' +
            request.get_full_path())
    else:
        return TemplateResponse(request, '401.html', {}, status=401).render()

def forbidden(request):
    return TemplateResponse(request, '401.html', {}, status=401).render()
