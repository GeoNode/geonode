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
import gc
import re
import ast
import copy
import json
import time
import base64
import select
import shutil
import string
import logging
import tarfile
import datetime
import requests
import tempfile
import traceback
import subprocess

from osgeo import ogr
from PIL import Image
from io import BytesIO, StringIO
from decimal import Decimal
from slugify import slugify
from contextlib import closing
from collections import defaultdict
from math import atan, exp, log, pi, sin, tan, floor
from zipfile import ZipFile, is_zipfile, ZIP_DEFLATED
from requests.packages.urllib3.util.retry import Retry

from django.conf import settings
from django.core.cache import cache
from django.db.models import signals
from django.utils.http import is_safe_url
from django.apps import apps as django_apps
from django.middleware.csrf import get_token
from django.http import Http404, HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.core.files.storage import default_storage as storage
from django.db import models, connection, transaction
from django.utils.translation import ugettext_lazy as _

from geonode import geoserver, qgis_server, GeoNodeException  # noqa
from geonode.compat import ensure_string
from geonode.base.auth import (
    extend_token,
    get_or_create_token,
    get_token_from_auth_header,
    get_token_object_from_session)

from urllib.parse import (
    urljoin,
    unquote,
    urlparse,
    urlsplit,
    urlencode,
    parse_qs,
    parse_qsl,
    ParseResult,
    SplitResult
)

MAX_EXTENT = 20037508.34
FULL_ROTATION_DEG = 360.0
HALF_ROTATION_DEG = 180.0
DEFAULT_TITLE = ""
DEFAULT_ABSTRACT = ""

INVALID_PERMISSION_MESSAGE = _("Invalid permission level.")

ALPHABET = f"{string.ascii_uppercase + string.ascii_lowercase + string.digits}-_"
ALPHABET_REVERSE = {c: i for (i, c) in enumerate(ALPHABET)}
BASE = len(ALPHABET)
SIGN_CHARACTER = '$'
SQL_PARAMS_RE = re.compile(r'%\(([\w_\-]+)\)s')

requests.packages.urllib3.disable_warnings()

signalnames = [
    'class_prepared',
    'm2m_changed',
    'post_delete',
    'post_init',
    'post_save',
    'post_syncdb',
    'pre_delete',
    'pre_init',
    'pre_save']
signals_store = {}

id_none = id(None)

logger = logging.getLogger("geonode.utils")


def unzip_file(upload_file, extension='.shp', tempdir=None):
    """
    Unzips a zipfile into a temporary directory and returns the full path of the .shp file inside (if any)
    """
    absolute_base_file = None
    if tempdir is None:
        tempdir = tempfile.mkdtemp(dir=settings.STATIC_ROOT)
    if not os.path.isdir(tempdir):
        os.makedirs(tempdir)

    the_zip = ZipFile(upload_file, allowZip64=True)
    the_zip.extractall(tempdir)
    for item in the_zip.namelist():
        if item.endswith(extension):
            absolute_base_file = os.path.join(tempdir, item)

    return absolute_base_file


def extract_tarfile(upload_file, extension='.shp', tempdir=None):
    """
    Extracts a tarfile into a temporary directory and returns the full path of the .shp file inside (if any)
    """
    absolute_base_file = None
    if tempdir is None:
        tempdir = tempfile.mkdtemp(dir=settings.STATIC_ROOT)

    the_tar = tarfile.open(upload_file)
    the_tar.extractall(tempdir)
    for item in the_tar.getnames():
        if item.endswith(extension):
            absolute_base_file = os.path.join(tempdir, item)

    return absolute_base_file


def get_layer_name(layer):
    """Get the workspace where the input layer belongs"""
    _name = layer.name
    if _name and ':' in _name:
        _name = _name.split(':')[1]
    try:
        if not _name and layer.alternate:
            if ':' in layer.alternate:
                _name = layer.alternate.split(':')[1]
            else:
                _name = layer.alternate
    except Exception:
        pass
    return _name


def get_layer_workspace(layer):
    """Get the workspace where the input layer belongs"""
    alternate = None
    workspace = None
    try:
        alternate = layer.alternate
    except Exception:
        alternate = layer.name
    try:
        workspace = layer.workspace
    except Exception:
        workspace = None
    if not workspace and alternate and ':' in alternate:
        workspace = alternate.split(":")[1]
    if not workspace:
        default_workspace = getattr(settings, "DEFAULT_WORKSPACE", "geonode")
        try:
            from geonode.services.enumerations import CASCADED
            if layer.remote_service.method == CASCADED:
                workspace = getattr(
                    settings, "CASCADE_WORKSPACE", default_workspace)
            else:
                raise RuntimeError("Layer is not cascaded")
        except AttributeError:  # layer does not have a service
            workspace = default_workspace
    return workspace


def get_headers(request, url, raw_url, allowed_hosts=[]):
    headers = {}
    cookies = None
    csrftoken = None

    if settings.SESSION_COOKIE_NAME in request.COOKIES and is_safe_url(
            url=raw_url, allowed_hosts=url.hostname):
        cookies = request.META["HTTP_COOKIE"]

    for cook in request.COOKIES:
        name = str(cook)
        value = request.COOKIES.get(name)
        if name == 'csrftoken':
            csrftoken = value
        cook = f"{name}={value}"
        cookies = cook if not cookies else (f"{cookies}; {cook}")

    csrftoken = get_token(request) if not csrftoken else csrftoken

    if csrftoken:
        headers['X-Requested-With'] = "XMLHttpRequest"
        headers['X-CSRFToken'] = csrftoken
        cook = f"{'csrftoken'}={csrftoken}"
        cookies = cook if not cookies else (f"{cookies}; {cook}")

    if cookies:
        if 'JSESSIONID' in request.session and request.session['JSESSIONID']:
            cookies = f"{cookies}; JSESSIONID={request.session['JSESSIONID']}"
        headers['Cookie'] = cookies

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    access_token = None
    site_url = urlsplit(settings.SITEURL)
    # We want to convert HTTP_AUTH into a Beraer Token only when hitting the local GeoServer
    if site_url.hostname in (allowed_hosts + [url.hostname]):
        # we give precedence to obtained from Aithorization headers
        if 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META.get(
                'HTTP_AUTHORIZATION',
                request.META.get('HTTP_AUTHORIZATION2'))
            if auth_header:
                headers['Authorization'] = auth_header
                access_token = get_token_from_auth_header(auth_header, create_if_not_exists=True)
        # otherwise we check if a session is active
        elif request and request.user.is_authenticated:
            access_token = get_token_object_from_session(request.session)

            # we extend the token in case the session is active but the token expired
            if access_token and access_token.is_expired():
                extend_token(access_token)
            else:
                access_token = get_or_create_token(request.user)

    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'

    pragma = "no-cache"
    referer = request.META[
        "HTTP_REFERER"] if "HTTP_REFERER" in request.META else \
        f"{site_url.scheme}://{site_url.netloc}/"
    encoding = request.META["HTTP_ACCEPT_ENCODING"] if "HTTP_ACCEPT_ENCODING" in request.META else "gzip"
    headers.update({"Pragma": pragma,
                    "Referer": referer,
                    "Accept-encoding": encoding,
                    })

    return (headers, access_token)


def _get_basic_auth_info(request):
    """
    grab basic auth info
    """
    meth, auth = request.META['HTTP_AUTHORIZATION'].split()
    if meth.lower() != 'basic':
        raise ValueError
    username, password = base64.b64decode(auth.encode()).decode().split(':')
    return username, password


def batch_permissions(request):
    # TODO
    pass


def batch_delete(request):
    # TODO
    pass


def _split_query(query):
    """
    split and strip keywords, preserve space
    separated quoted blocks.
    """

    qq = query.split(' ')
    keywords = []
    accum = None
    for kw in qq:
        if accum is None:
            if kw.startswith('"'):
                accum = kw[1:]
            elif kw:
                keywords.append(kw)
        else:
            accum += f" {kw}"
            if kw.endswith('"'):
                keywords.append(accum[0:-1])
                accum = None
    if accum is not None:
        keywords.append(accum)
    return [kw.strip() for kw in keywords if kw.strip()]


def bbox_to_wkt(x0, x1, y0, y1, srid="4326", include_srid=True):
    if srid and str(srid).startswith('EPSG:'):
        srid = srid[5:]
    if None not in {x0, x1, y0, y1}:
        wkt = 'POLYGON((%f %f,%f %f,%f %f,%f %f,%f %f))' % (
            float(x0), float(y0),
            float(x0), float(y1),
            float(x1), float(y1),
            float(x1), float(y0),
            float(x0), float(y0))
        if include_srid:
            wkt = f'SRID={srid};{wkt}'
    else:
        wkt = 'POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))'
        if include_srid:
            wkt = f'SRID=4326;{wkt}'
    return wkt


