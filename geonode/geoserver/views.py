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

import json
import logging
import base64
import httplib2
import os

from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext as _

from guardian.shortcuts import get_objects_for_user

from geonode.base.models import ResourceBase
from geonode.layers.forms import LayerStyleUploadForm
from geonode.layers.models import Layer, Style
from geonode.layers.views import _resolve_layer, _PERMISSION_MSG_MODIFY
from geonode.geoserver.signals import gs_catalog
from geonode.tasks.update import geoserver_update_layers
from geonode.utils import json_response, _get_basic_auth_info
from geoserver.catalog import FailedRequestError, ConflictingDataError
from lxml import etree
from .helpers import get_stores, ogc_server_settings, set_styles, style_update, create_gs_thumbnail

logger = logging.getLogger(__name__)


def stores(request, store_type=None):
    stores = get_stores(store_type)
    data = json.dumps(stores)
    return HttpResponse(data)


@user_passes_test(lambda u: u.is_superuser)
def updatelayers(request):
    params = request.REQUEST
    # Get the owner specified in the request if any, otherwise used the logged
    # user
    owner = params.get('owner', None)
    owner = get_user_model().objects.get(
        username=owner) if owner is not None else request.user
    workspace = params.get('workspace', None)
    store = params.get('store', None)
    filter = params.get('filter', None)
    geoserver_update_layers.delay(ignore_errors=False, owner=owner, workspace=workspace,
                                  store=store, filter=filter)

    return HttpResponseRedirect(reverse('layer_browse'))


@login_required
@require_POST
def layer_style(request, layername):
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_MODIFY)

    style_name = request.POST.get('defaultStyle')

    # would be nice to implement
    # better handling of default style switching
    # in layer model or deeper (gsconfig.py, REST API)

    old_default = layer.default_style
    if old_default.name == style_name:
        return HttpResponse(
            "Default style for %s remains %s" %
            (layer.name, style_name), status=200)

    # This code assumes without checking
    # that the new default style name is included
    # in the list of possible styles.

    new_style = (
        style for style in layer.styles if style.name == style_name).next()

    # Does this change this in geoserver??
    layer.default_style = new_style
    layer.styles = [
        s for s in layer.styles if s.name != style_name] + [old_default]
    layer.save()

    return HttpResponse(
        "Default style for %s changed to %s" %
        (layer.name, style_name), status=200)


@login_required
def layer_style_upload(request, layername):
    def respond(*args, **kw):
        kw['content_type'] = 'text/html'
        return json_response(*args, **kw)
    form = LayerStyleUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return respond(errors="Please provide an SLD file.")

    data = form.cleaned_data
    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase',
        _PERMISSION_MSG_MODIFY)

    sld = request.FILES['sld'].read()

    try:
        dom = etree.XML(sld)
    except Exception:
        return respond(errors="The uploaded SLD file is not valid XML")

    el = dom.findall(
        "{http://www.opengis.net/sld}NamedLayer/{http://www.opengis.net/sld}Name")
    if len(el) == 0 and not data.get('name'):
        return respond(
            errors="Please provide a name, unable to extract one from the SLD.")
    name = data.get('name') or el[0].text
    if data['update']:
        match = None
        styles = list(layer.styles) + [layer.default_style]
        for style in styles:
            if style.sld_name == name:
                match = style
                break
        if match is None:
            return respond(errors="Cannot locate style : " + name)
        match.update_body(sld)
    else:
        try:
            cat = gs_catalog
            cat.create_style(name, sld)
            layer.styles = layer.styles + \
                [type('style', (object,), {'name': name})]
            cat.save(layer.publishing)
        except ConflictingDataError:
            return respond(errors="""A layer with this name exists. Select
                                     the update option if you want to update.""")
    return respond(
        body={
            'success': True,
            'style': name,
            'updated': data['update']})


