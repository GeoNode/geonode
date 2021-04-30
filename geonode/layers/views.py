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
import re
import os
import sys
import logging
import shutil
import traceback
from types import TracebackType
import decimal
import pickle
from django.db.models import Q
from urllib.parse import quote

from django.http import Http404
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from requests import Request
from itertools import chain
from owslib.wfs import WebFeatureService

from guardian.shortcuts import get_perms, get_objects_for_user
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.conf import settings
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_http_methods

from geonode.thumbs.thumbnails import create_thumbnail

from dal import autocomplete

import json
from django.utils.html import escape
from django.template.defaultfilters import slugify
from django.forms.models import inlineformset_factory
from django.db import IntegrityError, transaction
from django.db.models import F
from django.forms.utils import ErrorList

from geonode.base.auth import get_or_create_token
from geonode.base.forms import CategoryForm, TKeywordForm, BatchPermissionsForm
from geonode.base.views import batch_modify
from geonode.base.models import (
    Thesaurus,
    TopicCategory)
from geonode.base.enumerations import CHARSETS
from geonode.decorators import check_keyword_write_perms

from geonode.layers.forms import (
    LayerForm,
    LayerUploadForm,
    NewLayerUploadForm,
    LayerAttributeForm)
from geonode.layers.models import (
    Layer,
    Attribute,
    UploadSession)
from geonode.layers.utils import (
    file_upload,
    is_raster,
    is_vector,
    surrogate_escape_string)

from geonode.maps.models import Map
from geonode.services.models import Service
from geonode.monitoring import register_event
from geonode.monitoring.models import EventType
from geonode.groups.models import GroupProfile
from geonode.security.views import _perms_info_json
from geonode.people.forms import ProfileForm, PocForm
from geonode.documents.models import get_related_documents
from geonode import geoserver
from geonode.security.utils import get_visible_resources

from geonode.utils import (
    resolve_object,
    default_map_config,
    check_ogc_backend,
    llbbox_to_mercator,
    bbox_to_projection,
    build_social_links,
    GXPLayer,
    GXPMap)

from geonode.geoserver.helpers import (ogc_server_settings,
                                       set_layer_style)
from geonode.base.utils import ManageResourceOwnerPermissions
from geonode.tasks.tasks import set_permissions

from celery.utils.log import get_logger

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    from geonode.geoserver.helpers import gs_catalog

CONTEXT_LOG_FILE = ogc_server_settings.LOG_FILE

logger = logging.getLogger("geonode.layers.views")
celery_logger = get_logger(__name__)

DEFAULT_SEARCH_BATCH_SIZE = 10
MAX_SEARCH_BATCH_SIZE = 25
GENERIC_UPLOAD_ERROR = _(
    "There was an error while attempting to upload your data. \
Please try again, or contact and administrator if the problem continues.")

METADATA_UPLOADED_PRESERVE_ERROR = _("Note: this layer's orginal metadata was \
populated and preserved by importing a metadata XML file. This metadata cannot be edited."
                                     )

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this layer")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this layer.')
_PERMISSION_MSG_MODIFY = _("You are not permitted to modify this layer")
_PERMISSION_MSG_METADATA = _(
    "You are not permitted to modify this layer's metadata")
_PERMISSION_MSG_VIEW = _("You are not permitted to view this layer")


def log_snippet(log_file):
    if not log_file or not os.path.isfile(log_file):
        return f"No log file at {log_file}"

    with open(log_file, "r") as f:
        f.seek(0, 2)  # Seek @ EOF
        fsize = f.tell()  # Get Size
        f.seek(max(fsize - 10024, 0), 0)  # Set pos @ last n chars
        return f.read()


def _resolve_layer(request, alternate, permission='base.view_resourcebase',
                   msg=_PERMISSION_MSG_GENERIC, **kwargs):
    """
    Resolve the layer by the provided typename (which may include service name) and check the optional permission.
    """
    service_typename = alternate.split(":", 1)
    if Service.objects.filter(name=service_typename[0]).exists():
        query = {
            'alternate': service_typename[1]
        }
        if len(service_typename) > 1:
            query['store'] = service_typename[0]
        else:
            query['storeType'] = 'remoteStore'
        return resolve_object(
            request,
            Layer,
            query,
            permission=permission,
            permission_msg=msg,
            **kwargs)
    else:
        if len(service_typename) > 1 and ':' in service_typename[1]:
            if service_typename[0]:
                query = {
                    'store': service_typename[0],
                    'alternate': service_typename[1]
                }
            else:
                query = {
                    'alternate': service_typename[1]
                }
        else:
            query = {'alternate': alternate}
        test_query = Layer.objects.filter(**query)
        if test_query.count() > 1 and test_query.exclude(storeType='remoteStore').count() == 1:
            query = {
                'id': test_query.exclude(storeType='remoteStore').last().id
            }
        elif test_query.count() > 1:
            query = {
                'id': test_query.last().id
            }
        return resolve_object(request,
                              Layer,
                              query,
                              permission=permission,
                              permission_msg=msg,
                              **kwargs)


# Basic Layer Views #


def layer_upload_handle_get(request, template):
    mosaics = Layer.objects.filter(is_mosaic=True).order_by('name')
    ctx = {
        'mosaics': mosaics,
        'charsets': CHARSETS,
        'is_layer': True,
    }
    return render(request, template, context=ctx)


