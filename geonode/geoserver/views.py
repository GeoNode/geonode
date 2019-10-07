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

import os
import re
import json
import logging
import traceback
from lxml import etree
from defusedxml import lxml as dlxml
from os.path import isfile

from urlparse import urlsplit, urljoin

from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext as _

from guardian.shortcuts import get_objects_for_user
from geonode.base.models import ResourceBase
from geonode.base.auth import get_or_create_token
from geonode.layers.forms import LayerStyleUploadForm
from geonode.layers.models import Layer, Style
from geonode.layers.views import _resolve_layer, _PERMISSION_MSG_MODIFY
from geonode.maps.models import Map
from geonode.proxy.views import proxy
from geonode.geoserver.signals import gs_catalog
from .tasks import geoserver_update_layers
from geonode.utils import json_response, _get_basic_auth_info, http_client
from geoserver.catalog import FailedRequestError
from .helpers import (get_stores,
                      ogc_server_settings,
                      extract_name_from_sld,
                      set_styles,
                      style_update,
                      set_layer_style,
                      _stylefilterparams_geowebcache_layer,
                      _invalidate_geowebcache_layer)

from django_basic_auth import logged_in_or_basicauth
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_control

logger = logging.getLogger(__name__)


def stores(request, store_type=None):
    stores = get_stores(store_type)
    data = json.dumps(stores)
    return HttpResponse(data)


