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
from owslib.etree import etree as dlxml
from os.path import isfile

from urllib.parse import (
    urlsplit,
    urljoin,
    unquote,
    parse_qsl)

from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.shortcuts import render
from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.utils.datastructures import MultiValueDictKeyError
from django.utils.translation import ugettext as _

from guardian.shortcuts import get_objects_for_user

from geonode.base.models import ResourceBase
from geonode.client.hooks import hookset
from geonode.compat import ensure_string
from geonode.base.auth import get_auth_user, get_or_create_token
from geonode.decorators import logged_in_or_basicauth
from geonode.layers.forms import LayerStyleUploadForm
from geonode.layers.models import Dataset, Style
from geonode.layers.views import _resolve_dataset, _PERMISSION_MSG_MODIFY
from geonode.maps.models import Map
from geonode.proxy.views import (
    proxy,
    fetch_response_headers)
from .tasks import geoserver_update_datasets
from geonode.utils import (
    json_response,
    _get_basic_auth_info,
    http_client,
    get_headers,
    get_dataset_workspace)
from geoserver.catalog import FailedRequestError
from geonode.geoserver.signals import (
    gs_catalog,
    geoserver_post_save_local)
from .helpers import (
    get_stores,
    ogc_server_settings,
    extract_name_from_sld,
    set_styles,
    style_update,
    set_dataset_style,
    temp_style_name_regex,
    _stylefilterparams_geowebcache_dataset,
    _invalidate_geowebcache_dataset)

from django.views.decorators.csrf import csrf_exempt

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
    result = geoserver_update_datasets.delay(
        ignore_errors=False, owner=owner, workspace=workspace,
        store=store, filter=filter)
    # Attempt to run task synchronously
    result.get()

    return HttpResponseRedirect(hookset.dataset_list_url())


@login_required
@require_POST
def dataset_style(request, layername):
    layer = _resolve_dataset(
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
            f"Default style for {layer.name} remains {style_name}", status=200)

    # This code assumes without checking
    # that the new default style name is included
    # in the list of possible styles.

    new_style = next(style for style in layer.styles if style.name == style_name)

    # Does this change this in geoserver??
    layer.default_style = new_style
    layer.styles = [
        s for s in layer.styles if s.name != style_name] + [old_default]
    layer.save(notify=True)

    # Invalidate GeoWebCache for the updated resource
    try:
        _stylefilterparams_geowebcache_dataset(layer.alternate)
        _invalidate_geowebcache_dataset(layer.alternate)
    except Exception:
        pass

    return HttpResponse(
        f"Default style for {layer.name} changed to {style_name}", status=200)