def layer_upload_handle_post(request, template):
    name = None
    form = NewLayerUploadForm(request.POST, request.FILES)
    tempdir = None
    saved_layer = None
    errormsgs = []
    input_charset = None
    out = {'success': False}
    if form.is_valid():
        title = form.cleaned_data["layer_title"]

        # Replace dots in filename - GeoServer REST API upload bug
        # and avoid any other invalid characters.
        # Use the title if possible, otherwise default to the filename
        if title is not None and len(title) > 0:
            name_base = title
        else:
            name_base, __ = os.path.splitext(
                form.cleaned_data["base_file"].name)
            title = slugify(name_base.replace(".", "_"))
        name = slugify(name_base.replace(".", "_"))

        if form.cleaned_data["abstract"] is not None and len(
                form.cleaned_data["abstract"]) > 0:
            abstract = form.cleaned_data["abstract"]
        else:
            abstract = "No abstract provided."

        # charset
        input_charset = form.cleaned_data["charset"]

        try:
            # Moved this inside the try/except block because it can raise
            # exceptions when unicode characters are present.
            # This should be followed up in upstream Django.
            tempdir, base_file = form.write_files()
            if not form.cleaned_data["style_upload_form"]:
                saved_layer = file_upload(
                    base_file,
                    name=name,
                    user=request.user,
                    overwrite=False,
                    charset=input_charset,
                    abstract=abstract,
                    title=title,
                    metadata_uploaded_preserve=form.cleaned_data[
                        "metadata_uploaded_preserve"],
                    metadata_upload_form=form.cleaned_data["metadata_upload_form"])
            else:
                saved_layer = Layer.objects.get(alternate=title)
                if not saved_layer:
                    msg = 'Failed to process. Could not find matching layer.'
                    raise Exception(msg)
                with open(base_file) as sld_file:
                    sld = sld_file.read()
                set_layer_style(saved_layer, title, base_file, sld)
            out['success'] = True
        except Exception as e:
            exception_type, error, tb = sys.exc_info()
            logger.exception(e)
            out['success'] = False
            out['errormsgs'] = _('Failed to upload the layer')
            try:
                out['errors'] = ''.join(error)
            except Exception:
                try:
                    out['errors'] = str(error)
                except Exception:
                    try:
                        tb = traceback.format_exc()
                        out['errors'] = tb
                    except Exception:
                        pass

            # Assign the error message to the latest UploadSession from
            # that user.
            latest_uploads = UploadSession.objects.filter(
                user=request.user).order_by('-date')
            if latest_uploads.count() > 0:
                upload_session = latest_uploads.first()
                # Ref issue #4232
                if not isinstance(error, TracebackType):
                    try:
                        upload_session.error = pickle.dumps(error).decode("utf-8", "replace")
                    except Exception:
                        err_msg = 'The error could not be parsed'
                        upload_session.error = err_msg
                        logger.error("TypeError: can't pickle traceback objects")
                else:
                    err_msg = 'The error could not be parsed'
                    upload_session.error = err_msg
                    logger.error("TypeError: can't pickle traceback objects")
                try:
                    upload_session.traceback = traceback.format_exc(tb)
                except TypeError:
                    upload_session.traceback = traceback.format_tb(tb)
                upload_session.context = log_snippet(CONTEXT_LOG_FILE)
                try:
                    upload_session.save()
                    out['traceback'] = upload_session.traceback
                    out['context'] = upload_session.context
                    out['upload_session'] = upload_session.id
                except Exception as e:
                    logger.debug(e)
            else:
                # Prevent calls to None
                if saved_layer:
                    out['success'] = True
                    if hasattr(saved_layer, 'info'):
                        out['info'] = saved_layer.info
                    out['url'] = reverse(
                        'layer_detail', args=[
                            saved_layer.service_typename])
                    if hasattr(saved_layer, 'bbox_string'):
                        out['bbox'] = saved_layer.bbox_string
                    if hasattr(saved_layer, 'srid'):
                        out['crs'] = {
                            'type': 'name',
                            'properties': saved_layer.srid
                        }
                    out['ogc_backend'] = settings.OGC_SERVER['default']['BACKEND']
                    upload_session = saved_layer.upload_session
                    if upload_session:
                        upload_session.processed = True
                        upload_session.save()
                    permissions = form.cleaned_data["permissions"]
                    if permissions is not None and len(permissions.keys()) > 0:
                        saved_layer.set_permissions(permissions)
                    saved_layer.handle_moderated_uploads()
        finally:
            if tempdir is not None:
                shutil.rmtree(tempdir)
    else:
        for e in form.errors.values():
            errormsgs.extend([escape(v) for v in e])
        out['errors'] = form.errors
        out['errormsgs'] = errormsgs
    if out['success']:
        out['status'] = 'finished'
        out['url'] = saved_layer.get_absolute_url()
        out['bbox'] = saved_layer.bbox_string
        out['crs'] = {
            'type': 'name',
            'properties': saved_layer.srid
        }
        out['ogc_backend'] = settings.OGC_SERVER['default']['BACKEND']
        upload_session = saved_layer.upload_session
        if upload_session:
            upload_session.processed = True
            upload_session.save()
        status_code = 200
        register_event(request, 'upload', saved_layer)
    else:
        status_code = 400

    # null-safe charset
    layer_charset = 'UTF-8'
    if saved_layer:
        layer_charset = getattr(saved_layer, 'charset', layer_charset)
    elif input_charset and 'undefined' not in input_charset:
        layer_charset = input_charset

    _keys = ['info', 'errors']
    for _k in _keys:
        if _k in out:
            if isinstance(out[_k], str):
                out[_k] = surrogate_escape_string(out[_k], layer_charset)
            elif isinstance(out[_k], dict):
                for key, value in out[_k].copy().items():
                    try:
                        item = out[_k][key]
                        # Ref issue #4241
                        if isinstance(item, ErrorList):
                            out[_k][key] = item.as_text().encode(
                                layer_charset, 'surrogateescape').decode('utf-8', 'surrogateescape')
                        else:
                            out[_k][key] = surrogate_escape_string(item, layer_charset)
                        out[_k][surrogate_escape_string(key, layer_charset)] = out[_k].pop(key)
                    except Exception as e:
                        logger.exception(e)

    return HttpResponse(
        json.dumps(out),
        content_type='application/json',
        status=status_code)


@login_required
def layer_upload(request, template='upload/layer_upload.html'):
    if request.method == 'GET':
        return layer_upload_handle_get(request, template)
    elif request.method == 'POST':
        return layer_upload_handle_post(request, template)