def _v(coord, x, source_srid=4326, target_srid=3857):
    if source_srid == 4326 and x and abs(coord) != HALF_ROTATION_DEG:
        coord -= (round(coord / FULL_ROTATION_DEG) * FULL_ROTATION_DEG)
    if source_srid == 4326 and target_srid != 4326:
        if x and float(coord) >= 179.999:
            return 179.999
        elif x and float(coord) <= -179.999:
            return -179.999

        if not x and float(coord) >= 89.999:
            return 89.999
        elif not x and float(coord) <= -89.999:
            return -89.999
    return coord


def bbox_to_projection(native_bbox, target_srid=4326):
    """
        native_bbox must be in the form
            ('-81.3962935', '-81.3490249', '13.3202891', '13.3859614', 'EPSG:4326')
    """
    box = native_bbox[:4]
    proj = native_bbox[-1]
    minx, maxx, miny, maxy = [float(a) for a in box]
    try:
        source_srid = int(proj.split(":")[1]) if proj and ':' in proj else int(proj)
    except Exception:
        source_srid = target_srid

    if source_srid != target_srid:
        try:
            wkt = bbox_to_wkt(_v(minx, x=True, source_srid=source_srid, target_srid=target_srid),
                              _v(maxx, x=True, source_srid=source_srid, target_srid=target_srid),
                              _v(miny, x=False, source_srid=source_srid, target_srid=target_srid),
                              _v(maxy, x=False, source_srid=source_srid, target_srid=target_srid),
                              srid=source_srid, include_srid=False)
            # AF: This causses error with GDAL 3.0.4 due to a breaking change on GDAL
            #     https://code.djangoproject.com/ticket/30645
            import osgeo.gdal
            _gdal_ver = osgeo.gdal.__version__.split(".", 2)
            from osgeo import ogr
            from osgeo.osr import SpatialReference, CoordinateTransformation
            g = ogr.Geometry(wkt=wkt)
            source = SpatialReference()
            source.ImportFromEPSG(source_srid)
            dest = SpatialReference()
            dest.ImportFromEPSG(target_srid)
            if int(_gdal_ver[0]) >= 3 and \
                    ((int(_gdal_ver[1]) == 0 and int(_gdal_ver[2]) >= 4) or int(_gdal_ver[1]) > 0):
                source.SetAxisMappingStrategy(0)
                dest.SetAxisMappingStrategy(0)
            g.Transform(CoordinateTransformation(source, dest))
            projected_bbox = [str(x) for x in g.GetEnvelope()]
            # Must be in the form : [x0, x1, y0, y1, EPSG:<target_srid>)
            return tuple([projected_bbox[0], projected_bbox[1], projected_bbox[2], projected_bbox[3]]) + \
                (f"EPSG:{target_srid}",)
        except Exception:
            tb = traceback.format_exc()
            logger.error(tb)

    return native_bbox


def bounds_to_zoom_level(bounds, width, height):
    WORLD_DIM = {'height': 256., 'width': 256.}
    ZOOM_MAX = 21

    def latRad(lat):
        _sin = sin(lat * pi / HALF_ROTATION_DEG)
        if abs(_sin) != 1.0:
            radX2 = log((1.0 + _sin) / (1.0 - _sin)) / 2.0
        else:
            radX2 = log(1.0) / 2.0
        return max(min(radX2, pi), -pi) / 2.0

    def zoom(mapPx, worldPx, fraction):
        try:
            return floor(log(mapPx / worldPx / fraction) / log(2.0))
        except Exception:
            return 0

    ne = [float(bounds[2]), float(bounds[3])]
    sw = [float(bounds[0]), float(bounds[1])]
    latFraction = (latRad(ne[1]) - latRad(sw[1])) / pi
    lngDiff = ne[0] - sw[0]
    lngFraction = ((lngDiff + FULL_ROTATION_DEG) if lngDiff < 0 else lngDiff) / FULL_ROTATION_DEG
    latZoom = zoom(float(height), WORLD_DIM['height'], latFraction)
    lngZoom = zoom(float(width), WORLD_DIM['width'], lngFraction)
    # ratio = float(max(width, height)) / float(min(width, height))
    # z_offset = 0 if ratio >= 2 else -1
    z_offset = 0
    zoom = int(max(latZoom, lngZoom) + z_offset)
    zoom = 0 if zoom > ZOOM_MAX else zoom
    return max(zoom, 0)


def llbbox_to_mercator(llbbox):
    minlonlat = forward_mercator([llbbox[0], llbbox[2]])
    maxlonlat = forward_mercator([llbbox[1], llbbox[3]])
    return [minlonlat[0], minlonlat[1], maxlonlat[0], maxlonlat[1]]


def mercator_to_llbbox(bbox):
    minlonlat = inverse_mercator([bbox[0], bbox[2]])
    maxlonlat = inverse_mercator([bbox[1], bbox[3]])
    return [minlonlat[0], minlonlat[1], maxlonlat[0], maxlonlat[1]]


def forward_mercator(lonlat):
    """
        Given geographic coordinates, return a x,y tuple in spherical mercator.

        If the lat value is out of range, -inf will be returned as the y value
    """
    x = lonlat[0] * MAX_EXTENT / HALF_ROTATION_DEG
    try:
        # With data sets that only have one point the value of this
        # expression becomes negative infinity. In order to continue,
        # we wrap this in a try catch block.
        n = tan((90 + lonlat[1]) * pi / FULL_ROTATION_DEG)
    except ValueError:
        n = 0
    if n <= 0:
        y = float("-inf")
    else:
        y = log(n) / pi * MAX_EXTENT
    return (x, y)


def inverse_mercator(xy):
    """
        Given coordinates in spherical mercator, return a lon,lat tuple.
    """
    lon = (xy[0] / MAX_EXTENT) * HALF_ROTATION_DEG
    lat = (xy[1] / MAX_EXTENT) * HALF_ROTATION_DEG
    lat = HALF_ROTATION_DEG / pi * \
        (2 * atan(exp(lat * pi / HALF_ROTATION_DEG)) - pi / 2)
    return (lon, lat)


def layer_from_viewer_config(map_id, model, layer, source, ordering, save_map=True):
    """
    Parse an object out of a parsed layer configuration from a GXP
    viewer.

    ``model`` is the type to instantiate
    ``layer`` is the parsed dict for the layer
    ``source`` is the parsed dict for the layer's source
    ``ordering`` is the index of the layer within the map's layer list
    ``save_map`` if map should be saved (default: True)
    """
    layer_cfg = dict(layer)
    for k in ["format", "name", "opacity", "styles", "transparent",
              "fixed", "group", "visibility", "source"]:
        if k in layer_cfg:
            del layer_cfg[k]
    layer_cfg["id"] = 1
    layer_cfg["wrapDateLine"] = True
    layer_cfg["displayOutsideMaxExtent"] = True

    source_cfg = dict(source) if source else {}
    if source_cfg:
        for k in ["url", "projection"]:
            if k in source_cfg:
                del source_cfg[k]

    # We don't want to hardcode 'access_token' into the storage
    styles = []
    if 'capability' in layer_cfg:
        _capability = layer_cfg['capability']
        if 'styles' in _capability:
            for style in _capability['styles']:
                if 'name' in style:
                    styles.append(style['name'])
                if 'legend' in style:
                    legend = style['legend']
                    if 'href' in legend:
                        legend['href'] = re.sub(
                            r'\&access_token=.*', '', legend['href'])
    if not styles and layer.get("styles", None):
        for style in layer.get("styles", None):
            if 'name' in style:
                styles.append(style['name'])
            else:
                styles.append(style)

    _model = model(
        map_id=map_id,
        stack_order=ordering,
        format=layer.get("format", None),
        name=layer.get("name", None),
        store=layer.get("store", None),
        opacity=layer.get("opacity", 1),
        styles=styles,
        transparent=layer.get("transparent", False),
        fixed=layer.get("fixed", False),
        group=layer.get('group', None),
        visibility=layer.get("visibility", True),
        ows_url=source.get("url", None) if source else None,
        layer_params=json.dumps(layer_cfg),
        source_params=json.dumps(source_cfg)
    )
    if map_id and save_map:
        _model.save()

    return _model