@login_required
def dataset_style_upload(request, layername):
    def respond(*args, **kw):
        kw['content_type'] = 'text/html'
        return json_response(*args, **kw)
    form = LayerStyleUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return respond(errors="Please provide an SLD file.")

    data = form.cleaned_data
    layer = _resolve_dataset(
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
                    with open(sld) as sld_file:
                        sld = sld_file.read()
                etree.XML(sld)
        except Exception:
            logger.exception("The uploaded SLD file is not valid XML")
            raise Exception(
                "The uploaded SLD file is not valid XML")

        sld_name = extract_name_from_sld(
            gs_catalog, sld, sld_file=request.FILES['sld'])
    except Exception as e:
        respond(errors=f"The uploaded SLD file is not valid XML: {e}")

    name = data.get('name') or sld_name

    set_dataset_style(layer, data.get('title') or name, sld)

    return respond(
        body={
            'success': True,
            'style': data.get('title') or name,
            'updated': data['update']})


@login_required
def dataset_style_manage(request, layername):
    layer = _resolve_dataset(
        request,
        layername,
        'layers.change_dataset_style',
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
            current_dataset_styles = layer.styles.all()
            dataset_styles = []
            for style in current_dataset_styles:
                sld_title = style.name
                try:
                    if style.sld_title:
                        sld_title = style.sld_title
                except Exception:
                    tb = traceback.format_exc()
                    logger.debug(tb)
                dataset_styles.append((style.name, sld_title))

            # Render the form
            def_sld_name = None  # noqa
            def_sld_title = None  # noqa
            default_style = None
            if layer.default_style:
                def_sld_name = layer.default_style.name  # noqa
                def_sld_title = layer.default_style.name  # noqa
                try:
                    if layer.default_style.sld_title:
                        def_sld_title = layer.default_style.sld_title
                except Exception:
                    tb = traceback.format_exc()
                    logger.debug(tb)
                default_style = (def_sld_name, def_sld_title)

            return render(
                request,
                'datasets/dataset_style_manage.html',
                context={
                    "layer": layer,
                    "gs_styles": gs_styles,
                    "dataset_styles": dataset_styles,
                    "dataset_style_names": [s[0] for s in dataset_styles],
                    "default_style": default_style
                }
            )
        except (FailedRequestError, OSError):
            tb = traceback.format_exc()
            logger.debug(tb)
            msg = (f'Could not connect to geoserver at "{ogc_server_settings.LOCATION}"'
                   f'to manage style information for layer "{layer.name}"')
            logger.debug(msg)
            # If geoserver is not online, return an error
            return render(
                request,
                'datasets/dataset_style_manage.html',
                context={
                    "layer": layer,
                    "error": msg
                }
            )
    elif request.method in ('POST', 'PUT', 'DELETE'):
        try:
            workspace = get_dataset_workspace(layer) or settings.DEFAULT_WORKSPACE
            selected_styles = request.POST.getlist('style-select')
            default_style = request.POST['default_style']

            # Save to GeoServer
            cat = gs_catalog
            try:
                gs_dataset = cat.get_layer(layer.name)
            except Exception:
                gs_dataset = None

            if not gs_dataset:
                gs_dataset = cat.get_layer(layer.alternate)

            if gs_dataset:
                _default_style = cat.get_style(default_style) or \
                    cat.get_style(default_style, workspace=workspace)
                if _default_style:
                    gs_dataset.default_style = _default_style
                elif cat.get_style(default_style, workspace=settings.DEFAULT_WORKSPACE):
                    gs_dataset.default_style = cat.get_style(default_style, workspace=settings.DEFAULT_WORKSPACE)
                styles = []
                for style in selected_styles:
                    _gs_sld = cat.get_style(style) or cat.get_style(style, workspace=workspace)
                    if _gs_sld:
                        styles.append(_gs_sld)
                    elif cat.get_style(style, workspace=settings.DEFAULT_WORKSPACE):
                        styles.append(cat.get_style(style, workspace=settings.DEFAULT_WORKSPACE))
                    else:
                        Style.objects.filter(name=style).delete()
                gs_dataset.styles = styles
                cat.save(gs_dataset)

            # Save to Django
            set_styles(layer, cat)

            # Invalidate GeoWebCache for the updated resource
            try:
                _stylefilterparams_geowebcache_dataset(layer.alternate)
                _invalidate_geowebcache_dataset(layer.alternate)
            except Exception:
                pass

            return HttpResponseRedirect(layer.get_absolute_url())
        except (FailedRequestError, OSError, MultiValueDictKeyError):
            tb = traceback.format_exc()
            logger.debug(tb)
            msg = (f'Error Saving Styles for Dataset "{layer.name}"')
            logger.warn(msg)
            return render(
                request,
                'datasets/dataset_style_manage.html',
                context={
                    "layer": layer,
                    "error": msg
                }
            )


def style_change_check(request, path, style_name=None, access_token=None):
    """
    If the layer has not change_dataset_style permission, return a status of
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
        if not request.user.is_authenticated and not access_token:
            authorized = False
        elif re.match(r'^.*(?<!/rest/)/rest/.*/?styles.*', path):
            # style new/update
            # we will iterate all layers (should be just one if not using GS)
            # to which the posted style is associated
            # and check if the user has change_style_dataset permissions on each
            # of them
            if style_name == 'styles' and 'raw' in request.GET:
                authorized = True
            elif re.match(temp_style_name_regex, style_name):
                authorized = True
            else:
                try:
                    user = request.user
                    if user.is_anonymous and access_token:
                        user = get_auth_user(access_token)
                    if not user or user.is_anonymous:
                        authorized = False
                    else:
                        style = Style.objects.get(name=style_name)
                        for dataset in style.dataset_styles.all():
                            if not user.has_perm('change_dataset_style', obj=dataset):
                                authorized = False
                                break
                            else:
                                authorized = True
                                break
                except Style.DoesNotExist:
                    if request.method != 'POST':
                        logger.warn(f'There is not a style with such a name: {style_name}.')
                except Exception as e:
                    logger.exception(e)
                    authorized = (request.method == 'POST')  # The user is probably trying to create a new style
    return authorized


def check_geoserver_access(request,
                           proxy_path,
                           downstream_path,
                           workspace=None,
                           layername=None,
                           allowed_hosts=[]):
    def strip_prefix(path, prefix):
        if prefix not in path:
            _s_prefix = prefix.split('/', 3)
            _s_path = path.split('/', 3)
            assert _s_prefix[1] == _s_path[1]
            _prefix = f'/{_s_path[1]}/{_s_path[2]}'
        else:
            _prefix = prefix
        assert _prefix in path
        prefix_idx = path.index(_prefix)
        _prefix = path[:prefix_idx] + _prefix
        full_prefix = f"{_prefix}/{layername}/{downstream_path}" if layername else _prefix
        return path[len(full_prefix):]

    path = strip_prefix(request.get_full_path(), proxy_path)

    raw_url = str(
        "".join([ogc_server_settings.LOCATION, downstream_path, path]))

    if settings.DEFAULT_WORKSPACE or workspace:
        ws = (workspace or settings.DEFAULT_WORKSPACE)
        if ws and ws in path:
            # Strip out WS from PATH
            try:
                path = f'/{strip_prefix(path, f"/{ws}:")}'
            except Exception:
                ws = None

        if proxy_path == f'/gs/{settings.DEFAULT_WORKSPACE}' and layername:
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
        re.match(r'/(rest).*$', path, re.IGNORECASE) or
            re.match(r'/(w.*s).*$', path, re.IGNORECASE) or
            re.match(r'/(ows).*$', path, re.IGNORECASE)):
        _url = str("".join([ogc_server_settings.LOCATION, '', path[1:]]))
        raw_url = _url
    url = urlsplit(raw_url)

    if f'{ws}/layers' in path:
        downstream_path = 'rest/layers'
    elif f'{ws}/styles' in path:
        downstream_path = 'rest/styles'

    # Collecting headers and cookies
    headers, access_token = get_headers(request, url, unquote(raw_url), allowed_hosts=allowed_hosts)
    return (raw_url, headers, access_token, downstream_path)


@csrf_exempt
def geoserver_proxy(request,
                    proxy_path,
                    downstream_path,
                    workspace=None,
                    layername=None):
    """
    WARNING: Decorators are applied in the order they appear in the source.
    """
    affected_datasets = None
    allowed_hosts = [urlsplit(ogc_server_settings.public_url).hostname, ]

    raw_url, headers, access_token, downstream_path = check_geoserver_access(
        request,
        proxy_path,
        downstream_path,
        workspace=workspace,
        layername=layername,
        allowed_hosts=allowed_hosts)
    url = urlsplit(raw_url)

    if re.match(r'^.*/rest/', url.path) and request.method in ("POST", "PUT", "DELETE"):
        if re.match(r'^.*(?<!/rest/)/rest/.*/?styles.*', url.path):
            logger.debug(
                f"[geoserver_proxy] Updating Style ---> url {url.geturl()}")
            _style_name, _style_ext = os.path.splitext(os.path.basename(urlsplit(url.geturl()).path))
            _parsed_get_args = dict(parse_qsl(urlsplit(url.geturl()).query))
            if _style_name == 'styles.json' and request.method == "PUT":
                if _parsed_get_args.get('name'):
                    _style_name, _style_ext = os.path.splitext(_parsed_get_args.get('name'))
            else:
                _style_name, _style_ext = os.path.splitext(_style_name)

            if not style_change_check(request, url.path, style_name=_style_name, access_token=access_token):
                return HttpResponse(
                    _("You don't have permissions to change style for this layer"),
                    content_type="text/plain",
                    status=401)
            if _style_name != 'style-check' and (_style_ext == '.json' or _parsed_get_args.get('raw')) and \
                    not re.match(temp_style_name_regex, _style_name):
                affected_datasets = style_update(request, raw_url, workspace)
        elif re.match(r'^.*(?<!/rest/)/rest/.*/?layers.*', url.path):
            logger.debug(f"[geoserver_proxy] Updating Dataset ---> url {url.geturl()}")
            try:
                _dataset_name = os.path.splitext(os.path.basename(request.path))[0]
                _dataset = Dataset.objects.get(name=_dataset_name)
                affected_datasets = [_dataset]
            except Exception:
                logger.warn(f"Could not find any Dataset {os.path.basename(request.path)} on DB")

    kwargs = {'affected_datasets': affected_datasets}
    raw_url = unquote(raw_url)
    timeout = getattr(ogc_server_settings, 'TIMEOUT') or 60
    response = proxy(request, url=raw_url, response_callback=_response_callback,
                     timeout=timeout, allowed_hosts=allowed_hosts,
                     headers=headers, access_token=access_token, **kwargs)
    return response


def _response_callback(**kwargs):
    status = kwargs.get('status')
    content = kwargs.get('content')
    content_type = kwargs.get('content_type')
    response_headers = kwargs.get('response_headers', None)
    content_type_list = ['application/xml', 'text/xml', 'text/plain', 'application/json', 'text/json']

    if content:
        if not content_type:
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            if (re.match(r'^<.+>$', content)):
                content_type = 'application/xml'
            elif (re.match(r'^({|[).+(}|])$', content)):
                content_type = 'application/json'
            else:
                content_type = 'text/plain'

        # Replace Proxy URL
        try:
            if isinstance(content, bytes):
                try:
                    _content = content.decode('UTF-8')
                except UnicodeDecodeError:
                    _content = content
            else:
                _content = content
            if re.findall(f"(?=(\\b{'|'.join(content_type_list)}\\b))", content_type):
                _gn_proxy_url = urljoin(settings.SITEURL, '/gs/')
                content = _content\
                    .replace(ogc_server_settings.LOCATION, _gn_proxy_url)\
                    .replace(ogc_server_settings.PUBLIC_LOCATION, _gn_proxy_url)
                for _ows_endpoint in list(dict.fromkeys(re.findall(rf'{_gn_proxy_url}w\ws', content, re.IGNORECASE))):
                    content = content.replace(_ows_endpoint, f'{_gn_proxy_url}ows')
        except Exception as e:
            logger.exception(e)

    if 'affected_datasets' in kwargs and kwargs['affected_datasets']:
        for layer in kwargs['affected_datasets']:
            geoserver_post_save_local(layer)

    _response = HttpResponse(
        content=content,
        status=status,
        content_type=content_type)
    return fetch_response_headers(_response, response_headers)


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

    if acl_user and acl_user.is_authenticated:
        resp['fullname'] = acl_user.get_full_name()
        resp['email'] = acl_user.email
    return HttpResponse(json.dumps(resp), content_type="application/json")


@logged_in_or_basicauth(realm="GeoNode")
def dataset_acls(request):
    """
    returns json-encoded lists of layer identifiers that
    represent the sets of read-write and read-only layers
    for the currently authenticated user.
    """
    # the dataset_acls view supports basic auth, and a special
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
    resources_readable = get_objects_for_user(
        acl_user, 'view_resourcebase',
        ResourceBase.objects.filter(polymorphic_ctype__model='dataset')).values_list('id', flat=True)
    dataset_writable = get_objects_for_user(
        acl_user, 'change_dataset_data',
        Dataset.objects.all())

    _read = set(
        Dataset.objects.filter(
            id__in=resources_readable).values_list(
            'alternate',
            flat=True))
    _write = set(dataset_writable.values_list('alternate', flat=True))

    read_only = _read ^ _write
    read_write = _read & _write

    result = {
        'rw': list(read_write),
        'ro': list(read_only),
        'name': acl_user.username,
        'is_superuser': acl_user.is_superuser,
        'is_anonymous': acl_user.is_anonymous,
    }
    if acl_user.is_authenticated:
        result['fullname'] = acl_user.get_full_name()
        result['email'] = acl_user.email

    return HttpResponse(json.dumps(result), content_type="application/json")


# capabilities
def get_dataset_capabilities(layer, version='1.3.0', access_token=None, tolerant=False):
    """
    Retrieve a layer-specific GetCapabilities document
    """
    workspace, layername = layer.alternate.split(":") if ":" in layer.alternate else (None, layer.alternate)
    if not layer.remote_service:
        wms_url = f'{ogc_server_settings.LOCATION}{workspace}/{layername}/wms?service=wms&version={version}&request=GetCapabilities'  # noqa
        if access_token:
            wms_url += f'&access_token={access_token}'
    else:
        wms_url = f'{layer.remote_service.service_url}?service=wms&version={version}&request=GetCapabilities'

    _user, _password = ogc_server_settings.credentials
    req, content = http_client.get(wms_url, user=_user)
    getcap = ensure_string(content)
    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
        if tolerant and ('ServiceException' in getcap or req.status_code == 404):
            # WARNING Please make sure to have enabled DJANGO CACHE as per
            # https://docs.djangoproject.com/en/2.0/topics/cache/#filesystem-caching
            wms_url = f'{ogc_server_settings.public_url}{workspace}/ows?service=wms&version={version}&request=GetCapabilities&layers={layer}'  # noqa
            if access_token:
                wms_url += f'&access_token={access_token}'
            req, content = http_client.get(wms_url, user=_user)
            getcap = ensure_string(content)

    if 'ServiceException' in getcap or req.status_code == 404:
        return None
    return getcap.encode('UTF-8')


def format_online_resource(workspace, layer, element, namespaces):
    """
    Replace workspace/layer-specific OnlineResource links with the more
    generic links returned by a site-wide GetCapabilities document
    """
    layerName = element.find('.//wms:Capability/wms:Layer/wms:Layer/wms:Name',
                             namespaces)
    if layerName is None:
        return

    layerName.text = f"{workspace}:{layer}" if workspace else layer
    layerresources = element.findall('.//wms:OnlineResource', namespaces)
    if layerresources is None:
        return

    for resource in layerresources:
        wtf = resource.attrib['{http://www.w3.org/1999/xlink}href']
        replace_string = f"/{workspace}/{layer}" if workspace else f"/{layer}"
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
        dataset_obj = Dataset.objects.get(id=layerid)
        cap_name += dataset_obj.title
        layers = Dataset.objects.filter(id=layerid)
    elif user is not None:
        layers = Dataset.objects.filter(owner__username=user)
        cap_name += user
    elif category is not None:
        layers = Dataset.objects.filter(category__identifier=category)
        cap_name += category
    elif mapid is not None:
        map_obj = Map.objects.get(id=mapid)
        cap_name += map_obj.title
        alternates = []
        for layer in map_obj.maplayers.iterator():
            if layer.local:
                alternates.append(layer.name)
        layers = Dataset.objects.filter(alternate__in=alternates)

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
                layercap = get_dataset_capabilities(layer, access_token=access_token, tolerant=tolerant)
                if layercap is not None:  # 1st one, seed with real GetCapabilities doc
                    try:
                        namespaces = {'wms': 'http://www.opengis.net/wms',
                                      'xlink': 'http://www.w3.org/1999/xlink',
                                      'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}
                        layercap = dlxml.fromstring(layercap)
                        rootdoc = etree.ElementTree(layercap)
                        format_online_resource(workspace, layername, rootdoc, namespaces)
                        service_name = rootdoc.find('.//wms:Service/wms:Name', namespaces)
                        if service_name is not None:
                            service_name.text = cap_name
                        rootdoc = rootdoc.find('.//wms:Capability/wms:Layer/wms:Layer', namespaces)
                    except Exception as e:
                        import traceback
                        traceback.print_exc()
                        logger.error(
                            f"Error occurred creating GetCapabilities for {layer.typename}: {str(e)}")
                        rootdoc = None
                if layercap is None or not len(layercap) or rootdoc is None or not len(rootdoc):
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
                    f"Error occurred creating GetCapabilities for {layer.typename}:{str(e)}")
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
    except Exception:
        return HttpResponse(json.dumps({'online': False}), content_type="application/json")
