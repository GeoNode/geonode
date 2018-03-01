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
import httplib2
from lxml import etree

from httplib import HTTPConnection, HTTPSConnection
from urlparse import urlsplit, urljoin

from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.template.loader import get_template
from django.template import Context
from django.template import RequestContext
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext as _

from guardian.shortcuts import get_objects_for_user

from geonode.base.models import ResourceBase
from geonode.layers.forms import LayerStyleUploadForm
from geonode.layers.models import Layer, Style
from geonode.layers.views import _resolve_layer, _PERMISSION_MSG_MODIFY
from geonode.maps.models import Map
from geonode.geoserver.signals import gs_catalog
from .tasks import geoserver_update_layers
from geonode.utils import json_response, _get_basic_auth_info
from geoserver.catalog import FailedRequestError, ConflictingDataError
from .helpers import (get_stores, ogc_server_settings,
                      extract_name_from_sld, set_styles, style_update,
                      create_gs_thumbnail, _invalidate_geowebcache_layer)

from django_basic_auth import logged_in_or_basicauth

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
    sld_name = None
    try:
        # Check SLD is valid
        sld_name = extract_name_from_sld(
            gs_catalog, sld, sld_file=request.FILES['sld'])
    except Exception as e:
        respond(errors="The uploaded SLD file is not valid XML: {}".format(e))

    name = data.get('name') or sld_name
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
            cat.create_style(
                name,
                sld,
                raw=True,
                workspace=settings.DEFAULT_WORKSPACE)
            layer.styles = layer.styles + \
                [type('style', (object,), {'name': name})]
            cat.save(layer.publishing)
        except ConflictingDataError:
            return respond(errors="""A layer with this name exists. Select
                                     the update option if you want to update.""")
    # Invalidate GeoWebCache for the updated resource
    _invalidate_geowebcache_layer(layer.alternate)
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

            # Ahmed Nour:
            # Get public styles also
            all_available_gs_styles = cat.get_styles(
                settings.DEFAULT_WORKSPACE)
            all_available_gs_styles += cat.get_styles()
            gs_styles = []
            for style in all_available_gs_styles:
                sld_title = style.name
                try:
                    if style.sld_title:
                        sld_title = style.sld_title
                except BaseException:
                    pass
                gs_styles.append((style.name, sld_title))

            current_layer_styles = layer.styles.all()
            layer_styles = []
            for style in current_layer_styles:
                sld_title = style.name
                try:
                    if style.sld_title:
                        sld_title = style.sld_title
                except BaseException:
                    pass
                layer_styles.append((style.name, sld_title))

            # Render the form
            sld_title = layer.default_style.name
            try:
                if layer.default_style.sld_title:
                    sld_title = layer.default_style.sld_title
            except BaseException:
                pass
            default_style = (layer.default_style.name, sld_title)
            return render_to_response(
                'layers/layer_style_manage.html',
                RequestContext(request, {
                    "layer": layer,
                    "gs_styles": gs_styles,
                    "layer_styles": layer_styles,
                    "default_style": default_style
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
            gs_layer.default_style = cat.get_style(default_style, workspace=settings.DEFAULT_WORKSPACE) or \
                cat.get_style(default_style)
            styles = []
            for style in selected_styles:
                styles.append(
                    cat.get_style(
                        style,
                        workspace=settings.DEFAULT_WORKSPACE) or cat.get_style(style))
            gs_layer.styles = styles
            cat.save(gs_layer)

            # Save to Django
            layer = set_styles(layer, cat)
            layer.save()

            # Invalidate GeoWebCache for the updated resource
            _invalidate_geowebcache_layer(layer.alternate)

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
    try:
        layer = _resolve_layer(request, layername)
    except BaseException:
        # Intercept and handle correctly resource not found exception
        return HttpResponse(
            json.dumps({'authorized': False}), content_type="application/json")
    datastore = ogc_server_settings.DATASTORE
    feature_edit = getattr(settings, "GEOGIG_DATASTORE", None) or datastore
    is_admin = False
    is_staff = False
    is_owner = False
    is_manager = False
    if request.user:
        is_admin = request.user.is_superuser if request.user else False
        is_staff = request.user.is_staff if request.user else False
        is_owner = (str(request.user) == str(layer.owner))
        try:
            is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
        except BaseException:
            is_manager = False
    if is_admin or is_staff or is_owner or is_manager or request.user.has_perm(
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
            # and check if the user has change_style_layer permissions on each
            # of them
            style_name = os.path.splitext(request.path)[0].split('/')[-1]
            try:
                style = Style.objects.get(name=style_name)
                for layer in style.layer_styles.all():
                    if not request.user.has_perm(
                            'change_layer_style', obj=layer):
                        authorized = False
            except BaseException:
                authorized = False
                logger.warn(
                    'There is not a style with such a name: %s.' % style_name)
    return authorized


@logged_in_or_basicauth(realm="GeoNode")
def geoserver_proxy(request, proxy_path, downstream_path, workspace=None):

    if not request.user.is_authenticated():
        return HttpResponse(
            "You must be logged in to access GeoServer",
            content_type="text/plain",
            status=401)

    def strip_prefix(path, prefix):
        assert path.startswith(prefix)
        return path[len(prefix):]

    path = strip_prefix(request.get_full_path(), proxy_path)

    access_token = None
    if 'access_token' in request.session:
        access_token = request.session['access_token']

    headers = {}
    affected_layers = None
    cookies = None
    for cook in request.COOKIES:
        name = str(cook)
        value = request.COOKIES.get(name)
        if name == 'csrftoken':
            headers['X-CSRFToken'] = value

        cook = "%s=%s" % (name, value)
        if not cookies:
            cookies = cook
        else:
            cookies = cookies + '; ' + cook

    if cookies:
        if 'JSESSIONID' in request.session and request.session['JSESSIONID']:
            cookies = cookies + '; JSESSIONID=' + \
                request.session['JSESSIONID']
        headers['Cookie'] = cookies

    # TODO: This won't work unless GeoServer is connected to the GeoNode Users' Repo
    #       We would need a specific GroupRoleService
    # if 'HTTP_AUTHORIZATION' in request.META:
    #     auth = request.META.get('HTTP_AUTHORIZATION', request.META.get('HTTP_AUTHORIZATION2'))
    #     if auth:
    #         headers['Authorization'] = auth
    if access_token:
        # TODO: Bearer is currently cutted of by Djano / GeoServer
        if request.method in ("POST", "PUT"):
            if access_token:
                headers['Authorization'] = 'Bearer {}'.format(access_token)
        if access_token and 'access_token' not in path:
            query_separator = '&' if '?' in path else '?'
            path = ('%s%saccess_token=%s' %
                    (path, query_separator, access_token))

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

        if downstream_path in ('rest/styles') and len(request.body) > 0:
            # Lets try
            # http://localhost:8080/geoserver/rest/workspaces/<ws>/styles/<style>.xml
            _url = str("".join([ogc_server_settings.LOCATION,
                                'rest/workspaces/', ws, '/styles',
                                path]))
            raw_url = _url

    if downstream_path in 'ows' and (
        'rest' in path or
            re.match(r'/(w.*s).*$', path, re.IGNORECASE) or
            re.match(r'/(ows).*$', path, re.IGNORECASE)):
        _url = str("".join([ogc_server_settings.LOCATION, '', path[1:]]))
        raw_url = _url

    url = urlsplit(raw_url)
    if url.scheme == 'https':
        conn = HTTPSConnection(url.hostname, url.port)
    else:
        conn = HTTPConnection(url.hostname, url.port)

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]
        # if user is not authorized, we must stop him
        # we need to sync django here and check if some object (styles) can
        # be edited by the user
        # we should remove this geonode dependency calling layers.views straight
        # from GXP, bypassing the proxy
        if downstream_path in ('rest/styles', 'rest/layers',
                               'rest/workspaces') and len(request.body) > 0:
            if not style_change_check(request, downstream_path):
                return HttpResponse(
                    _("You don't have permissions to change style for this layer"),
                    content_type="text/plain",
                    status=401)
            elif downstream_path == 'rest/styles':
                logger.info(
                    "[geoserver_proxy] Updating Style to ---> url %s" %
                    url.path)
                affected_layers = style_update(request, raw_url)

    headers["Accept-encoding"] = 'gzip'
    conn.request(request.method, raw_url, request.body, headers=headers)
    response = conn.getresponse()
    content = response.read()
    status = response.status
    content_type = response.getheader("Content-Type", "text/plain")

    # update thumbnails
    if status == 200 and affected_layers:
        for layer in affected_layers:
            logger.debug(
                'Updating thumbnail for layer with uuid %s' %
                layer.uuid)
            create_gs_thumbnail(layer, True)

    # decompress GZipped responses if not enabled
    if content and response.getheader('Content-Encoding') == 'gzip':
        from StringIO import StringIO
        import gzip
        buf = StringIO(content)
        f = gzip.GzipFile(fileobj=buf)
        content = f.read()

    # Replace Proxy URL
    if content_type in ('application/xml', 'text/xml', 'text/plain'):
        _gn_proxy_url = urljoin(settings.SITEURL, '/gs/')
        content = content\
            .replace(ogc_server_settings.LOCATION, _gn_proxy_url)\
            .replace(ogc_server_settings.PUBLIC_LOCATION, _gn_proxy_url)

    return HttpResponse(
        content=content,
        status=status,
        content_type=content_type)


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
        layers = Layer.objects.filter(alternate__in=list(layers))

        def layer_son(layer):
            return {
                "name": layer.alternate,
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
def get_layer_capabilities(
        workspace, layer, access_token=None, tolerant=False):
    """
    Retrieve a layer-specific GetCapabilities document
    """
    # TODO implement this for 1.3.0 too
    wms_url = '%s%s/%s/wms?service=wms&version=1.1.0&request=GetCapabilities'\
        % (ogc_server_settings.public_url, workspace, layer)
    if access_token:
        wms_url += ('&access_token=%s' % access_token)
    http = httplib2.Http()
    response, getcap = http.request(wms_url)
    # TODO this is to bypass an actual bug of GeoServer 2.12.x
    if tolerant and response.status == 404:
        # WARNING Please make sure to have enabled DJANGO CACHE as per
        # https://docs.djangoproject.com/en/2.0/topics/cache/#filesystem-caching
        wms_url = '%s%s/wms?service=wms&version=1.1.0&request=GetCapabilities&layers=%s'\
            % (ogc_server_settings.public_url, workspace, layer)
        if access_token:
            wms_url += ('&access_token=%s' % access_token)
        response, getcap = http.request(wms_url)
    return getcap


def format_online_resource(workspace, layer, element):
    """
    Replace workspace/layer-specific OnlineResource links with the more
    generic links returned by a site-wide GetCapabilities document
    """
    layerName = element.find('.//Name')
    layerName.text = workspace + ":" + layer
    layerresources = element.findall('.//OnlineResource')
    for resource in layerresources:
        wtf = resource.attrib['{http://www.w3.org/1999/xlink}href']
        resource.attrib['{http://www.w3.org/1999/xlink}href'] = wtf.replace(
            "/" + workspace + "/" + layer, "")


def get_capabilities(request, layerid=None, user=None,
                     mapid=None, category=None, tolerant=False):
    """
    Compile a GetCapabilities document containing public layers
    filtered by layer, user, map, or category
    """

    rootdoc = None
    rootlayerelem = None
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
            access_token = None
            if 'access_token' in request.session:
                access_token = request.session['access_token']
            else:
                access_token = None

            try:
                workspace, layername = layer.alternate.split(":")
                if rootdoc is None:  # 1st one, seed with real GetCapabilities doc
                    try:
                        layercap = get_layer_capabilities(workspace,
                                                          layername,
                                                          access_token=access_token,
                                                          tolerant=tolerant)
                        layercap = etree.fromstring(layercap)
                        rootdoc = etree.ElementTree(layercap)
                        rootlayerelem = rootdoc.find('.//Capability/Layer')
                        format_online_resource(workspace, layername, rootdoc)
                        rootdoc.find('.//Service/Name').text = cap_name
                    except Exception as e:
                        logger.error(
                            "Error occurred creating GetCapabilities for %s: %s" %
                            (layer.typename, str(e)))
                else:
                        # Get the required info from layer model
                    tpl = get_template("geoserver/layer.xml")
                    ctx = Context({
                        'layer': layer,
                        'geoserver_public_url': ogc_server_settings.public_url,
                        'catalogue_url': settings.CATALOGUE['default']['URL'],
                    })
                    gc_str = tpl.render(ctx)
                    gc_str = gc_str.encode("utf-8")
                    layerelem = etree.XML(gc_str)
                    rootlayerelem.append(layerelem)
            except Exception as e:
                logger.error(
                    "Error occurred creating GetCapabilities for %s:%s" %
                    (layer.typename, str(e)))
                pass
    if rootdoc is not None:
        capabilities = etree.tostring(
            rootdoc,
            xml_declaration=True,
            encoding='UTF-8',
            pretty_print=True)
        return HttpResponse(capabilities, content_type="text/xml")
    return HttpResponse(status=200)