class GXPMapBase(object):

    def viewer_json(self, request, *added_layers):
        """
        Convert this map to a nested dictionary structure matching the JSON
        configuration for GXP Viewers.

        The ``added_layers`` parameter list allows a list of extra MapLayer
        instances to append to the Map's layer list when generating the
        configuration. These are not persisted; if you want to add layers you
        should use ``.layer_set.create()``.
        """

        user = request.user if request else None
        access_token = get_or_create_token(user)
        if access_token and not access_token.is_expired():
            access_token = access_token.token

        if self.id and len(added_layers) == 0:
            cfg = cache.get(f"viewer_json_{str(self.id)}_{str(0 if user is None else user.id)}")
            if cfg is not None:
                return cfg

        layers = list(self.layers)
        layers.extend(added_layers)

        server_lookup = {}
        sources = {}

        def uniqify(seq):
            """
            get a list of unique items from the input sequence.

            This relies only on equality tests, so you can use it on most
            things.  If you have a sequence of hashables, list(set(seq)) is
            better.
            """
            results = []
            for x in seq:
                if x not in results:
                    results.append(x)
            return results

        configs = [lyr.source_config(access_token) for lyr in layers]

        i = 0
        for source in uniqify(configs):
            while str(i) in sources:
                i = i + 1
            sources[str(i)] = source
            server_lookup[json.dumps(source)] = str(i)

        def source_lookup(source):
            for k, v in sources.items():
                if v == source:
                    return k
            return None

        def layer_config(lyr, user=None):
            cfg = lyr.layer_config(user=user)
            src_cfg = lyr.source_config(access_token)
            source = source_lookup(src_cfg)
            if source:
                cfg["source"] = source
            return cfg

        source_urls = [source['url']
                       for source in sources.values() if source and 'url' in source]

        if 'geonode.geoserver' in settings.INSTALLED_APPS:
            if len(sources.keys()) > 0 and 'source' in settings.MAP_BASELAYERS[0] and \
                'url' in settings.MAP_BASELAYERS[0]['source'] and \
                    not settings.MAP_BASELAYERS[0]['source']['url'] in source_urls:
                keys = sorted(sources.keys())
                settings.MAP_BASELAYERS[0]['source'][
                    'title'] = 'Local Geoserver'
                sources[str(int(keys[-1]) + 1)
                        ] = settings.MAP_BASELAYERS[0]['source']

        def _base_source(source):
            base_source = copy.deepcopy(source)
            for key in ["id", "baseParams", "title"]:
                if base_source and key in base_source:
                    del base_source[key]
            return base_source

        for lyr in settings.MAP_BASELAYERS:
            if "source" in lyr and _base_source(
                    lyr["source"]) not in map(
                    _base_source,
                    sources.values()):
                if len(sources.keys()) > 0:
                    sources[str(int(max(sources.keys(), key=int)) + 1)
                            ] = lyr["source"]

        # adding remote services sources
        from geonode.services.models import Service
        from geonode.maps.models import Map
        if not self.sender or isinstance(self.sender, Map):
            index = int(max(sources.keys())) if len(sources.keys()) > 0 else 0
            for service in Service.objects.all():
                remote_source = {
                    'url': service.service_url,
                    'remote': True,
                    'ptype': service.ptype,
                    'name': service.name,
                    'title': f"[R] {service.title}"
                }
                if remote_source['url'] not in source_urls:
                    index += 1
                    sources[index] = remote_source

        config = {
            'id': self.id,
            'about': {
                'title': self.title,
                'abstract': self.abstract
            },
            'aboutUrl': '../about',
            'defaultSourceType': "gxp_wmscsource",
            'sources': sources,
            'map': {
                'layers': [layer_config(lyr, user=user) for lyr in layers],
                'center': [self.center_x, self.center_y],
                'projection': self.projection,
                'zoom': self.zoom
            }
        }

        if any(layers):
            # Mark the last added layer as selected - important for data page
            config["map"]["layers"][len(layers) - 1]["selected"] = True
        else:
            (def_map_config, def_map_layers) = default_map_config(None)
            config = def_map_config

        config["map"].update(_get_viewer_projection_info(self.projection))

        # Create user-specific cache of maplayer config
        if self is not None:
            cache.set(f"viewer_json_{str(self.id)}_{str(0 if user is None else user.id)}", config)

        # Client conversion if needed
        from geonode.client.hooks import hookset
        config = hookset.viewer_json(config, context={'request': request})
        return config


class GXPMap(GXPMapBase):

    def __init__(self, sender=None, projection=None, title=None, abstract=None,
                 center_x=None, center_y=None, zoom=None):
        self.id = 0
        self.sender = sender
        self.projection = projection
        self.title = title or DEFAULT_TITLE
        self.abstract = abstract or DEFAULT_ABSTRACT
        _DEFAULT_MAP_CENTER = forward_mercator(settings.DEFAULT_MAP_CENTER)
        self.center_x = center_x if center_x is not None else _DEFAULT_MAP_CENTER[
            0]
        self.center_y = center_y if center_y is not None else _DEFAULT_MAP_CENTER[
            1]
        self.zoom = zoom if zoom is not None else settings.DEFAULT_MAP_ZOOM
        self.layers = []


class GXPLayerBase(object):

    def source_config(self, access_token):
        """
        Generate a dict that can be serialized to a GXP layer source
        configuration suitable for loading this layer.
        """
        try:
            cfg = json.loads(self.source_params)
        except Exception:
            cfg = dict(ptype="gxp_wmscsource", restUrl="/gs/rest")

        if self.ows_url:
            '''
            This limits the access token we add to only the OGC servers decalred in OGC_SERVER.
            Will also override any access_token in the request and replace it with an existing one.
            '''
            urls = []
            for name, server in settings.OGC_SERVER.items():
                url = urlsplit(server['PUBLIC_LOCATION'])
                urls.append(url.netloc)

            my_url = urlsplit(self.ows_url)

            if str(access_token) and my_url.netloc in urls:
                request_params = parse_qs(my_url.query)
                if 'access_token' in request_params:
                    del request_params['access_token']
                # request_params['access_token'] = [access_token]
                encoded_params = urlencode(request_params, doseq=True)

                parsed_url = SplitResult(
                    my_url.scheme,
                    my_url.netloc,
                    my_url.path,
                    encoded_params,
                    my_url.fragment)
                cfg["url"] = parsed_url.geturl()
            else:
                cfg["url"] = self.ows_url

        return cfg

    def layer_config(self, user=None):
        """
        Generate a dict that can be serialized to a GXP layer configuration
        suitable for loading this layer.

        The "source" property will be left unset; the layer is not aware of the
        name assigned to its source plugin.  See
        geonode.maps.models.Map.viewer_json for an example of
        generating a full map configuration.
        """
        try:
            cfg = json.loads(self.layer_params)
        except Exception:
            cfg = dict()

        if self.format:
            cfg['format'] = self.format
        if self.name:
            cfg["name"] = self.name
        if self.opacity:
            cfg['opacity'] = self.opacity
        if self.styles:
            try:
                cfg['styles'] = ast.literal_eval(self.styles) \
                    if isinstance(self.styles, str) else self.styles
            except Exception:
                pass
        if self.transparent:
            cfg['transparent'] = True

        cfg["fixed"] = self.fixed
        if self.group:
            cfg["group"] = self.group
        cfg["visibility"] = self.visibility

        return cfg


class GXPLayer(GXPLayerBase):

    '''GXPLayer represents an object to be included in a GXP map.
    '''

    def __init__(self, name=None, ows_url=None, **kw):
        self.format = None
        self.name = name
        self.opacity = 1.0
        self.styles = None
        self.transparent = False
        self.fixed = False
        self.group = None
        self.visibility = True
        self.wrapDateLine = True
        self.displayOutsideMaxExtent = True
        self.ows_url = ows_url
        self.layer_params = ""
        self.source_params = ""
        for k in kw:
            setattr(self, k, kw[k])


def default_map_config(request):
    if getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857') == "EPSG:4326":
        _DEFAULT_MAP_CENTER = inverse_mercator(settings.DEFAULT_MAP_CENTER)
    else:
        _DEFAULT_MAP_CENTER = forward_mercator(settings.DEFAULT_MAP_CENTER)

    _default_map = GXPMap(
        title=DEFAULT_TITLE,
        abstract=DEFAULT_ABSTRACT,
        projection=getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:3857'),
        center_x=_DEFAULT_MAP_CENTER[0],
        center_y=_DEFAULT_MAP_CENTER[1],
        zoom=settings.DEFAULT_MAP_ZOOM
    )

    def _baselayer(lyr, order):
        return layer_from_viewer_config(
            None,
            GXPLayer,
            layer=lyr,
            source=lyr["source"] if lyr and "source" in lyr else None,
            ordering=order
        )

    DEFAULT_BASE_LAYERS = [
        _baselayer(
            lyr, idx) for idx, lyr in enumerate(
            settings.MAP_BASELAYERS)]

    DEFAULT_MAP_CONFIG = _default_map.viewer_json(
        request, *DEFAULT_BASE_LAYERS)

    return DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS


max_extent = [-MAX_EXTENT, -MAX_EXTENT, MAX_EXTENT, MAX_EXTENT]
_viewer_projection_lookup = {
    "EPSG:900913": {
        "maxResolution": 156543.03390625,
        "units": "m",
        "maxExtent": max_extent,
    },
    "EPSG:3857": {
        "maxResolution": 156543.03390625,
        "units": "m",
        "maxExtent": max_extent,
    },
    "EPSG:4326": {
        "max_resolution": FULL_ROTATION_DEG / 256,
        "units": "degrees",
        "maxExtent": [-180, -90, 180, 90]
    }
}


def _get_viewer_projection_info(srid):
    # TODO: Look up projection details in EPSG database
    return _viewer_projection_lookup.get(srid, {})


def resolve_object(request, model, query, permission='base.view_resourcebase',
                   user=None, permission_required=True, permission_msg=None):
    """Resolve an object using the provided query and check the optional
    permission. Model views should wrap this function as a shortcut.

    query - a dict to use for querying the model
    permission - an optional permission to check
    permission_required - if False, allow get methods to proceed
    permission_msg - optional message to use in 403
    """
    user = request.user if request and request.user else user
    obj = get_object_or_404(model, **query)
    obj_to_check = obj.get_self_resource()

    from guardian.shortcuts import assign_perm, get_groups_with_perms
    from geonode.groups.models import GroupProfile

    groups = get_groups_with_perms(obj_to_check,
                                   attach_perms=True)

    if obj_to_check.group and obj_to_check.group not in groups:
        groups[obj_to_check.group] = obj_to_check.group

    obj_group_managers = []
    obj_group_members = []
    if groups:
        for group in groups:
            try:
                group_profile = GroupProfile.objects.get(slug=group.name)
                managers = group_profile.get_managers()
                if managers:
                    for manager in managers:
                        if manager not in obj_group_managers and not manager.is_superuser:
                            obj_group_managers.append(manager)
                if group_profile.user_is_member(
                        user) and user not in obj_group_members:
                    obj_group_members.append(user)
            except GroupProfile.DoesNotExist:
                pass

    if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
        is_admin = False
        is_manager = False
        is_owner = user == obj_to_check.owner
        if user and user.is_authenticated:
            is_admin = user.is_superuser if user else False
            try:
                is_manager = user.groupmember_set.all().filter(role='manager').exists()
            except Exception:
                is_manager = False
        if (not obj_to_check.is_approved):
            if not user or user.is_anonymous:
                raise Http404
            elif not is_admin:
                if is_manager and user in obj_group_managers:
                    if (not user.has_perm('publish_resourcebase', obj_to_check)) and (
                        not user.has_perm('view_resourcebase', obj_to_check)) and (
                            not user.has_perm('change_resourcebase_metadata', obj_to_check)) and (
                                not is_owner and not settings.ADMIN_MODERATE_UPLOADS):
                        pass
                    else:
                        assign_perm(
                            'view_resourcebase', user, obj_to_check)
                        assign_perm(
                            'publish_resourcebase',
                            user,
                            obj_to_check)
                        assign_perm(
                            'change_resourcebase_metadata',
                            user,
                            obj_to_check)
                        assign_perm(
                            'download_resourcebase',
                            user,
                            obj_to_check)

                        if is_owner:
                            assign_perm(
                                'change_resourcebase', user, obj_to_check)
                            assign_perm(
                                'delete_resourcebase', user, obj_to_check)

    allowed = True
    if permission.split('.')[-1] in ['change_layer_data',
                                     'change_layer_style']:
        if obj.__class__.__name__ == 'Layer':
            obj_to_check = obj
    if permission:
        if permission_required or request.method != 'GET':
            if user in obj_group_managers:
                allowed = True
            else:
                allowed = user.has_perm(
                    permission,
                    obj_to_check)
    if not allowed:
        mesg = permission_msg or _('Permission Denied')
        raise PermissionDenied(mesg)
    return obj


def json_response(body=None, errors=None, url=None, redirect_to=None, exception=None,
                  content_type=None, status=None):
    """Create a proper JSON response. If body is provided, this is the response.
    If errors is not None, the response is a success/errors json object.
    If redirect_to is not None, the response is a success=True, redirect_to object
    If the exception is provided, it will be logged. If body is a string, the
    exception message will be used as a format option to that string and the
    result will be a success=False, errors = body % exception
    """
    if isinstance(body, HttpResponse):
        return body
    if content_type is None:
        content_type = "application/json"
    if errors:
        if isinstance(errors, str):
            errors = [errors]
        body = {
            'success': False,
            'errors': errors
        }
    elif redirect_to:
        body = {
            'success': True,
            'redirect_to': redirect_to
        }
    elif url:
        body = {
            'success': True,
            'url': url
        }
    elif exception:
        if body is None:
            body = f"Unexpected exception {exception}"
        else:
            body = body % exception
        body = {
            'success': False,
            'errors': [body]
        }
    elif body:
        pass
    else:
        raise Exception("must call with body, errors or redirect_to")

    if status is None:
        status = 200

    if not isinstance(body, str):
        try:
            body = json.dumps(body, cls=DjangoJSONEncoder)
        except Exception:
            body = str(body)
    return HttpResponse(body, content_type=content_type, status=status)


def num_encode(n):
    if n < 0:
        return SIGN_CHARACTER + num_encode(-n)
    s = []
    while True:
        n, r = divmod(n, BASE)
        s.append(ALPHABET[r])
        if n == 0:
            break
    return ''.join(reversed(s))


def num_decode(s):
    if s[0] == SIGN_CHARACTER:
        return -num_decode(s[1:])
    n = 0
    for c in s:
        n = n * BASE + ALPHABET_REVERSE[c]
    return n


def format_urls(a, values):
    b = []
    for i in a:
        j = i.copy()
        try:
            j['url'] = str(j['url']).format(**values)
        except KeyError:
            j['url'] = None
        b.append(j)
    return b


def build_abstract(resourcebase, url=None, includeURL=True):
    if resourcebase.abstract and url and includeURL:
        return "{abstract} -- [{url}]({url})".format(
            abstract=resourcebase.abstract, url=url)
    else:
        return resourcebase.abstract


def build_caveats(resourcebase):
    caveats = []
    if resourcebase.maintenance_frequency:
        caveats.append(resourcebase.maintenance_frequency_title())
    if resourcebase.license:
        caveats.append(resourcebase.license_verbose)
    if resourcebase.data_quality_statement:
        caveats.append(resourcebase.data_quality_statement)
    if len(caveats) > 0:
        return f"- {'%0A- '.join(caveats)}"
    else:
        return ""


def build_social_links(request, resourcebase):
    social_url = f"{'https' if request.is_secure() else 'http'}://{request.get_host()}{request.get_full_path()}"
    # Don't use datetime strftime() because it requires year >= 1900
    # see
    # https://docs.python.org/2/library/datetime.html#strftime-strptime-behavior
    date = '{0.month:02d}/{0.day:02d}/{0.year:4d}'.format(
        resourcebase.date) if resourcebase.date else None
    abstract = build_abstract(resourcebase, url=social_url, includeURL=True)
    caveats = build_caveats(resourcebase)
    hashtags = ",".join(getattr(settings, 'TWITTER_HASHTAGS', []))
    return format_urls(
        settings.SOCIAL_ORIGINS,
        {
            'name': resourcebase.title,
            'date': date,
            'abstract': abstract,
            'caveats': caveats,
            'hashtags': hashtags,
            'url': social_url})


def check_shp_columnnames(layer):
    """ Check if shapefile for a given layer has valid column names.
        If not, try to fix column names and warn the user
    """
    # TODO we may add in a better location this method
    inShapefile = ''
    for f in layer.upload_session.layerfile_set.all():
        if os.path.splitext(f.file.name)[1] == '.shp':
            inShapefile = f.file.path
    if inShapefile:
        return fixup_shp_columnnames(inShapefile, layer.charset)


def clone_shp_field_defn(srcFieldDefn, name):
    """
    Clone an existing ogr.FieldDefn with a new name
    """
    dstFieldDefn = ogr.FieldDefn(name, srcFieldDefn.GetType())
    dstFieldDefn.SetWidth(srcFieldDefn.GetWidth())
    dstFieldDefn.SetPrecision(srcFieldDefn.GetPrecision())

    return dstFieldDefn