@login_required
def layer_style_manage(request, layername):

    layer = _resolve_layer(
        request,
        layername,
        'layers.change_layer_style',
        _PERMISSION_MSG_MODIFY)

    if request.method == 'GET':
        try:
            cat = gs_catalog

            # First update the layer style info from GS to GeoNode's DB
            # The try/except is
            try:
                set_styles(layer, cat)
            except AttributeError:
                logger.warn(
                    'Unable to set the default style.  Ensure Geoserver is running and that this layer exists.')

            all_available_gs_styles = cat.get_styles()
            gs_styles = []
            for style in all_available_gs_styles:
                gs_styles.append((style.name, style.sld_title))

            current_layer_styles = layer.styles.all()
            layer_styles = []
            for style in current_layer_styles:
                layer_styles.append((style.name, style.sld_title))

            # Render the form
            return render_to_response(
                'layers/layer_style_manage.html',
                RequestContext(request, {
                    "layer": layer,
                    "gs_styles": gs_styles,
                    "layer_styles": layer_styles,
                    "default_style": (layer.default_style.name, layer.default_style.sld_title)
                }
                )
            )
        except (FailedRequestError, EnvironmentError) as e:
            msg = ('Could not connect to geoserver at "%s"'
                   'to manage style information for layer "%s"' % (
                       ogc_server_settings.LOCATION, layer.name)
                   )
            logger.warn(msg, e)
            # If geoserver is not online, return an error
            return render_to_response(
                'layers/layer_style_manage.html',
                RequestContext(request, {
                    "layer": layer,
                    "error": msg
                }
                )
            )
    elif request.method == 'POST':
        try:
            selected_styles = request.POST.getlist('style-select')
            default_style = request.POST['default_style']
            # Save to GeoServer
            cat = gs_catalog
            gs_layer = cat.get_layer(layer.name)
            gs_layer.default_style = cat.get_style(default_style)
            styles = []
            for style in selected_styles:
                styles.append(cat.get_style(style))
            gs_layer.styles = styles
            cat.save(gs_layer)

            # Save to Django
            layer = set_styles(layer, cat)
            layer.save()
            return HttpResponseRedirect(
                reverse(
                    'layer_detail',
                    args=(
                        layer.service_typename,
                    )))
        except (FailedRequestError, EnvironmentError, MultiValueDictKeyError) as e:
            msg = ('Error Saving Styles for Layer "%s"' % (layer.name)
                   )
            logger.warn(msg, e)
            return render_to_response(
                'layers/layer_style_manage.html',
                RequestContext(request, {
                    "layer": layer,
                    "error": msg
                }
                )
            )


def feature_edit_check(request, layername):
    """
    If the layer is not a raster and the user has edit permission, return a status of 200 (OK).
    Otherwise, return a status of 401 (unauthorized).
    """
    layer = _resolve_layer(request, layername)
    datastore = ogc_server_settings.DATASTORE
    feature_edit = getattr(settings, "GEOGIG_DATASTORE", None) or datastore
    if request.user.has_perm(
            'change_layer_data',
            obj=layer) and layer.storeType == 'dataStore' and feature_edit:
        return HttpResponse(
            json.dumps({'authorized': True}), content_type="application/json")
    else:
        return HttpResponse(
            json.dumps({'authorized': False}), content_type="application/json")


def style_change_check(request, path):
    """
    If the layer has not change_layer_style permission, return a status of
    401 (unauthorized)
    """
    # a new style is created with a POST and then a PUT,
    # a style is updated with a PUT
    # a layer is updated with a style with a PUT
    # in both case we need to check permissions here
    # for PUT path is /gs/rest/styles/san_andres_y_providencia_water_a452004b.xml
    # or /ge/rest/layers/geonode:san_andres_y_providencia_coastline.json
    # for POST path is /gs/rest/styles
    # we will suppose that a user can create a new style only if he is an
    # authenticated (we need to discuss about it)
    authorized = True
    if request.method == 'POST':
        # new style
        if not request.user.is_authenticated:
            authorized = False
    if request.method == 'PUT':
        if path == 'rest/layers':
            # layer update, should be safe to always authorize it
            authorized = True
        else:
            # style update
            # we will iterate all layers (should be just one if not using GS)
            # to which the posted style is associated
            # and check if the user has change_style_layer permissions on each of them
            style_name = os.path.splitext(request.path)[0].split('/')[-1]
            try:
                style = Style.objects.get(name=style_name)
                for layer in style.layer_styles.all():
                    if not request.user.has_perm('change_layer_style', obj=layer):
                        authorized = False
            except:
                authorized = False
                logger.warn(
                    'There is not a style with such a name: %s.' % style_name)
    return authorized


def geoserver_rest_proxy(request, proxy_path, downstream_path):

    if not request.user.is_authenticated():
        return HttpResponse(
            "You must be logged in to access GeoServer",
            content_type="text/plain",
            status=401)

    def strip_prefix(path, prefix):
        assert path.startswith(prefix)
        return path[len(prefix):]

    path = strip_prefix(request.get_full_path(), proxy_path)
    url = str("".join([ogc_server_settings.LOCATION, downstream_path, path]))

    http = httplib2.Http()
    username, password = ogc_server_settings.credentials
    auth = base64.encodestring(username + ':' + password)
    # http.add_credentials(*(ogc_server_settings.credentials))
    headers = dict()

    affected_layers = None

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]
        headers["Authorization"] = "Basic " + auth
        # if user is not authorized, we must stop him
        # we need to sync django here and check if some object (styles) can
        # be edited by the user
        # we should remove this geonode dependency calling layers.views straight
        # from GXP, bypassing the proxy
        if downstream_path in ('rest/styles', 'rest/layers') and len(request.body) > 0:
            if not style_change_check(request, downstream_path):
                return HttpResponse(
                    _("You don't have permissions to change style for this layer"),
                    content_type="text/plain",
                    status=401)
            if downstream_path == 'rest/styles':
                affected_layers = style_update(request, url)

    response, content = http.request(
        url, request.method,
        body=request.body or None,
        headers=headers)

    # update thumbnails
    if affected_layers:
        for layer in affected_layers:
            logger.debug('Updating thumbnail for layer with uuid %s' % layer.uuid)
            create_gs_thumbnail(layer, True)

    return HttpResponse(
        content=content,
        status=response.status,
        content_type=response.get("content-type", "text/plain"))