def layer_detail(request, layername, template='layers/layer_detail.html'):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    permission_manager = ManageResourceOwnerPermissions(layer)
    permission_manager.set_owner_permissions_according_to_workflow()

    # Add metadata_author or poc if missing
    layer.add_missing_metadata_author_or_poc()

    def decimal_encode(bbox):
        _bbox = []
        for o in [float(coord) for coord in bbox]:
            if isinstance(o, decimal.Decimal):
                o = (str(o) for o in [o])
            _bbox.append(o)
        return [_bbox[0], _bbox[2], _bbox[1], _bbox[3]]

    def sld_definition(style):
        _sld = {
            "title": style.sld_title or style.name,
            "legend": {
                "height": "40",
                "width": "22",
                "href": f"{layer.ows_url}?service=wms&request=GetLegendGraphic&format=image%2Fpng&width=20&height=20&layer={quote(layer.service_typename, safe='')}",
                "format": "image/png"
            },
            "name": style.name
        }
        return _sld

    # assert False, str(layer_bbox)
    config = layer.attribute_config()
    if hasattr(layer, 'srid'):
        config['crs'] = {
            'type': 'name',
            'properties': layer.srid
        }
    # Add required parameters for GXP lazy-loading
    layer_bbox = layer.bbox[0:4]
    # Must be in the form xmin, ymin, xmax, ymax
    bbox = [
        float(layer_bbox[0]), float(layer_bbox[2]),
        float(layer_bbox[1]), float(layer_bbox[3])
    ]

    # Add required parameters for GXP lazy-loading
    attribution = f"{layer.owner.first_name} {layer.owner.last_name}" if layer.owner.first_name or layer.owner.last_name else str(
        layer.owner)
    srs = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857')
    srs_srid = int(srs.split(":")[1]) if srs != "EPSG:900913" else 3857
    config["attribution"] = f"<span class='gx-attribution-title'>{attribution}</span>"
    config["format"] = getattr(
        settings, 'DEFAULT_LAYER_FORMAT', 'image/png')
    config["title"] = layer.title
    config["wrapDateLine"] = True
    config["visibility"] = True
    config["srs"] = srs
    config["bbox"] = bbox_to_projection([float(coord) for coord in layer_bbox] + [layer.srid, ],
                                        target_srid=int(srs.split(":")[1]))[:4]

    config["capability"] = {
        "abstract": layer.abstract,
        "store": layer.store,
        "name": layer.alternate,
        "title": layer.title,
        "style": '',
        "queryable": True,
        "storeType": layer.storeType,
        "bbox": {
            layer.srid: {
                "srs": layer.srid,
                "bbox": decimal_encode(bbox)
            },
            srs: {
                "srs": srs,
                "bbox": bbox_to_projection([float(coord) for coord in layer_bbox] + [layer.srid, ],
                                           target_srid=srs_srid)[:4]
            },
            "EPSG:4326": {
                "srs": "EPSG:4326",
                "bbox": decimal_encode(bbox) if layer.srid == 'EPSG:4326' else
                bbox_to_projection(
                    [float(coord) for coord in layer_bbox] + [layer.srid, ], target_srid=4326)[:4]
            },
            "EPSG:900913": {
                "srs": "EPSG:900913",
                "bbox": decimal_encode(bbox) if layer.srid == 'EPSG:900913' else
                bbox_to_projection(
                    [float(coord) for coord in layer_bbox] + [layer.srid, ], target_srid=3857)[:4]
            }
        },
        "srs": {
            srs: True
        },
        "formats": ["image/png", "application/atom xml", "application/atom+xml", "application/json;type=utfgrid",
                    "application/openlayers", "application/pdf", "application/rss xml", "application/rss+xml",
                    "application/vnd.google-earth.kml", "application/vnd.google-earth.kml xml",
                    "application/vnd.google-earth.kml+xml", "application/vnd.google-earth.kml+xml;mode=networklink",
                    "application/vnd.google-earth.kmz", "application/vnd.google-earth.kmz xml",
                    "application/vnd.google-earth.kmz+xml", "application/vnd.google-earth.kmz;mode=networklink",
                    "atom", "image/geotiff", "image/geotiff8", "image/gif", "image/gif;subtype=animated",
                    "image/jpeg", "image/png8", "image/png; mode=8bit", "image/svg", "image/svg xml",
                    "image/svg+xml", "image/tiff", "image/tiff8", "image/vnd.jpeg-png",
                    "kml", "kmz", "openlayers", "rss", "text/html; subtype=openlayers", "utfgrid"],
        "attribution": {
            "title": attribution
        },
        "infoFormats": ["text/plain", "application/vnd.ogc.gml", "text/xml", "application/vnd.ogc.gml/3.1.1",
                        "text/xml; subtype=gml/3.1.1", "text/html", "application/json"],
        "styles": [sld_definition(s) for s in layer.styles.all()],
        "prefix": layer.alternate.split(":")[0] if ":" in layer.alternate else "",
        "keywords": [k.name for k in layer.keywords.all()] if layer.keywords else [],
        "llbbox": decimal_encode(bbox) if layer.srid == 'EPSG:4326' else
        bbox_to_projection(
            [float(coord) for coord in layer_bbox] + [layer.srid, ], target_srid=4326)[:4]
    }

    granules = None
    all_times = None
    all_granules = None
    filter = None
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        if layer.has_time:
            from geonode.geoserver.views import get_capabilities
            # WARNING Please make sure to have enabled DJANGO CACHE as per
            # https://docs.djangoproject.com/en/2.0/topics/cache/#filesystem-caching
            wms_capabilities_resp = get_capabilities(
                request, layer.id, tolerant=True)
            if wms_capabilities_resp.status_code >= 200 and wms_capabilities_resp.status_code < 400:
                wms_capabilities = wms_capabilities_resp.getvalue()
                if wms_capabilities:
                    from defusedxml import lxml as dlxml
                    namespaces = {'wms': 'http://www.opengis.net/wms',
                                  'xlink': 'http://www.w3.org/1999/xlink',
                                  'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

                    e = dlxml.fromstring(wms_capabilities)
                    for atype in e.findall(
                            f"./[wms:Name='{layer.alternate}']/wms:Dimension[@name='time']", namespaces):
                        dim_name = atype.get('name')
                        if dim_name:
                            dim_name = str(dim_name).lower()
                            if dim_name == 'time':
                                dim_values = atype.text
                                if dim_values:
                                    all_times = dim_values.split(",")
                                    break
            if all_times:
                config["capability"]["dimensions"] = {
                    "time": {
                        "name": "time",
                        "units": "ISO8601",
                        "unitsymbol": None,
                        "nearestVal": False,
                        "multipleVal": False,
                        "current": False,
                        "default": "current",
                        "values": all_times
                    }
                }
        if layer.is_mosaic:
            try:
                cat = gs_catalog
                cat._cache.clear()
                store = cat.get_store(layer.name)
                coverages = cat.mosaic_coverages(store)
                try:
                    if request.GET["filter"]:
                        filter = request.GET["filter"]
                except Exception:
                    pass

                offset = 10 * (request.page - 1)
                granules = cat.mosaic_granules(
                    coverages['coverages']['coverage'][0]['name'],
                    store,
                    limit=10,
                    offset=offset,
                    filter=filter)
                all_granules = cat.mosaic_granules(
                    coverages['coverages']['coverage'][0]['name'], store, filter=filter)
            except Exception:
                granules = {"features": []}
                all_granules = {"features": []}

    # Call this first in order to be sure "perms_list" is correct
    permissions_json = _perms_info_json(layer)

    perms_list = get_perms(
        request.user,
        layer.get_self_resource()) + get_perms(request.user, layer)

    group = None
    if layer.group:
        try:
            group = GroupProfile.objects.get(slug=layer.group.name)
        except GroupProfile.DoesNotExist:
            group = None

    show_popup = False
    if 'show_popup' in request.GET and request.GET["show_popup"]:
        show_popup = True

    if layer.storeType == "remoteStore":
        service = layer.remote_service
        source_params = {}
        if service.type in ('REST_MAP', 'REST_IMG'):
            source_params = {
                "ptype": service.ptype,
                "remote": True,
                "url": service.service_url,
                "name": service.name,
                "title": f"[R] {service.title}"}
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params)
        )
    else:
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config)
        )
    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    layer.view_count_up(request.user)
    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(
        sender=Layer,
        projection=getattr(
            settings,
            'DEFAULT_MAP_CRS',
            'EPSG:3857'))
    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config(request)[1] if la.ows_url is None]

    metadata = layer.link_set.metadata().filter(
        name__in=settings.DOWNLOAD_FORMATS_METADATA)

    access_token = None
    if request and request.user:
        access_token = get_or_create_token(request.user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token
        else:
            access_token = None

    context_dict = {
        'access_token': access_token,
        'resource': layer,
        'group': group,
        'perms_list': perms_list,
        "permissions_json": permissions_json,
        "documents": get_related_documents(layer),
        "metadata": metadata,
        "is_layer": True,
        "wps_enabled": settings.OGC_SERVER['default']['WPS_ENABLED'],
        "granules": granules,
        "all_granules": all_granules,
        "all_times": all_times,
        "show_popup": show_popup,
        "filter": filter,
        "storeType": layer.storeType,
        "online": (layer.remote_service.probe == 200) if layer.storeType == "remoteStore" else True,
        "processed": layer.processed
    }

    context_dict["viewer"] = json.dumps(map_obj.viewer_json(
        request, * (NON_WMS_BASE_LAYERS + [maplayer])))
    context_dict["preview"] = getattr(
        settings,
        'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
        'mapstore')
    context_dict["crs"] = getattr(
        settings,
        'DEFAULT_MAP_CRS',
        'EPSG:3857')

    if layer.storeType == 'dataStore':
        links = layer.link_set.download().filter(
            Q(name__in=settings.DOWNLOAD_FORMATS_VECTOR) |
            Q(link_type='original'))
    else:
        links = layer.link_set.download().filter(
            Q(name__in=settings.DOWNLOAD_FORMATS_RASTER) |
            Q(link_type='original'))
    links_view = [item for item in links if
                  item.link_type == 'image']
    links_download = [item for item in links if item.link_type in ('data', 'original')]
    for item in links_view:
        if item.url and access_token and 'access_token' not in item.url:
            params = {'access_token': access_token}
            item.url = Request('GET', item.url, params=params).prepare().url
    for item in links_download:
        if item.url and access_token and 'access_token' not in item.url:
            params = {'access_token': access_token}
            item.url = Request('GET', item.url, params=params).prepare().url
    if request.user.has_perm('view_resourcebase', layer.get_self_resource()):
        context_dict["links"] = links_view
    if request.user.has_perm('download_resourcebase', layer.get_self_resource()):
        context_dict["links_download"] = links_download
    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, layer)
    layers_names = layer.alternate
    context_dict["layer_name"] = json.dumps(layers_names)
    try:
        # get type of layer (raster or vector)
        if layer.storeType == 'coverageStore':
            context_dict["layer_type"] = "raster"
        elif layer.storeType == 'dataStore':
            if layer.has_time:
                context_dict["layer_type"] = "vector_time"
            else:
                context_dict["layer_type"] = "vector"
    except Exception:
        logger.error(
            "Possible error with OWSLib. Turning all available properties to string")
    # maps owned by user needed to fill the "add to existing map section" in template
    if request.user.is_authenticated:
        context_dict["maps"] = Map.objects.filter(owner=request.user)
        if getattr(settings, 'FAVORITE_ENABLED', False):
            from geonode.favorite.utils import get_favorite_info
            context_dict["favorite_info"] = get_favorite_info(request.user, layer)

    if request.user.is_authenticated and (request.user.is_superuser or "change_resourcebase_permissions" in perms_list):
        context_dict['users'] = [user for user in get_user_model().objects.all().exclude(
            id=request.user.id).exclude(is_superuser=True).order_by('username')]
        if request.user.is_superuser:
            context_dict['groups'] = [group for group in GroupProfile.objects.all()]
        else:
            context_dict['groups'] = [group for group in request.user.group_list_all()]

    register_event(request, 'view', layer)
    context_dict['map_layers'] = [map_layer for map_layer in layer.maps() if
                                  request.user.has_perm('view_resourcebase', map_layer.map.get_self_resource())]
    return TemplateResponse(
        request, template, context=context_dict)