def rename_shp_columnnames(inLayer, fieldnames):
    """
    Rename columns in a layer to those specified in the given mapping
    """
    inLayerDefn = inLayer.GetLayerDefn()

    for i in range(inLayerDefn.GetFieldCount()):
        srcFieldDefn = inLayerDefn.GetFieldDefn(i)
        dstFieldName = fieldnames.get(srcFieldDefn.GetName())

        if dstFieldName is not None:
            dstFieldDefn = clone_shp_field_defn(srcFieldDefn, dstFieldName)
            inLayer.AlterFieldDefn(i, dstFieldDefn, ogr.ALTER_NAME_FLAG)


def fixup_shp_columnnames(inShapefile, charset, tempdir=None):
    """ Try to fix column names and warn the user
    """
    charset = charset if charset and 'undefined' not in charset else 'UTF-8'

    if not tempdir:
        tempdir = tempfile.mkdtemp(dir=settings.STATIC_ROOT)

    if is_zipfile(inShapefile):
        inShapefile = unzip_file(inShapefile, '.shp', tempdir=tempdir)

    inDriver = ogr.GetDriverByName('ESRI Shapefile')
    try:
        inDataSource = inDriver.Open(inShapefile, 1)
    except Exception:
        tb = traceback.format_exc()
        logger.debug(tb)
        inDataSource = None

    if inDataSource is None:
        logger.debug(f"Could not open {inShapefile}")
        return False, None, None
    else:
        inLayer = inDataSource.GetLayer()

    # TODO we may need to improve this regexp
    # first character must be any letter or "_"
    # following characters can be any letter, number, "#", ":"
    regex = r'^[a-zA-Z,_][a-zA-Z,_#:\d]*$'
    a = re.compile(regex)
    regex_first_char = r'[a-zA-Z,_]{1}'
    b = re.compile(regex_first_char)
    inLayerDefn = inLayer.GetLayerDefn()

    list_col_original = []
    list_col = {}

    for i in range(inLayerDefn.GetFieldCount()):
        try:
            field_name = inLayerDefn.GetFieldDefn(i).GetName()
            if a.match(field_name):
                list_col_original.append(field_name)
        except Exception as e:
            logger.exception(e)
            return True, None, None

    for i in range(inLayerDefn.GetFieldCount()):
        try:
            field_name = inLayerDefn.GetFieldDefn(i).GetName()
            if not a.match(field_name):
                # once the field_name contains Chinese, to use slugify_zh
                if any('\u4e00' <= ch <= '\u9fff' for ch in field_name):
                    new_field_name = slugify_zh(field_name, separator='_')
                else:
                    new_field_name = slugify(field_name)
                if not b.match(new_field_name):
                    new_field_name = f"_{new_field_name}"
                j = 0
                while new_field_name in list_col_original or new_field_name in list_col.values():
                    if j == 0:
                        new_field_name += '_0'
                    if new_field_name.endswith(f"_{str(j)}"):
                        j += 1
                        new_field_name = f"{new_field_name[:-2]}_{str(j)}"
                if field_name != new_field_name:
                    list_col[field_name] = new_field_name
        except Exception as e:
            logger.exception(e)
            return True, None, None

    if len(list_col) == 0:
        return True, None, None
    else:
        try:
            rename_shp_columnnames(inLayer, list_col)
            inDataSource.SyncToDisk()
            inDataSource.Destroy()
        except Exception as e:
            logger.exception(e)
            raise GeoNodeException(
                f"Could not decode SHAPEFILE attributes by using the specified charset '{charset}'.")
    return True, None, list_col


def id_to_obj(id_):
    if id_ == id_none:
        return None

    for obj in gc.get_objects():
        if id(obj) == id_:
            return obj
    raise Exception("Not found")


def printsignals():
    for signalname in signalnames:
        logger.debug(f"SIGNALNAME: {signalname}")
        signaltype = getattr(models.signals, signalname)
        signals = signaltype.receivers[:]
        for signal in signals:
            logger.debug(signal)


class DisableDjangoSignals:
    """
    Python3 class temporarily disabling django signals on model creation.

    usage:
    with DisableDjangoSignals():
        # do some fancy stuff here
    """

    def __init__(self, disabled_signals=None, skip=False):
        self.skip = skip
        self.stashed_signals = defaultdict(list)
        self.disabled_signals = disabled_signals or [
            signals.pre_init, signals.post_init,
            signals.pre_save, signals.post_save,
            signals.pre_delete, signals.post_delete,
            signals.pre_migrate, signals.post_migrate,
            signals.m2m_changed,
        ]

    def __enter__(self):
        if not self.skip:
            for signal in self.disabled_signals:
                self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if not self.skip:
            for signal in list(self.stashed_signals):
                self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]


def run_subprocess(*cmd, **kwargs):
    p = subprocess.Popen(
        ' '.join(cmd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        **kwargs)
    stdout = StringIO()
    stderr = StringIO()
    buff_size = 1024
    while p.poll() is None:
        inr = [p.stdout.fileno(), p.stderr.fileno()]
        inw = []
        rlist, wlist, xlist = select.select(inr, inw, [])

        for r in rlist:
            if r == p.stdout.fileno():
                readfrom = p.stdout
                readto = stdout
            else:
                readfrom = p.stderr
                readto = stderr
            readto.write(readfrom.read(buff_size))

        for w in wlist:
            w.write('')

    return p.returncode, stdout.getvalue(), stderr.getvalue()


def parse_datetime(value):
    for patt in settings.DATETIME_INPUT_FORMATS:
        try:
            if isinstance(value, dict):
                value_obj = value['$'] if '$' in value else value['content']
                return datetime.datetime.strptime(value_obj, patt)
            else:
                return datetime.datetime.strptime(value, patt)
        except Exception:
            # tb = traceback.format_exc()
            # logger.error(tb)
            pass
    raise ValueError(f"Invalid datetime input: {value}")


def _convert_sql_params(cur, query):
    # sqlite driver doesn't support %(key)s notation,
    # use :key instead.
    if cur.db.vendor in ('sqlite', 'sqlite3', 'spatialite',):
        return SQL_PARAMS_RE.sub(r':\1', query)
    return query


@transaction.atomic
def raw_sql(query, params=None, ret=True):
    """
    Execute raw query
    param ret=True returns data from cursor as iterator
    """
    with connection.cursor() as c:
        query = _convert_sql_params(c, query)
        c.execute(query, params)
        if ret:
            desc = [r[0] for r in c.description]
            for row in c:
                yield dict(zip(desc, row))


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_client_host(request):
    hostname = None
    http_host = request.META.get('HTTP_HOST')
    if http_host:
        hostname = http_host.split(':')[0]
    return hostname


def check_ogc_backend(backend_package):
    """Check that geonode use a particular OGC Backend integration

    :param backend_package: django app of backend to use
    :type backend_package: str

    :return: bool
    :rtype: bool
    """
    ogc_conf = settings.OGC_SERVER['default']
    is_configured = ogc_conf.get('BACKEND') == backend_package

    # Check environment variables
    _backend = os.environ.get('BACKEND', None)
    if _backend:
        return backend_package == _backend and is_configured

    # Check exists in INSTALLED_APPS
    try:
        in_installed_apps = backend_package in settings.INSTALLED_APPS
        return in_installed_apps and is_configured
    except Exception:
        pass
    return False


class HttpClient(object):

    def __init__(self):
        self.timeout = 30
        self.retries = 3
        self.pool_maxsize = 10
        self.backoff_factor = 0.3
        self.pool_connections = 10
        self.status_forcelist = (500, 502, 503, 504)
        self.username = 'admin'
        self.password = 'admin'
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            ogc_server_settings = settings.OGC_SERVER['default']
            self.timeout = ogc_server_settings.get('TIMEOUT', 60)
            self.retries = ogc_server_settings.get('MAX_RETRIES', 5)
            self.backoff_factor = ogc_server_settings.get('BACKOFF_FACTOR', 0.3)
            self.pool_maxsize = ogc_server_settings.get('POOL_MAXSIZE', 10)
            self.pool_connections = ogc_server_settings.get('POOL_CONNECTIONS', 10)
            self.username = ogc_server_settings.get('USER', 'admin')
            self.password = ogc_server_settings.get('PASSWORD', 'geoserver')

    def request(self, url, method='GET', data=None, headers={}, stream=False,
                timeout=None, retries=None, user=None, verify=False):
        if (user or self.username != 'admin') and \
                check_ogc_backend(geoserver.BACKEND_PACKAGE) and 'Authorization' not in headers:
            if connection.cursor().db.vendor not in ('sqlite', 'sqlite3', 'spatialite'):
                try:
                    if user and isinstance(user, str):
                        user = get_user_model().objects.get(username=user)
                    _u = user or get_user_model().objects.get(username=self.username)
                    access_token = get_or_create_token(_u)
                    if access_token and not access_token.is_expired():
                        headers['Authorization'] = f'Bearer {access_token.token}'
                except Exception:
                    tb = traceback.format_exc()
                    logger.debug(tb)
            elif user == self.username:
                valid_uname_pw = base64.b64encode(
                    f"{self.username}:{self.password}".encode()).decode()
                headers['Authorization'] = f'Basic {valid_uname_pw}'

        response = None
        content = None
        session = requests.Session()
        retry = Retry(
            total=retries or self.retries,
            read=retries or self.retries,
            connect=retries or self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry,
            pool_maxsize=self.pool_maxsize,
            pool_connections=self.pool_connections
        )
        session.mount("{scheme}://".format(scheme=urlsplit(url).scheme), adapter)
        session.verify = False
        action = getattr(session, method.lower(), None)
        if action:
            _req_tout = timeout or self.timeout
            try:
                response = action(
                    url=url,
                    data=data,
                    headers=headers,
                    timeout=_req_tout,
                    stream=stream,
                    verify=verify)
            except (requests.exceptions.RequestException, ValueError) as e:
                msg = f"Request exception [{e}] - TOUT [{_req_tout}] to URL: {url} - headers: {headers}"
                logger.exception(Exception(msg))
                response = None
        else:
            response = session.get(url, headers=headers, timeout=self.timeout)

        try:
            content = ensure_string(response.content) if not stream else response.raw
        except Exception:
            content = None

        return (response, content)

    def get(self, url, data=None, headers={}, stream=False, timeout=None, user=None, verify=False):
        return self.request(url,
                            method='GET',
                            data=data,
                            headers=headers,
                            timeout=timeout or self.timeout,
                            stream=stream,
                            user=user,
                            verify=verify)

    def post(self, url, data=None, headers={}, stream=False, timeout=None, user=None, verify=False):
        return self.request(url,
                            method='POST',
                            data=data,
                            headers=headers,
                            timeout=timeout or self.timeout,
                            stream=stream,
                            user=user,
                            verify=verify)


http_client = HttpClient()


def get_dir_time_suffix():
    """Returns the name of a folder with the 'now' time as suffix"""
    dirfmt = "%4d-%02d-%02d_%02d%02d%02d"
    now = time.localtime()[0:6]
    dirname = dirfmt % now

    return dirname


def zip_dir(basedir, archivename):
    assert os.path.isdir(basedir)
    with closing(ZipFile(archivename, "w", ZIP_DEFLATED, allowZip64=True)) as z:
        for root, dirs, files in os.walk(basedir):
            # NOTE: ignore empty directories
            for fn in files:
                absfn = os.path.join(root, fn)
                zfn = absfn[len(basedir) + len(os.sep):]  # XXX: relative path
                z.write(absfn, zfn)


def copy_tree(src, dst, symlinks=False, ignore=None):
    try:
        for item in os.listdir(src):
            s = os.path.join(src, item)
            d = os.path.join(dst, item)
            if os.path.isdir(s):
                # shutil.rmtree(d)
                if os.path.exists(d):
                    try:
                        os.remove(d)
                    except Exception:
                        try:
                            shutil.rmtree(d)
                        except Exception:
                            pass
                try:
                    shutil.copytree(s, d, symlinks=symlinks, ignore=ignore)
                except Exception:
                    pass
            else:
                try:
                    if ignore and s in ignore(dst, [s]):
                        return
                    shutil.copy2(s, d)
                except Exception:
                    pass
    except Exception:
        traceback.print_exc()


def extract_archive(zip_file, dst):
    target_folder = os.path.join(dst, os.path.splitext(os.path.basename(zip_file))[0])
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)

    with ZipFile(zip_file, "r", allowZip64=True) as z:
        z.extractall(target_folder)

    return target_folder