def layer_batch_download(request):
    """
    batch download a set of layers

    POST - begin download
    GET?id=<download_id> monitor status
    """

    from geonode.utils import http_client
    # currently this just piggy-backs on the map download backend
    # by specifying an ad hoc map that contains all layers requested
    # for download. assumes all layers are hosted locally.
    # status monitoring is handled slightly differently.

    if request.method == 'POST':
        layers = request.POST.getlist("layer")
        layers = Layer.objects.filter(typename__in=list(layers))

        def layer_son(layer):
            return {
                "name": layer.typename,
                "service": layer.service_type,
                "metadataURL": "",
                "serviceURL": ""
            }

        readme = """This data is provided by GeoNode.\n\nContents:"""

        def list_item(lyr):
            return "%s - %s.*" % (lyr.title, lyr.name)

        readme = "\n".join([readme] + [list_item(l) for l in layers])

        fake_map = {
            "map": {"readme": readme},
            "layers": [layer_son(lyr) for lyr in layers]
        }

        url = "%srest/process/batchDownload/launch/" % ogc_server_settings.LOCATION
        resp, content = http_client.request(
            url, 'POST', body=json.dumps(fake_map))
        return HttpResponse(content, status=resp.status)

    if request.method == 'GET':
        # essentially, this just proxies back to geoserver
        download_id = request.GET.get('id', None)
        if download_id is None:
            return HttpResponse(status=404)

        url = "%srest/process/batchDownload/status/%s" % (
            ogc_server_settings.LOCATION, download_id)
        resp, content = http_client.request(url, 'GET')
        return HttpResponse(content, status=resp.status)


def resolve_user(request):
    user = None
    geoserver = False
    superuser = False
    acl_user = request.user
    if 'HTTP_AUTHORIZATION' in request.META:
        username, password = _get_basic_auth_info(request)
        acl_user = authenticate(username=username, password=password)
        if acl_user:
            user = acl_user.username
            superuser = acl_user.is_superuser
        elif _get_basic_auth_info(request) == ogc_server_settings.credentials:
            geoserver = True
            superuser = True
        else:
            return HttpResponse(_("Bad HTTP Authorization Credentials."),
                                status=401,
                                content_type="text/plain")

    if not any([user, geoserver, superuser]
               ) and not request.user.is_anonymous():
        user = request.user.username
        superuser = request.user.is_superuser

    resp = {
        'user': user,
        'geoserver': geoserver,
        'superuser': superuser,
    }

    if acl_user and acl_user.is_authenticated():
        resp['fullname'] = acl_user.get_full_name()
        resp['email'] = acl_user.email
    return HttpResponse(json.dumps(resp), content_type="application/json")


def layer_acls(request):
    """
    returns json-encoded lists of layer identifiers that
    represent the sets of read-write and read-only layers
    for the currently authenticated user.
    """
    # the layer_acls view supports basic auth, and a special
    # user which represents the geoserver administrator that
    # is not present in django.
    acl_user = request.user
    if 'HTTP_AUTHORIZATION' in request.META:
        try:
            username, password = _get_basic_auth_info(request)
            acl_user = authenticate(username=username, password=password)

            # Nope, is it the special geoserver user?
            if (acl_user is None and
                    username == ogc_server_settings.USER and
                    password == ogc_server_settings.PASSWORD):
                # great, tell geoserver it's an admin.
                result = {
                    'rw': [],
                    'ro': [],
                    'name': username,
                    'is_superuser': True,
                    'is_anonymous': False
                }
                return HttpResponse(
                    json.dumps(result),
                    content_type="application/json")
        except Exception:
            pass

        if acl_user is None:
            return HttpResponse(_("Bad HTTP Authorization Credentials."),
                                status=401,
                                content_type="text/plain")

    # Include permissions on the anonymous user
    # use of polymorphic selectors/functions to optimize performances
    resources_readable = get_objects_for_user(acl_user, 'view_resourcebase',
                                              ResourceBase.objects.instance_of(Layer)).values_list('id', flat=True)
    layer_writable = get_objects_for_user(acl_user, 'change_layer_data',
                                          Layer.objects.all())

    _read = set(Layer.objects.filter(id__in=resources_readable).values_list('typename', flat=True))
    _write = set(layer_writable.values_list('typename', flat=True))

    read_only = _read ^ _write
    read_write = _read & _write

    result = {
        'rw': list(read_write),
        'ro': list(read_only),
        'name': acl_user.username,
        'is_superuser': acl_user.is_superuser,
        'is_anonymous': acl_user.is_anonymous(),
    }
    if acl_user.is_authenticated():
        result['fullname'] = acl_user.get_full_name()
        result['email'] = acl_user.email

    return HttpResponse(json.dumps(result), content_type="application/json")