# Loads the data using the OWS lib when the "Do you want to filter it"
# button is clicked.
def load_layer_data(request, template='layers/layer_detail.html'):
    context_dict = {}
    data_dict = json.loads(request.POST.get('json_data'))
    layername = data_dict['layer_name']
    filtered_attributes = ''
    if not isinstance(data_dict['filtered_attributes'], str):
        filtered_attributes = [x for x in data_dict['filtered_attributes'] if '/load_layer_data' not in x]
    name = layername if ':' not in layername else layername.split(':')[1]
    location = "{location}{service}".format(** {
        'location': settings.OGC_SERVER['default']['LOCATION'],
        'service': 'wms',
    })
    headers = {}
    if request and 'access_token' in request.session:
        access_token = request.session['access_token']
        headers['Authorization'] = f'Bearer {access_token}'

    try:
        wfs = WebFeatureService(
            location,
            version='1.1.0',
            headers=headers
        )
        response = wfs.getfeature(
            typename=name,
            propertyname=filtered_attributes,
            outputFormat='application/json')
        x = response.read()
        x = json.loads(x)
        features_response = json.dumps(x)
        decoded = json.loads(features_response)
        decoded_features = decoded['features']
        properties = {}
        for key in decoded_features[0]['properties']:
            properties[key] = []

        # loop the dictionary based on the values on the list and add the properties
        # in the dictionary (if doesn't exist) together with the value
        from collections.abc import Iterable
        for i in range(len(decoded_features)):
            for key, value in decoded_features[i]['properties'].items():
                if value != '' and isinstance(value, (str, int, float)) and (
                        (isinstance(value, Iterable) and '/load_layer_data' not in value) or value):
                    properties[key].append(value)

        for key in properties:
            properties[key] = list(set(properties[key]))
            properties[key].sort()

        context_dict["feature_properties"] = properties
    except Exception:
        traceback.print_exc()
        logger.error("Possible error with OWSLib.")
    return HttpResponse(json.dumps(context_dict),
                        content_type="application/json")