def chmod_tree(dst, permissions=0o777):
    for dirpath, dirnames, filenames in os.walk(dst):
        for filename in filenames:
            path = os.path.join(dirpath, filename)
            os.chmod(path, permissions)
            status = os.stat(path)
            if oct(status.st_mode & 0o777) != str(oct(permissions)):
                raise Exception(f"Could not update permissions of {path}")

        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            os.chmod(path, permissions)
            status = os.stat(path)
            if oct(status.st_mode & 0o777) != str(oct(permissions)):
                raise Exception(f"Could not update permissions of {path}")


def slugify_zh(text, separator='_'):
    """
    Make a slug from the given text, which is simplified from slugify.
    It remove the other args and do not convert Chinese into Pinyin
    :param text (str): initial text
    :param separator (str): separator between words
    :return (str):
    """

    QUOTE_PATTERN = re.compile(r'[\']+')
    ALLOWED_CHARS_PATTERN = re.compile('[^\u4e00-\u9fa5a-z0-9]+')
    DUPLICATE_DASH_PATTERN = re.compile('-{2,}')
    NUMBERS_PATTERN = re.compile(r'(?<=\d),(?=\d)')
    DEFAULT_SEPARATOR = '-'

    # if not isinstance(text, types.UnicodeType):
    #    text = unicode(text, 'utf-8', 'ignore')
    # replace quotes with dashes - pre-process
    text = QUOTE_PATTERN.sub(DEFAULT_SEPARATOR, text)
    # make the text lowercase
    text = text.lower()
    # remove generated quotes -- post-process
    text = QUOTE_PATTERN.sub('', text)
    # cleanup numbers
    text = NUMBERS_PATTERN.sub('', text)
    # replace all other unwanted characters
    text = re.sub(ALLOWED_CHARS_PATTERN, DEFAULT_SEPARATOR, text)
    # remove redundant
    text = re.sub(DUPLICATE_DASH_PATTERN, DEFAULT_SEPARATOR, text).strip(DEFAULT_SEPARATOR)
    if separator != DEFAULT_SEPARATOR:
        text = text.replace(DEFAULT_SEPARATOR, separator)
    return text