@user_passes_test(lambda u: u.is_superuser)
def updatelayers(request):
    params = request.GET
    # Get the owner specified in the request if any, otherwise used the logged
    # user
    owner = params.get('owner', None)
    owner = get_user_model().objects.get(
        username=owner) if owner is not None else request.user
    workspace = params.get('workspace', None)
    store = params.get('store', None)
    filter = params.get('filter', None)
    geoserver_update_layers.delay(
        ignore_errors=False, owner=owner, workspace=workspace,
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

    # Invalidate GeoWebCache for the updated resource
    try:
        _stylefilterparams_geowebcache_layer(layer.alternate)
        _invalidate_geowebcache_layer(layer.alternate)
    except BaseException:
        pass

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
    sld_name = None
    try:
        # Check SLD is valid
        try:
            if sld:
                if isfile(sld):
                    sld = open(sld, "r").read()
                etree.XML(sld)
        except Exception:
            logger.exception("The uploaded SLD file is not valid XML")
            raise Exception(
                "The uploaded SLD file is not valid XML")

        sld_name = extract_name_from_sld(
            gs_catalog, sld, sld_file=request.FILES['sld'])
    except Exception as e:
        respond(errors="The uploaded SLD file is not valid XML: {}".format(e))

    name = data.get('name') or sld_name

    set_layer_style(layer, data.get('title') or name, sld)

    return respond(
        body={
            'success': True,
            'style': data.get('title') or name,
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
            try:
                set_styles(layer, cat)
            except AttributeError:
                logger.warn(
                    'Unable to set the default style.  Ensure Geoserver is running and that this layer exists.')

            gs_styles = []
            # Temporary Hack to remove GeoServer temp styles from the list
            Style.objects.filter(name__iregex=r'\w{8}-\w{4}-\w{4}-\w{4}-\w{12}_(ms)_\d{13}').delete()
            for style in Style.objects.values('name', 'sld_title'):
                gs_styles.append((style['name'], style['sld_title']))
            current_layer_styles = layer.styles.all()
            layer_styles = []
            for style in current_layer_styles:
                sld_title = style.name
                try:
                    if style.sld_title:
                        sld_title = style.sld_title
                except BaseException:
                    tb = traceback.format_exc()
                    logger.debug(tb)
                layer_styles.append((style.name, sld_title))

            # Render the form
            def_sld_name = None  # noqa
            def_sld_title = None  # noqa
            if layer.default_style:
                def_sld_name = layer.default_style.name  # noqa
                def_sld_title = layer.default_style.name  # noqa
                try:
                    if layer.default_style.sld_title:
                        def_sld_title = layer.default_style.sld_title
                except BaseException:
                    tb = traceback.format_exc()
                    logger.debug(tb)

            default_style = (def_sld_name, def_sld_title)

            return render(
                request,
                'layers/layer_style_manage.html',
                context={
                    "layer": layer,
                    "gs_styles": gs_styles,
                    "layer_styles": layer_styles,
                    "layer_style_names": [s[0] for s in layer_styles],
                    "default_style": default_style
                }
            )
        except (FailedRequestError, EnvironmentError):
            tb = traceback.format_exc()
            logger.debug(tb)
            msg = ('Could not connect to geoserver at "%s"'
                   'to manage style information for layer "%s"' % (
                       ogc_server_settings.LOCATION, layer.name)
                   )
            logger.debug(msg)
            # If geoserver is not online, return an error
            return render(
                request,
                'layers/layer_style_manage.html',
                context={
                    "layer": layer,
                    "error": msg
                }
            )
    elif request.method in ('POST', 'PUT', 'DELETE'):
        try:
            selected_styles = request.POST.getlist('style-select')

            default_style = request.POST['default_style']

            # Save to GeoServer
            cat = gs_catalog
            gs_layer = cat.get_layer(layer.name)
            if not gs_layer:
                gs_layer = cat.get_layer(layer.alternate)

            if gs_layer:
                gs_layer.default_style = cat.get_style(default_style, workspace=settings.DEFAULT_WORKSPACE) or \
                    cat.get_style(default_style)
                styles = []
                for style in selected_styles:
                    gs_sld = cat.get_style(style, workspace=settings.DEFAULT_WORKSPACE) or cat.get_style(style)
                    if gs_sld:
                        styles.append(gs_sld)
                gs_layer.styles = styles
                cat.save(gs_layer)

            # Save to Django
            set_styles(layer, cat)

            # Invalidate GeoWebCache for the updated resource
            try:
                _stylefilterparams_geowebcache_layer(layer.alternate)
                _invalidate_geowebcache_layer(layer.alternate)
            except BaseException:
                pass

            return HttpResponseRedirect(
                reverse(
                    'layer_detail',
                    args=(
                        layer.service_typename,
                    )))
        except (FailedRequestError, EnvironmentError, MultiValueDictKeyError):
            tb = traceback.format_exc()
            logger.debug(tb)
            msg = ('Error Saving Styles for Layer "%s"' % (layer.name)
                   )
            logger.warn(msg)
            return render(
                request,
                'layers/layer_style_manage.html',
                context={
                    "layer": layer,
                    "error": msg
                }
            )


def feature_edit_check(request, layername, permission='change_layer_data'):
    """
    If the layer is not a raster and the user has edit permission, return a status of 200 (OK).
    Otherwise, return a status of 401 (unauthorized).
    """
    try:
        layer = _resolve_layer(request, layername)
    except BaseException:
        # Intercept and handle correctly resource not found exception
        return HttpResponse(
            json.dumps({'authorized': False}), content_type="application/json")
    datastore = ogc_server_settings.DATASTORE
    feature_edit = datastore
    is_admin = False
    is_staff = False
    is_owner = False
    is_manager = False
    if request.user:
        is_admin = request.user.is_superuser if request.user else False
        is_staff = request.user.is_staff if request.user else False
        is_owner = (str(request.user) == str(layer.owner))
        try:
            is_manager = request.user.groupmember_set.all().filter(
                role='manager').exists()
        except BaseException:
            is_manager = False
    if is_admin or is_staff or is_owner or is_manager or request.user.has_perm(
            permission,
            obj=layer) and \
            ((permission == 'change_layer_data' and layer.storeType == 'dataStore' and feature_edit) or
             True):
        return HttpResponse(
            json.dumps({'authorized': True}), content_type="application/json")
    else:
        return HttpResponse(
            json.dumps({'authorized': False}), content_type="application/json")


def style_edit_check(request, layername):
    """
    If the layer is not a raster and the user has edit permission, return a status of 200 (OK).
    Otherwise, return a status of 401 (unauthorized).
    """
    return feature_edit_check(request, layername, permission='change_layer_style')


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
    if request.method in ('PUT', 'POST'):
        if not request.user.is_authenticated:
            authorized = False
        elif path == 'rest/layers' and request.method == 'PUT':
            # layer update, should be safe to always authorize it
            authorized = True
        else:
            # style new/update
            # we will iterate all layers (should be just one if not using GS)
            # to which the posted style is associated
            # and check if the user has change_style_layer permissions on each
            # of them
            style_name = os.path.splitext(request.path)[0].split('/')[-1]
            if style_name == 'styles' and 'raw' in request.GET:
                authorized = True
            else:
                try:
                    style = Style.objects.get(name=style_name)
                    for layer in style.layer_styles.all():
                        if not request.user.has_perm(
                                'change_layer_style', obj=layer):
                            authorized = False
                except BaseException:
                    authorized = (request.method == 'POST')  # The user is probably trying to create a new style
                    logger.warn(
                        'There is not a style with such a name: %s.' % style_name)
    return authorized


@csrf_exempt
@logged_in_or_basicauth(realm="GeoNode")
def geoserver_protected_proxy(request,
                              proxy_path,
                              downstream_path,
                              workspace=None,
                              layername=None):
    return geoserver_proxy(request,
                           proxy_path,
                           downstream_path,
                           workspace=workspace,
                           layername=layername)


@csrf_exempt
@cache_control(public=True, must_revalidate=True, max_age=30)
def geoserver_proxy(request,
                    proxy_path,
                    downstream_path,
                    workspace=None,
                    layername=None):
    """
    WARNING: Decorators are applied in the order they appear in the source.
    """
    # AF: No need to authenticate first. We will check if "access_token" is present
    # or not on session

    # @dismissed
    # if not request.user.is_authenticated():
    #     return HttpResponse(
    #         "You must be logged in to access GeoServer",
    #         content_type="text/plain",
    #         status=401)

    def strip_prefix(path, prefix):
        assert prefix in path
        prefix_idx = path.index(prefix)
        _prefix = path[:prefix_idx] + prefix
        full_prefix = "%s/%s/%s" % (
            _prefix, layername, downstream_path) if layername else _prefix
        return path[len(full_prefix):]

    path = strip_prefix(request.get_full_path(), proxy_path)

    raw_url = str(
        "".join([ogc_server_settings.LOCATION, downstream_path, path]))

    if settings.DEFAULT_WORKSPACE or workspace:
        ws = (workspace or settings.DEFAULT_WORKSPACE)
        if ws and ws in path:
            # Strip out WS from PATH
            try:
                path = "/%s" % strip_prefix(path, "/%s:" % (ws))
            except BaseException:
                pass

        if proxy_path == '/gs/%s' % settings.DEFAULT_WORKSPACE and layername:
            import posixpath
            raw_url = urljoin(ogc_server_settings.LOCATION,
                              posixpath.join(workspace, layername, downstream_path, path))

        if downstream_path in ('rest/styles') and len(request.body) > 0:
            if ws:
                # Lets try
                # http://localhost:8080/geoserver/rest/workspaces/<ws>/styles/<style>.xml
                _url = str("".join([ogc_server_settings.LOCATION,
                                    'rest/workspaces/', ws, '/styles',
                                    path]))
            else:
                _url = str("".join([ogc_server_settings.LOCATION,
                                    'rest/styles',
                                    path]))
            raw_url = _url

    if downstream_path in 'ows' and (
        'rest' in path or
            re.match(r'/(w.*s).*$', path, re.IGNORECASE) or
            re.match(r'/(ows).*$', path, re.IGNORECASE)):
        _url = str("".join([ogc_server_settings.LOCATION, '', path[1:]]))
        raw_url = _url
    url = urlsplit(raw_url)
    affected_layers = None

    if '%s/layers' % ws in path:
        downstream_path = 'rest/layers'
    elif '%s/styles' % ws in path:
        downstream_path = 'rest/styles'

    if request.method in ("POST", "PUT", "DELETE"):
        if downstream_path in ('rest/styles', 'rest/layers',
                               'rest/workspaces'):
            if not style_change_check(request, downstream_path):
                return HttpResponse(
                    _(
                        "You don't have permissions to change style for this layer"),
                    content_type="text/plain",
                    status=401)
            elif downstream_path == 'rest/styles':
                logger.info(
                    "[geoserver_proxy] Updating Style ---> url %s" %
                    url.geturl())
                affected_layers = style_update(request, raw_url)
            elif downstream_path == 'rest/layers':
                logger.debug(
                    "[geoserver_proxy] Updating Layer ---> url %s" %
                    url.geturl())
                try:
                    _layer_name = os.path.splitext(os.path.basename(request.path))[0]
                    _layer = Layer.objects.get(name__icontains=_layer_name)
                    affected_layers = [_layer]
                except BaseException:
                    logger.warn("Could not find any Layer %s on DB" % os.path.basename(request.path))

    kwargs = {'affected_layers': affected_layers}
    import urllib
    raw_url = urllib.unquote(raw_url).decode('utf8')
    timeout = getattr(ogc_server_settings, 'TIMEOUT') or 10
    allowed_hosts = [urlsplit(ogc_server_settings.public_url).hostname, ]
    return proxy(request, url=raw_url, response_callback=_response_callback,
                 timeout=timeout, allowed_hosts=allowed_hosts, **kwargs)


def _response_callback(**kwargs):
    # affected_layers = kwargs['affected_layers']
    # response = kwargs['response']
    content = kwargs['content']
    status = kwargs['status']
    content_type = kwargs['content_type']

    # Replace Proxy URL
    if content_type in ('application/xml', 'text/xml', 'text/plain', 'application/json', 'text/json'):
        _gn_proxy_url = urljoin(settings.SITEURL, '/gs/')
        content = content\
            .replace(ogc_server_settings.LOCATION, _gn_proxy_url)\
            .replace(ogc_server_settings.PUBLIC_LOCATION, _gn_proxy_url)

    return HttpResponse(
        content=content,
        status=status,
        content_type=content_type)


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
               ) and not request.user.is_anonymous:
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


@logged_in_or_basicauth(realm="GeoNode")
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

    _read = set(
        Layer.objects.filter(
            id__in=resources_readable).values_list(
            'alternate',
            flat=True))
    _write = set(layer_writable.values_list('alternate', flat=True))

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


# capabilities
def get_layer_capabilities(layer, version='1.3.0', access_token=None, tolerant=False):
    """
    Retrieve a layer-specific GetCapabilities document
    """
    workspace, layername = layer.alternate.split(":") if ":" in layer.alternate else (None, layer.alternate)
    if not layer.remote_service:
        wms_url = '%s%s/%s/wms?service=wms&version=%s&request=GetCapabilities'\
            % (ogc_server_settings.LOCATION, workspace, layername, version)
        if access_token:
            wms_url += ('&access_token=%s' % access_token)
    else:
        wms_url = '%s?service=wms&version=%s&request=GetCapabilities'\
            % (layer.remote_service.service_url, version)

    _user, _password = ogc_server_settings.credentials
    req, content = http_client.get(wms_url, user=_user)
    getcap = content
    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        if tolerant and ('ServiceException' in getcap or req.status_code == 404):
            # WARNING Please make sure to have enabled DJANGO CACHE as per
            # https://docs.djangoproject.com/en/2.0/topics/cache/#filesystem-caching
            wms_url = '%s%s/ows?service=wms&version=%s&request=GetCapabilities&layers=%s'\
                % (ogc_server_settings.public_url, workspace, version, layer)
            if access_token:
                wms_url += ('&access_token=%s' % access_token)
            req, content = http_client.get(wms_url, user=_user)
            getcap = content

    if 'ServiceException' in getcap or req.status_code == 404:
        return None
    return getcap


def format_online_resource(workspace, layer, element, namespaces):
    """
    Replace workspace/layer-specific OnlineResource links with the more
    generic links returned by a site-wide GetCapabilities document
    """
    layerName = element.find('.//wms:Capability/wms:Layer/wms:Layer/wms:Name',
                             namespaces)
    if layerName is None:
        return

    layerName.text = workspace + ":" + layer if workspace else layer
    layerresources = element.findall('.//wms:OnlineResource', namespaces)
    if layerresources is None:
        return

    for resource in layerresources:
        wtf = resource.attrib['{http://www.w3.org/1999/xlink}href']
        replace_string = "/" + workspace + "/" + layer if workspace else "/" + layer
        resource.attrib['{http://www.w3.org/1999/xlink}href'] = wtf.replace(
            replace_string, "")


def get_capabilities(request, layerid=None, user=None,
                     mapid=None, category=None, tolerant=False):
    """
    Compile a GetCapabilities document containing public layers
    filtered by layer, user, map, or category
    """

    rootdoc = None
    layers = None
    cap_name = ' Capabilities - '
    if layerid is not None:
        layer_obj = Layer.objects.get(id=layerid)
        cap_name += layer_obj.title
        layers = Layer.objects.filter(id=layerid)
    elif user is not None:
        layers = Layer.objects.filter(owner__username=user)
        cap_name += user
    elif category is not None:
        layers = Layer.objects.filter(category__identifier=category)
        cap_name += category
    elif mapid is not None:
        map_obj = Map.objects.get(id=mapid)
        cap_name += map_obj.title
        alternates = []
        for layer in map_obj.layers:
            if layer.local:
                alternates.append(layer.name)
        layers = Layer.objects.filter(alternate__in=alternates)

    for layer in layers:
        if request.user.has_perm('view_resourcebase',
                                 layer.get_self_resource()):
            access_token = get_or_create_token(request.user)
            if access_token and not access_token.is_expired():
                access_token = access_token.token
            else:
                access_token = None
            try:
                workspace, layername = layer.alternate.split(":") if ":" in layer.alternate else (None, layer.alternate)
                layercap = get_layer_capabilities(layer,
                                                  access_token=access_token,
                                                  tolerant=tolerant)
                if layercap:  # 1st one, seed with real GetCapabilities doc
                    try:
                        namespaces = {'wms': 'http://www.opengis.net/wms',
                                      'xlink': 'http://www.w3.org/1999/xlink',
                                      'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
                        layercap = dlxml.fromstring(layercap)
                        rootdoc = etree.ElementTree(layercap)
                        format_online_resource(workspace, layername, rootdoc, namespaces)
                        service_name = rootdoc.find('.//wms:Service/wms:Name', namespaces)
                        if service_name:
                            service_name.text = cap_name
                        rootdoc = rootdoc.find('.//wms:Capability/wms:Layer/wms:Layer', namespaces)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        logger.error(
                            "Error occurred creating GetCapabilities for %s: %s" %
                            (layer.typename, str(e)))
                        rootdoc = None
                if not layercap or not rootdoc:
                    # Get the required info from layer model
                    # TODO: store time dimension on DB also
                    tpl = get_template("geoserver/layer.xml")
                    ctx = {
                        'layer': layer,
                        'geoserver_public_url': ogc_server_settings.public_url,
                        'catalogue_url': settings.CATALOGUE['default']['URL'],
                    }
                    gc_str = tpl.render(ctx)
                    gc_str = gc_str.encode("utf-8", "replace")
                    layerelem = etree.XML(gc_str)
                    rootdoc = etree.ElementTree(layerelem)
            except Exception as e:
                import traceback
                traceback.print_exc()
                logger.error(
                    "Error occurred creating GetCapabilities for %s:%s" %
                    (layer.typename, str(e)))
                rootdoc = None
    if rootdoc is not None:
        capabilities = etree.tostring(
            rootdoc,
            xml_declaration=True,
            encoding='UTF-8',
            pretty_print=True)
        return HttpResponse(capabilities, content_type="text/xml")
    return HttpResponse(status=200)


def server_online(request):
    """
    Returns {success} whenever the LOCAL_GEOSERVER is up and running
    """
    from .helpers import check_geoserver_is_up
    try:
        check_geoserver_is_up()
        return HttpResponse(json.dumps({'online': True}), content_type="application/json")
    except BaseException:
        return HttpResponse(json.dumps({'online': False}), content_type="application/json")