def layer_feature_catalogue(
        request,
        layername,
        template='../../catalogue/templates/catalogue/feature_catalogue.xml'):
    try:
        layer = _resolve_layer(request, layername)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if layer.storeType != 'dataStore':
        out = {
            'success': False,
            'errors': 'layer is not a feature type'
        }
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=400)

    attributes = []

    for attrset in layer.attribute_set.order_by('display_order'):
        attr = {
            'name': attrset.attribute,
            'type': attrset.attribute_type
        }
        attributes.append(attr)

    context_dict = {
        'layer': layer,
        'attributes': attributes,
        'metadata': settings.PYCSW['CONFIGURATION']['metadata:main']
    }
    register_event(request, 'view', layer)
    return render(
        request,
        template,
        context=context_dict,
        content_type='application/xml')


@login_required
@check_keyword_write_perms
def layer_metadata(
        request,
        layername,
        template='layers/layer_metadata.html',
        ajax=True):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'base.change_resourcebase_metadata',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    layer_attribute_set = inlineformset_factory(
        Layer,
        Attribute,
        extra=0,
        form=LayerAttributeForm,
    )
    current_keywords = [keyword.name for keyword in layer.keywords.all()]
    topic_category = layer.category

    # Add metadata_author or poc if missing
    layer.add_missing_metadata_author_or_poc()

    poc = layer.poc
    metadata_author = layer.metadata_author

    # assert False, str(layer_bbox)
    config = layer.attribute_config()

    # Add required parameters for GXP lazy-loading
    layer_bbox = layer.bbox
    bbox = [float(coord) for coord in list(layer_bbox[0:4])]
    if hasattr(layer, 'srid'):
        config['crs'] = {
            'type': 'name',
            'properties': layer.srid
        }
    config["srs"] = getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857')
    config["bbox"] = bbox if config["srs"] != 'EPSG:3857' \
        else llbbox_to_mercator([float(coord) for coord in bbox])
    config["title"] = layer.title
    config["queryable"] = True

    if layer.storeType == "remoteStore":
        service = layer.remote_service
        source_params = {}
        if service.type in ('REST_MAP', 'REST_IMG'):
            source_params = {
                "ptype": service.ptype,
                "remote": True,
                "url": service.service_url,
                "name": service.name,
                "title": f"[R] {service.title}"}
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config),
            source_params=json.dumps(source_params)
        )
    else:
        maplayer = GXPLayer(
            name=layer.alternate,
            ows_url=layer.ows_url,
            layer_params=json.dumps(config))

    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != layer.owner and not request.user.is_superuser:
        Layer.objects.filter(
            id=layer.id).update(popular_count=F('popular_count') + 1)

    # center/zoom don't matter; the viewer will center on the layer bounds
    map_obj = GXPMap(
        projection=getattr(
            settings,
            'DEFAULT_MAP_CRS',
            'EPSG:3857'))

    NON_WMS_BASE_LAYERS = [
        la for la in default_map_config(request)[1] if la.ows_url is None]

    if request.method == "POST":
        if layer.metadata_uploaded_preserve:  # layer metadata cannot be edited
            out = {
                'success': False,
                'errors': METADATA_UPLOADED_PRESERVE_ERROR
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)

        layer_form = LayerForm(request.POST, instance=layer, prefix="resource")
        if not layer_form.is_valid():
            logger.error(f"Layer Metadata form is not valid: {layer_form.errors}")
            out = {
                'success': False,
                'errors': [
                    re.sub(re.compile('<.*?>'), '', str(err)) for err in layer_form.errors]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
        attribute_form = layer_attribute_set(
            request.POST,
            instance=layer,
            prefix="layer_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))
        if not attribute_form.is_valid():
            logger.error(f"Layer Attributes form is not valid: {attribute_form.errors}")
            out = {
                'success': False,
                'errors': [
                    re.sub(re.compile('<.*?>'), '', str(err)) for err in attribute_form.errors]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
        category_form = CategoryForm(request.POST, prefix="category_choice_field", initial=int(
            request.POST["category_choice_field"]) if "category_choice_field" in request.POST and
            request.POST["category_choice_field"] else None)
        if not category_form.is_valid():
            logger.error(f"Layer Category form is not valid: {category_form.errors}")
            out = {
                'success': False,
                'errors': [
                    re.sub(re.compile('<.*?>'), '', str(err)) for err in category_form.errors]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
        tkeywords_form = TKeywordForm(request.POST)
        #  set initial values for thesaurus form
        if not tkeywords_form.is_valid():
            logger.error(f"Layer Thesauri Keywords form is not valid: {tkeywords_form.errors}")
            out = {
                'success': False,
                'errors': [
                    re.sub(re.compile('<.*?>'), '', str(err)) for err in tkeywords_form.errors]
            }
            return HttpResponse(
                json.dumps(out),
                content_type='application/json',
                status=400)
    else:
        layer_form = LayerForm(instance=layer, prefix="resource")
        layer_form.disable_keywords_widget_for_non_superuser(request.user)
        attribute_form = layer_attribute_set(
            instance=layer,
            prefix="layer_attribute_set",
            queryset=Attribute.objects.order_by('display_order'))
        category_form = CategoryForm(
            prefix="category_choice_field",
            initial=topic_category.id if topic_category else None)

        # Keywords from THESAURUS management
        layer_tkeywords = layer.tkeywords.all()
        tkeywords_list = ''
        lang = 'en'  # TODO: use user's language
        if layer_tkeywords and len(layer_tkeywords) > 0:
            tkeywords_ids = layer_tkeywords.values_list('id', flat=True)
            if hasattr(settings, 'THESAURUS') and settings.THESAURUS:
                el = settings.THESAURUS
                thesaurus_name = el['name']
                try:
                    t = Thesaurus.objects.get(identifier=thesaurus_name)
                    for tk in t.thesaurus.filter(pk__in=tkeywords_ids):
                        tkl = tk.keyword.filter(lang=lang)
                        if len(tkl) > 0:
                            tkl_ids = ",".join(
                                map(str, tkl.values_list('id', flat=True)))
                            tkeywords_list += f",{tkl_ids}" if len(
                                tkeywords_list) > 0 else tkl_ids
                except Exception:
                    tb = traceback.format_exc()
                    logger.error(tb)
        tkeywords_form = TKeywordForm(instance=layer)
    if request.method == "POST" and layer_form.is_valid() and attribute_form.is_valid(
    ) and category_form.is_valid():
        new_poc = layer_form.cleaned_data['poc']
        new_author = layer_form.cleaned_data['metadata_author']

        if new_poc is None:
            if poc is None:
                poc_form = ProfileForm(
                    request.POST,
                    prefix="poc",
                    instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.is_valid():
                if len(poc_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = poc_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set a point of contact for this resource'))
                    poc = None
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author is None:
                author_form = ProfileForm(request.POST, prefix="author",
                                          instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.is_valid():
                if len(author_form.cleaned_data['profile']) == 0:
                    # FIXME use form.add_error in django > 1.7
                    errors = author_form._errors.setdefault(
                        'profile', ErrorList())
                    errors.append(
                        _('You must set an author for this resource'))
                    metadata_author = None
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        new_category = None
        if category_form and 'category_choice_field' in category_form.cleaned_data and\
                category_form.cleaned_data['category_choice_field']:
            new_category = TopicCategory.objects.get(
                id=int(category_form.cleaned_data['category_choice_field']))

        for form in attribute_form.cleaned_data:
            la = Attribute.objects.get(id=int(form['id'].id))
            la.description = form["description"]
            la.attribute_label = form["attribute_label"]
            la.visible = form["visible"]
            la.display_order = form["display_order"]
            la.featureinfo_type = form["featureinfo_type"]
            la.save()

        if new_poc is not None or new_author is not None:
            if new_poc is not None:
                layer.poc = new_poc
            if new_author is not None:
                layer.metadata_author = new_author

        new_keywords = current_keywords if request.keyword_readonly else layer_form.cleaned_data['keywords']
        new_regions = [x.strip() for x in layer_form.cleaned_data['regions']]

        layer.keywords.clear()
        if new_keywords:
            layer.keywords.add(*new_keywords)
        layer.regions.clear()
        if new_regions:
            layer.regions.add(*new_regions)
        layer.category = new_category

        up_sessions = UploadSession.objects.filter(layer=layer)
        if up_sessions.count() > 0 and up_sessions[0].user != layer.owner:
            up_sessions.update(user=layer.owner)

        register_event(request, EventType.EVENT_CHANGE_METADATA, layer)
        if not ajax:
            return HttpResponseRedirect(
                reverse(
                    'layer_detail',
                    args=(
                        layer.service_typename,
                    )))

        message = layer.alternate

        try:
            if not tkeywords_form.is_valid():
                return HttpResponse(json.dumps({'message': "Invalid thesaurus keywords"}, status_code=400))

            thesaurus_setting = getattr(settings, 'THESAURUS', None)
            if thesaurus_setting:
                tkeywords_data = tkeywords_form.cleaned_data['tkeywords']
                tkeywords_data = tkeywords_data.filter(
                    thesaurus__identifier=thesaurus_setting['name']
                )
                layer.tkeywords.set(tkeywords_data)
            elif Thesaurus.objects.all().exists():
                fields = tkeywords_form.cleaned_data
                layer.tkeywords.set(tkeywords_form.cleanx(fields))

        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

        layer.save(notify=True)
        return HttpResponse(json.dumps({'message': message}))

    if settings.ADMIN_MODERATE_UPLOADS:
        if not request.user.is_superuser:
            can_change_metadata = request.user.has_perm(
                'change_resourcebase_metadata',
                layer.get_self_resource())
            try:
                is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
            except Exception:
                is_manager = False

            if not is_manager or not can_change_metadata:
                if settings.RESOURCE_PUBLISHING:
                    layer_form.fields['is_published'].widget.attrs.update(
                        {'disabled': 'true'})
                layer_form.fields['is_approved'].widget.attrs.update(
                    {'disabled': 'true'})

    if poc is not None:
        layer_form.fields['poc'].initial = poc.id
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = True
    else:
        poc_form = ProfileForm(prefix="poc")
        poc_form.hidden = False

    if metadata_author is not None:
        layer_form.fields['metadata_author'].initial = metadata_author.id
        author_form = ProfileForm(prefix="author")
        author_form.hidden = True
    else:
        author_form = ProfileForm(prefix="author")
        author_form.hidden = False

    viewer = json.dumps(map_obj.viewer_json(
        request, * (NON_WMS_BASE_LAYERS + [maplayer])))

    metadata_author_groups = []
    if request.user.is_superuser or request.user.is_staff:
        metadata_author_groups = GroupProfile.objects.all()
    else:
        try:
            all_metadata_author_groups = chain(
                request.user.group_list_all().distinct(),
                GroupProfile.objects.exclude(access="private"))
        except Exception:
            all_metadata_author_groups = GroupProfile.objects.exclude(
                access="private")
        [metadata_author_groups.append(item) for item in all_metadata_author_groups
            if item not in metadata_author_groups]

    register_event(request, 'view_metadata', layer)
    return render(request, template, context={
        "resource": layer,
        "layer": layer,
        "layer_form": layer_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "attribute_form": attribute_form,
        "category_form": category_form,
        "tkeywords_form": tkeywords_form,
        "viewer": viewer,
        "preview": getattr(settings, 'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY', 'mapstore'),
        "crs": getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857'),
        "metadataxsl": getattr(settings, 'GEONODE_CATALOGUE_METADATA_XSL', True),
        "freetext_readonly": getattr(
            settings,
            'FREETEXT_KEYWORDS_READONLY',
            False),
        "metadata_author_groups": metadata_author_groups,
        "TOPICCATEGORY_MANDATORY": getattr(settings, 'TOPICCATEGORY_MANDATORY', False),
        "GROUP_MANDATORY_RESOURCES": getattr(settings, 'GROUP_MANDATORY_RESOURCES', False),
    })


@login_required
def layer_metadata_advanced(request, layername):
    return layer_metadata(
        request,
        layername,
        template='layers/layer_metadata_advanced.html')


@login_required
def layer_change_poc(request, ids, template='layers/layer_change_poc.html'):
    layers = Layer.objects.filter(id__in=ids.split('_'))

    if request.method == 'POST':
        form = PocForm(request.POST)
        if form.is_valid():
            for layer in layers:
                layer.poc = form.cleaned_data['contact']
                layer.save()

            # Process the data in form.cleaned_data
            # ...
            # Redirect after POST
            return HttpResponseRedirect('/admin/maps/layer')
    else:
        form = PocForm()  # An unbound form
    return render(
        request, template, context={'layers': layers, 'form': form})


@login_required
def layer_replace(request, layername, template='layers/layer_replace.html'):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'base.change_resourcebase',
            _PERMISSION_MSG_MODIFY)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if request.method == 'GET':
        ctx = {
            'charsets': CHARSETS,
            'resource': layer,
            'is_featuretype': layer.is_vector(),
            'is_layer': True,
        }
        return render(request, template, context=ctx)
    elif request.method == 'POST':
        form = LayerUploadForm(request.POST, request.FILES)
        tempdir = None
        out = {}

        if form.is_valid():
            try:
                tempdir, base_file = form.write_files()
                if layer.is_vector() and is_raster(base_file):
                    out['success'] = False
                    out['errors'] = _(
                        "You are attempting to replace a vector layer with a raster.")
                elif (not layer.is_vector()) and is_vector(base_file):
                    out['success'] = False
                    out['errors'] = _(
                        "You are attempting to replace a raster layer with a vector.")
                else:
                    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                        out['ogc_backend'] = geoserver.BACKEND_PACKAGE

                    saved_layer = file_upload(
                        base_file,
                        layer=layer,
                        title=layer.title,
                        abstract=layer.abstract,
                        is_approved=layer.is_approved,
                        is_published=layer.is_published,
                        name=layer.name,
                        user=layer.owner,
                        license=layer.license.name if layer.license else None,
                        category=layer.category,
                        keywords=list(layer.keywords.all()),
                        regions=list(layer.regions.values_list('name', flat=True)),
                        overwrite=True,
                        charset=form.cleaned_data["charset"],
                    )

                    upload_session = saved_layer.upload_session
                    if upload_session:
                        upload_session.processed = True
                        upload_session.save()
                    out['success'] = True
                    out['url'] = reverse(
                        'layer_detail', args=[
                            saved_layer.service_typename])
            except Exception as e:
                logger.exception(e)
                out['success'] = False
                out['errors'] = str(e)
            finally:
                if tempdir is not None:
                    shutil.rmtree(tempdir)
        else:
            errormsgs = []
            for e in form.errors.values():
                errormsgs.append([escape(v) for v in e])
            out['errors'] = form.errors
            out['errormsgs'] = errormsgs

        if out['success']:
            status_code = 200
            register_event(request, 'change', layer)
        else:
            status_code = 400
        return HttpResponse(
            json.dumps(out),
            content_type='application/json',
            status=status_code)


@login_required
def layer_remove(request, layername, template='layers/layer_remove.html'):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if (request.method == 'GET'):
        return render(request, template, context={
            "layer": layer
        })
    if (request.method == 'POST'):
        try:
            logger.debug(f'Deleting Layer {layer}')
            with transaction.atomic():
                Layer.objects.filter(id=layer.id).delete()
        except IntegrityError:
            raise
        except Exception as e:
            traceback.print_exc()
            message = '{0}: {1}.'.format(
                _('Unable to delete layer'), layer.alternate)

            if getattr(e, 'message', None) and 'referenced by layer group' in getattr(e, 'message', ''):
                message = _(
                    'This layer is a member of a layer group, you must remove the layer from the group '
                    'before deleting.')

            messages.error(request, message)
            return render(
                request, template, context={"layer": layer})

        register_event(request, 'remove', layer)
        return HttpResponseRedirect(reverse("layer_browse"))
    else:
        return HttpResponse("Not allowed", status=403)


@login_required
def layer_granule_remove(
        request,
        granule_id,
        layername,
        template='layers/layer_granule_remove.html'):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'base.delete_resourcebase',
            _PERMISSION_MSG_DELETE)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    if (request.method == 'GET'):
        return render(request, template, context={
            "granule_id": granule_id,
            "layer": layer
        })
    if (request.method == 'POST'):
        try:
            cat = gs_catalog
            cat._cache.clear()
            store = cat.get_store(layer.name)
            coverages = cat.mosaic_coverages(store)
            cat.mosaic_delete_granule(
                coverages['coverages']['coverage'][0]['name'], store, granule_id)
        except Exception as e:
            traceback.print_exc()
            message = '{0}: {1}.'.format(
                _('Unable to delete layer'), layer.alternate)

            if 'referenced by layer group' in getattr(e, 'message', ''):
                message = _(
                    'This layer is a member of a layer group, you must remove the layer from the group '
                    'before deleting.')

            messages.error(request, message)
            return render(
                request, template, context={"layer": layer})
        return HttpResponseRedirect(
            reverse(
                'layer_detail', args=(
                    layer.service_typename,)))
    else:
        return HttpResponse("Not allowed", status=403)


@require_http_methods(["POST"])
def layer_thumbnail(request, layername):
    try:
        layer_obj = _resolve_layer(request, layername)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer_obj:
        raise Http404(_("Not found"))

    try:
        request_body = json.loads(request.body)
        bbox = request_body['bbox'] + [request_body['srid']]
        zoom = request_body.get('zoom', None)

        create_thumbnail(
            layer_obj,
            bbox=bbox,
            background_zoom=zoom,
            overwrite=True
        )

        return HttpResponse('Thumbnail saved')

    except Exception as e:
        logger.exception(e)
        return HttpResponse(
            content=_('couldn\'t generate thumbnail: %s' % str(e)),
            status=500,
            content_type='text/plain'
        )


def get_layer(request, layername):
    """Get Layer object as JSON"""

    # Function to treat Decimal in json.dumps.
    # http://stackoverflow.com/a/16957370/1198772
    def decimal_default(obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        raise TypeError
    logger.debug('Call get layer')
    if request.method == 'GET':
        try:
            layer_obj = _resolve_layer(request, layername)
        except PermissionDenied:
            return HttpResponse(_("Not allowed"), status=403)
        except Exception:
            raise Http404(_("Not found"))
        if not layer_obj:
            raise Http404(_("Not found"))

        logger.debug(layername)
        response = {
            'typename': layername,
            'name': layer_obj.name,
            'title': layer_obj.title,
            'url': layer_obj.get_tiles_url(),
            'bbox_string': layer_obj.bbox_string,
            'bbox_x0': layer_obj.bbox_helper.xmin,
            'bbox_x1': layer_obj.bbox_helper.xmax,
            'bbox_y0': layer_obj.bbox_helper.ymin,
            'bbox_y1': layer_obj.bbox_helper.ymax,
        }
        return HttpResponse(
            json.dumps(
                response,
                ensure_ascii=False,
                default=decimal_default
            ),
            content_type='application/javascript')


def layer_metadata_detail(
        request,
        layername,
        template='layers/layer_metadata_detail.html'):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'view_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    group = None
    if layer.group:
        try:
            group = GroupProfile.objects.get(slug=layer.group.name)
        except GroupProfile.DoesNotExist:
            group = None
    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL

    register_event(request, 'view_metadata', layer)

    return render(request, template, context={
        "resource": layer,
        "perms_list": get_perms(
            request.user,
            layer.get_self_resource()) + get_perms(request.user, layer),
        "group": group,
        'SITEURL': site_url
    })


def layer_metadata_upload(
        request,
        layername,
        template='layers/layer_metadata_upload.html'):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'base.change_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    return render(request, template, context={
        "resource": layer,
        "layer": layer,
        'SITEURL': site_url
    })


def layer_sld_upload(
        request,
        layername,
        template='layers/layer_style_upload.html'):
    try:
        layer = _resolve_layer(
            request,
            layername,
            'base.change_resourcebase',
            _PERMISSION_MSG_METADATA)
    except PermissionDenied:
        return HttpResponse(_("Not allowed"), status=403)
    except Exception:
        raise Http404(_("Not found"))
    if not layer:
        raise Http404(_("Not found"))

    site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
    return render(request, template, context={
        "resource": layer,
        "layer": layer,
        'SITEURL': site_url
    })


def layer_sld_edit(
        request,
        layername,
        template='layers/layer_style_edit.html'):
    return layer_detail(request, layername, template)


@xframe_options_exempt
def layer_embed(
        request,
        layername,
        template='layers/layer_embed.html'):
    return layer_detail(request, layername, template)


@login_required
def layer_batch_metadata(request):
    return batch_modify(request, 'Layer')


def batch_permissions(request, model):
    Resource = None
    if model == 'Layer':
        Resource = Layer
    if not Resource or not request.user.is_superuser:
        raise PermissionDenied

    template = 'base/batch_permissions.html'
    ids = request.POST.get("ids")

    if "cancel" in request.POST or not ids:
        return HttpResponseRedirect(
            '/admin/{model}s/{model}/'.format(model=model.lower())
        )

    if request.method == 'POST':
        form = BatchPermissionsForm(request.POST)
        if form.is_valid():
            _data = form.cleaned_data
            resources_names = []
            for resource in Resource.objects.filter(id__in=ids.split(',')):
                resources_names.append(resource.name)
            users_usernames = [_data['user'].username, ] if _data['user'] else None
            groups_names = [_data['group'].name, ] if _data['group'] else None
            if users_usernames and 'AnonymousUser' in users_usernames and \
                    (not groups_names or 'anonymous' not in groups_names):
                if not groups_names:
                    groups_names = []
                groups_names.append('anonymous')
            if groups_names and 'anonymous' in groups_names and \
                    (not users_usernames or 'AnonymousUser' not in users_usernames):
                if not users_usernames:
                    users_usernames = []
                users_usernames.append('AnonymousUser')
            delete_flag = _data['mode'] == 'unset'
            permissions_names = _data['permission_type']
            if permissions_names:
                try:
                    set_permissions.apply_async((
                        permissions_names,
                        resources_names,
                        users_usernames,
                        groups_names,
                        delete_flag))
                except set_permissions.OperationalError as exc:
                    celery_logger.exception('Sending task raised: %r', exc)
            return HttpResponseRedirect(
                '/admin/{model}s/{model}/'.format(model=model.lower())
            )
        return render(
            request,
            template,
            context={
                'form': form,
                'ids': ids,
                'model': model,
            }
        )

    form = BatchPermissionsForm(
        {
            'permission_type': ('r', ),
            'mode': 'set'
        })
    return render(
        request,
        template,
        context={
            'form': form,
            'ids': ids,
            'model': model,
        }
    )


@login_required
def layer_batch_permissions(request):
    return batch_permissions(request, 'Layer')


def layer_view_counter(layer_id, viewer):
    _l = Layer.objects.get(id=layer_id)
    _u = get_user_model().objects.get(username=viewer)
    _l.view_count_up(_u, do_local=True)


class LayerAutocomplete(autocomplete.Select2QuerySetView):

    # Overriding both result label methods to ensure autocomplete labels display without 'geonode:' prefix
    def get_selected_result_label(self, result):
        """Return the label of a selected result."""
        return self.get_result_label(result)

    def get_result_label(self, result):
        """Return the label of a selected result."""
        return str(result.title)

    def get_queryset(self):
        request = self.request
        permitted = get_objects_for_user(
            request.user,
            'base.view_resourcebase')
        qs = Layer.objects.all().filter(id__in=permitted)

        if self.q:
            qs = qs.filter(title__icontains=self.q)

        return get_visible_resources(
            qs,
            request.user if request else None,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES)