def set_resource_default_links(instance, layer, prune=False, **kwargs):

    from geonode.base.models import Link
    from django.urls import reverse
    from django.utils.translation import ugettext

    # Prune old links
    if prune:
        logger.debug(" -- Resource Links[Prune old links]...")
        _def_link_types = (
            'data', 'image', 'original', 'html', 'OGC:WMS', 'OGC:WFS', 'OGC:WCS')
        Link.objects.filter(resource=instance.resourcebase_ptr, link_type__in=_def_link_types).delete()
        logger.debug(" -- Resource Links[Prune old links]...done!")

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        from geonode.geoserver.ows import wcs_links, wfs_links, wms_links
        from geonode.geoserver.helpers import ogc_server_settings, gs_catalog

        # Compute parameters for the new links
        logger.debug(" -- Resource Links[Compute parameters for the new links]...")
        height = 550
        width = 550

        # Parse Layer BBOX and SRID
        bbox = None
        srid = instance.srid if instance.srid else getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:4326')
        if instance.srid and instance.bbox_x0:
            bbox = ','.join(str(x) for x in [instance.bbox_x0, instance.bbox_y0,
                                             instance.bbox_x1, instance.bbox_y1])
        else:
            try:
                gs_resource = gs_catalog.get_resource(
                    name=instance.name,
                    workspace=instance.workspace)
                if not gs_resource:
                    gs_resource = gs_catalog.get_resource(
                        name=instance.name,
                        store=instance.store,
                        workspace=instance.workspace)
                if not gs_resource:
                    gs_resource = gs_catalog.get_resource(name=instance.name)
                bbox = gs_resource.native_bbox

                dx = float(bbox[1]) - float(bbox[0])
                dy = float(bbox[3]) - float(bbox[2])
                dataAspect = 1 if dy == 0 else dx / dy
                width = int(height * dataAspect)

                srid = bbox[4]
                bbox = ','.join(str(x) for x in [bbox[0], bbox[2], bbox[1], bbox[3]])
            except Exception as e:
                logger.exception(e)

        # Create Raw Data download link
        if settings.DISPLAY_ORIGINAL_DATASET_LINK:
            logger.debug(" -- Resource Links[Create Raw Data download link]...")
            download_url = urljoin(settings.SITEURL,
                                   reverse('download', args=[instance.id]))
            while Link.objects.filter(
                    resource=instance.resourcebase_ptr,
                    url=download_url).count() > 1:
                Link.objects.filter(
                    resource=instance.resourcebase_ptr,
                    url=download_url).first().delete()
            Link.objects.update_or_create(
                resource=instance.resourcebase_ptr,
                url=download_url,
                defaults=dict(
                    extension='zip',
                    name='Original Dataset',
                    mime='application/octet-stream',
                    link_type='original',
                )
            )
            logger.debug(" -- Resource Links[Create Raw Data download link]...done!")
        else:
            Link.objects.filter(resource=instance.resourcebase_ptr,
                                name='Original Dataset').delete()

        # Set download links for WMS, WCS or WFS and KML
        logger.debug(" -- Resource Links[Set download links for WMS, WCS or WFS and KML]...")
        links = wms_links(f"{ogc_server_settings.public_url}ows?",
                          instance.alternate,
                          bbox,
                          srid,
                          height,
                          width)

        for ext, name, mime, wms_url in links:
            try:
                Link.objects.update_or_create(
                    resource=instance.resourcebase_ptr,
                    name=ugettext(name),
                    defaults=dict(
                        extension=ext,
                        url=wms_url,
                        mime=mime,
                        link_type='image',
                    )
                )
            except Link.MultipleObjectsReturned:
                _d = dict(extension=ext,
                          url=wms_url,
                          mime=mime,
                          link_type='image')
                Link.objects.filter(resource=instance.resourcebase_ptr,
                                    name=ugettext(name),
                                    link_type='image').update(**_d)

        if instance.storeType == "dataStore":
            links = wfs_links(f"{ogc_server_settings.public_url}ows?",
                              instance.alternate,
                              bbox=None,  # bbox filter should be set at runtime otherwise conflicting with CQL
                              srid=srid)
            for ext, name, mime, wfs_url in links:
                if mime == 'SHAPE-ZIP':
                    name = 'Zipped Shapefile'
                if (Link.objects.filter(resource=instance.resourcebase_ptr,
                                        url=wfs_url,
                                        name=name,
                                        link_type='data').count() < 2):
                    Link.objects.update_or_create(
                        resource=instance.resourcebase_ptr,
                        url=wfs_url,
                        name=name,
                        link_type='data',
                        defaults=dict(
                            extension=ext,
                            mime=mime,
                        )
                    )

        elif instance.storeType == 'coverageStore':
            links = wcs_links(f"{ogc_server_settings.public_url}wcs?",
                              instance.alternate,
                              bbox,
                              srid)

        for ext, name, mime, wcs_url in links:
            if (Link.objects.filter(resource=instance.resourcebase_ptr,
                                    url=wcs_url,
                                    name=name,
                                    link_type='data').count() < 2):
                Link.objects.update_or_create(
                    resource=instance.resourcebase_ptr,
                    url=wcs_url,
                    name=name,
                    link_type='data',
                    defaults=dict(
                        extension=ext,
                        mime=mime,
                    )
                )

        site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
        html_link_url = f'{site_url}{instance.get_absolute_url()}'

        if (Link.objects.filter(resource=instance.resourcebase_ptr,
                                url=html_link_url,
                                name=instance.alternate,
                                link_type='html').count() < 2):
            Link.objects.update_or_create(
                resource=instance.resourcebase_ptr,
                url=html_link_url,
                name=instance.alternate,
                link_type='html',
                defaults=dict(
                    extension='html',
                    mime='text/html',
                )
            )
        logger.debug(" -- Resource Links[Set download links for WMS, WCS or WFS and KML]...done!")

        # Legend link
        logger.debug(" -- Resource Links[Legend link]...")
        try:
            for style in set(list(instance.styles.all()) + [instance.default_style, ]):
                if style:
                    style_name = os.path.basename(
                        urlparse(style.sld_url).path).split('.')[0]
                    legend_url = ogc_server_settings.PUBLIC_LOCATION + \
                        'ows?service=WMS&request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
                        instance.alternate + '&STYLE=' + style_name + \
                        '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'

                    if Link.objects.filter(resource=instance.resourcebase_ptr, url=legend_url).count() < 2:
                        Link.objects.update_or_create(
                            resource=instance.resourcebase_ptr,
                            name='Legend',
                            url=legend_url,
                            defaults=dict(
                                extension='png',
                                url=legend_url,
                                mime='image/png',
                                link_type='image',
                            )
                        )
            logger.debug(" -- Resource Links[Legend link]...done!")
        except Exception as e:
            logger.debug(f" -- Resource Links[Legend link]...error: {e}")

        # Thumbnail link
        logger.debug(" -- Resource Links[Thumbnail link]...")
        if (Link.objects.filter(resource=instance.resourcebase_ptr,
                                url=instance.get_thumbnail_url(),
                                name='Thumbnail').count() < 2):
            Link.objects.update_or_create(
                resource=instance.resourcebase_ptr,
                url=instance.get_thumbnail_url(),
                name='Thumbnail',
                defaults=dict(
                    extension='png',
                    mime='image/png',
                    link_type='image',
                )
            )
        logger.debug(" -- Resource Links[Thumbnail link]...done!")

        logger.debug(" -- Resource Links[OWS Links]...")
        # ogc_wms_path = '%s/ows' % instance.workspace
        ogc_wms_path = 'ows'
        ogc_wms_url = urljoin(ogc_server_settings.public_url, ogc_wms_path)
        ogc_wms_name = f'OGC WMS: {instance.workspace} Service'
        if Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wms_name, url=ogc_wms_url).count() < 2:
            Link.objects.get_or_create(
                resource=instance.resourcebase_ptr,
                url=ogc_wms_url,
                name=ogc_wms_name,
                defaults=dict(
                    extension='html',
                    url=ogc_wms_url,
                    mime='text/html',
                    link_type='OGC:WMS',
                )
            )

        if instance.storeType == "dataStore":
            # ogc_wfs_path = '%s/wfs' % instance.workspace
            ogc_wfs_path = 'ows'
            ogc_wfs_url = urljoin(ogc_server_settings.public_url, ogc_wfs_path)
            ogc_wfs_name = f'OGC WFS: {instance.workspace} Service'
            if Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wfs_name, url=ogc_wfs_url).count() < 2:
                Link.objects.get_or_create(
                    resource=instance.resourcebase_ptr,
                    url=ogc_wfs_url,
                    name=ogc_wfs_name,
                    defaults=dict(
                        extension='html',
                        url=ogc_wfs_url,
                        mime='text/html',
                        link_type='OGC:WFS',
                    )
                )

        if instance.storeType == "coverageStore":
            # ogc_wcs_path = '%s/wcs' % instance.workspace
            ogc_wcs_path = 'ows'
            ogc_wcs_url = urljoin(ogc_server_settings.public_url, ogc_wcs_path)
            ogc_wcs_name = f'OGC WCS: {instance.workspace} Service'
            if Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wcs_name, url=ogc_wcs_url).count() < 2:
                Link.objects.get_or_create(
                    resource=instance.resourcebase_ptr,
                    url=ogc_wcs_url,
                    name=ogc_wcs_name,
                    defaults=dict(
                        extension='html',
                        url=ogc_wcs_url,
                        mime='text/html',
                        link_type='OGC:WCS',
                    )
                )
        logger.debug(" -- Resource Links[OWS Links]...done!")
    elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
        from geonode.layers.models import LayerFile
        from geonode.qgis_server.helpers import (
            tile_url_format, style_list, create_qgis_project)
        from geonode.qgis_server.models import QGISServerLayer

        # args
        is_shapefile = kwargs.pop('is_shapefile', False)
        original_ext = kwargs.pop('original_ext', None)

        # base url for geonode
        base_url = settings.SITEURL

        # Set Link for Download Raw in Zip File
        zip_download_url = reverse(
            'qgis_server:download-zip', kwargs={'layername': instance.name})
        zip_download_url = urljoin(base_url, zip_download_url)
        logger.debug(f'zip_download_url: {zip_download_url}')
        if is_shapefile:
            link_name = 'Zipped Shapefile'
            link_mime = 'SHAPE-ZIP'
        else:
            link_name = 'Zipped All Files'
            link_mime = 'ZIP'

        # Zip file
        Link.objects.update_or_create(
            resource=instance.resourcebase_ptr,
            name=link_name,
            defaults=dict(
                extension='zip',
                mime=link_mime,
                url=zip_download_url,
                link_type='data'
            )
        )

        # WMS link layer workspace
        ogc_wms_url = urljoin(
            settings.SITEURL,
            reverse(
                'qgis_server:layer-request', kwargs={'layername': instance.name}))
        ogc_wms_name = f'OGC WMS: {instance.workspace} Service'
        ogc_wms_link_type = 'OGC:WMS'
        Link.objects.update_or_create(
            resource=instance.resourcebase_ptr,
            name=ogc_wms_name,
            link_type=ogc_wms_link_type,
            defaults=dict(
                extension='html',
                url=ogc_wms_url,
                mime='text/html',
                link_type=ogc_wms_link_type
            )
        )

        # QGS link layer workspace
        ogc_qgs_url = urljoin(
            base_url,
            reverse(
                'qgis_server:download-qgs',
                kwargs={'layername': instance.name}))
        logger.debug(f'qgs_download_url: {ogc_qgs_url}')
        link_name = 'QGIS project file (.qgs)'
        link_mime = 'application/xml'
        Link.objects.update_or_create(
            resource=instance.resourcebase_ptr,
            name=link_name,
            defaults=dict(
                extension='qgs',
                mime=link_mime,
                url=ogc_qgs_url,
                link_type='data'
            )
        )

        if instance.is_vector():
            # WFS link layer workspace
            ogc_wfs_url = urljoin(
                settings.SITEURL,
                reverse(
                    'qgis_server:layer-request',
                    kwargs={'layername': instance.name}))
            ogc_wfs_name = f'OGC WFS: {instance.workspace} Service'
            ogc_wfs_link_type = 'OGC:WFS'
            Link.objects.update_or_create(
                resource=instance.resourcebase_ptr,
                name=ogc_wfs_name,
                link_type=ogc_wfs_link_type,
                defaults=dict(
                    extension='html',
                    url=ogc_wfs_url,
                    mime='text/html',
                    link_type=ogc_wfs_link_type
                )
            )

        # QLR link layer workspace
        ogc_qlr_url = urljoin(
            base_url,
            reverse(
                'qgis_server:download-qlr',
                kwargs={'layername': instance.name}))
        logger.debug(f'qlr_download_url: {ogc_qlr_url}')
        link_name = 'QGIS layer file (.qlr)'
        link_mime = 'application/xml'
        Link.objects.update_or_create(
            resource=instance.resourcebase_ptr,
            name=link_name,
            defaults=dict(
                extension='qlr',
                mime=link_mime,
                url=ogc_qlr_url,
                link_type='data'
            )
        )

        # if layer has overwrite attribute, then it probably comes from
        # importlayers management command and needs to be overwritten
        overwrite = getattr(instance, 'overwrite', False)

        # Create the QGIS Project
        response = create_qgis_project(
            instance, layer.qgis_project_path, overwrite=overwrite,
            internal=True)

        logger.debug(f'Creating the QGIS Project : {response.url}')
        if ensure_string(response.content) != 'OK':
            logger.debug(f'Result : {ensure_string(response.content)}')

        # Generate style model cache
        style_list(instance, internal=False)

        # Remove QML file if necessary
        try:
            qml_file = instance.upload_session.layerfile_set.get(name='qml')
            if not os.path.exists(qml_file.file.path):
                qml_file.delete()
        except LayerFile.DoesNotExist:
            pass

        Link.objects.update_or_create(
            resource=instance.resourcebase_ptr,
            name="Tiles",
            defaults=dict(
                url=tile_url_format(instance.name),
                extension='tiles',
                mime='image/png',
                link_type='image'
            )
        )

        if original_ext.split('.')[-1] in QGISServerLayer.geotiff_format:
            # geotiff link
            geotiff_url = reverse(
                'qgis_server:geotiff', kwargs={'layername': instance.name})
            geotiff_url = urljoin(base_url, geotiff_url)
            logger.debug(f'geotif_url: {geotiff_url}')

            Link.objects.update_or_create(
                resource=instance.resourcebase_ptr,
                name="GeoTIFF",
                defaults=dict(
                    extension=original_ext.split('.')[-1],
                    url=geotiff_url,
                    mime='image/tiff',
                    link_type='image'
                )
            )

        # Create legend link
        legend_url = reverse(
            'qgis_server:legend',
            kwargs={'layername': instance.name}
        )
        legend_url = urljoin(base_url, legend_url)
        Link.objects.update_or_create(
            resource=instance.resourcebase_ptr,
            name='Legend',
            defaults=dict(
                extension='png',
                url=legend_url,
                mime='image/png',
                link_type='image',
            )
        )


def add_url_params(url, params):
    """ Add GET params to provided URL being aware of existing.

    :param url: string of target URL
    :param params: dict containing requested params to be added
    :return: string with updated URL

    >> url = 'http://stackoverflow.com/test?answers=true'
    >> new_params = {'answers': False, 'data': ['some','values']}
    >> add_url_params(url, new_params)
    'http://stackoverflow.com/test?data=some&data=values&answers=false'
    """
    # Unquoting URL first so we don't loose existing args
    url = unquote(url)
    # Extracting url info
    parsed_url = urlparse(url)
    # Extracting URL arguments from parsed URL
    get_args = parsed_url.query
    # Converting URL arguments to dict
    parsed_get_args = dict(parse_qsl(get_args))
    # Merging URL arguments dict with new params
    parsed_get_args.update(params)

    # Bool and Dict values should be converted to json-friendly values
    # you may throw this part away if you don't like it :)
    parsed_get_args.update(
        {k: json.dumps(v) for k, v in parsed_get_args.items()
         if isinstance(v, (bool, dict))}
    )

    # Converting URL argument to proper query string
    encoded_get_args = urlencode(parsed_get_args, doseq=True)
    # Creating new parsed result object based on provided with new
    # URL arguments. Same thing happens inside of urlparse.
    new_url = ParseResult(
        parsed_url.scheme, parsed_url.netloc, parsed_url.path,
        parsed_url.params, encoded_get_args, parsed_url.fragment
    ).geturl()

    return new_url


json_serializer_k_map = {
    'user': settings.AUTH_USER_MODEL,
    'owner': settings.AUTH_USER_MODEL,
    'restriction_code_type': 'base.RestrictionCodeType',
    'license': 'base.License',
    'category': 'base.TopicCategory',
    'spatial_representation_type': 'base.SpatialRepresentationType',
    'group': 'auth.Group',
    'default_style': 'layers.Style',
    'upload_session': 'layers.UploadSession'
}


def json_serializer_producer(dictionary):
    """
     - usage:
            serialized_obj =
                json_serializer_producer(model_to_dict(instance))

     - dump to file:
        with open('data.json', 'w') as outfile:
            json.dump(serialized_obj, outfile)

     - read from file:
        with open('data.json', 'r') as infile:
            serialized_obj = json.load(infile)
    """
    def to_json(keys):
        if isinstance(keys, datetime.datetime):
            return str(keys)
        elif isinstance(keys, str) or isinstance(keys, int):
            return keys
        elif isinstance(keys, dict):
            return json_serializer_producer(keys)
        elif isinstance(keys, list):
            return [json_serializer_producer(model_to_dict(k)) for k in keys]
        elif isinstance(keys, models.Model):
            return json_serializer_producer(model_to_dict(keys))
        elif isinstance(keys, Decimal):
            return float(keys)
        else:
            return str(keys)

    output = {}

    _keys_to_skip = [
        'email',
        'password',
        'last_login',
        'date_joined',
        'is_staff',
        'is_active',
        'is_superuser',
        'permissions',
        'user_permissions',
    ]

    for (x, y) in dictionary.items():
        if x not in _keys_to_skip:
            if x in json_serializer_k_map.keys():
                instance = django_apps.get_model(
                    json_serializer_k_map[x], require_ready=False)
                if instance.objects.filter(id=y):
                    _obj = instance.objects.get(id=y)
                    y = model_to_dict(_obj)
            output[x] = to_json(y)
    return output


def is_monochromatic_image(image_url, image_data=None):

    def is_local_static(url):
        if url.startswith(settings.STATIC_URL) or \
                (url.startswith(settings.SITEURL) and settings.STATIC_URL in url):
            return True
        return False

    def is_absolute(url):
        return bool(urlparse(url).netloc)

    def get_thumb_handler(url):
        _index = url.find(settings.STATIC_URL)
        _thumb_path = urlparse(url[_index + len(settings.STATIC_URL):]).path
        if storage.exists(_thumb_path):
            return storage.open(_thumb_path)
        return None

    def verify_image(stream):
        with Image.open(stream) as _stream:
            img = _stream.convert("L")
            img.verify()  # verify that it is, in fact an image
            extr = img.getextrema()
            a = 0
            for i in extr:
                if isinstance(i, tuple):
                    a += abs(i[0] - i[1])
                else:
                    a = abs(extr[0] - extr[1])
                    break
            return a == 0

    try:
        if image_data:
            logger.debug("...Checking if image is a blank image")
            with BytesIO(image_data) as stream:
                return verify_image(stream)
        elif image_url:
            logger.debug(f"...Checking if '{image_url}' is a blank image")
            url = image_url if is_absolute(image_url) else urljoin(settings.SITEURL, image_url)
            if not is_local_static(url):
                req, stream_content = http_client.get(url, timeout=5)
                with BytesIO(stream_content) as stream:
                    return verify_image(stream)
            else:
                with get_thumb_handler(url) as stream:
                    return verify_image(stream)
        return True
    except Exception as e:
        logger.exception(e)
        return False
