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
import six
import ast
import copy
import time
import base64
import logging
import select
import shutil
import string
import urllib
import tarfile
import weakref
import datetime
import requests
import tempfile
import urlparse
import traceback
import subprocess

from osgeo import ogr
from slugify import slugify
from StringIO import StringIO
from contextlib import closing
from math import atan, exp, log, pi, sin, tan, floor
from zipfile import ZipFile, is_zipfile, ZIP_DEFLATED
from requests.packages.urllib3.util.retry import Retry

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.utils.http import is_safe_url
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
# use lazy gettext because some translated strings are used before
# i18n infra is up
from django.utils.translation import ugettext_lazy as _
from django.db import models, connection, transaction
from django.contrib.gis.geos import GEOSGeometry
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth import get_user_model
from geonode import geoserver, qgis_server, GeoNodeException  # noqa
from geonode.base.auth import (extend_token,
                               get_or_create_token,
                               get_token_from_auth_header,
                               get_token_object_from_session)

try:
    import json
except ImportError:
    from django.utils import simplejson as json

DEFAULT_TITLE = ""
DEFAULT_ABSTRACT = ""

INVALID_PERMISSION_MESSAGE = _("Invalid permission level.")

ALPHABET = string.ascii_uppercase + string.ascii_lowercase + \
    string.digits + '-_'
ALPHABET_REVERSE = dict((c, i) for (i, c) in enumerate(ALPHABET))
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
        tempdir = tempfile.mkdtemp()
    if not os.path.isdir(tempdir):
        os.makedirs(tempdir)

    the_zip = ZipFile(upload_file)
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
        tempdir = tempfile.mkdtemp()

    the_tar = tarfile.open(upload_file)
    the_tar.extractall(tempdir)
    for item in the_tar.getnames():
        if item.endswith(extension):
            absolute_base_file = os.path.join(tempdir, item)

    return absolute_base_file


def get_headers(request, url, raw_url, allowed_hosts=[]):
    headers = {}
    cookies = None
    csrftoken = None

    if settings.SESSION_COOKIE_NAME in request.COOKIES and is_safe_url(
            url=raw_url, host=url.hostname):
        cookies = request.META["HTTP_COOKIE"]

    for cook in request.COOKIES:
        name = str(cook)
        value = request.COOKIES.get(name)
        if name == 'csrftoken':
            csrftoken = value
        cook = "%s=%s" % (name, value)
        cookies = cook if not cookies else (cookies + '; ' + cook)

    csrftoken = get_token(request) if not csrftoken else csrftoken

    if csrftoken:
        headers['X-Requested-With'] = "XMLHttpRequest"
        headers['X-CSRFToken'] = csrftoken
        cook = "%s=%s" % ('csrftoken', csrftoken)
        cookies = cook if not cookies else (cookies + '; ' + cook)

    if cookies:
        if 'JSESSIONID' in request.session and request.session['JSESSIONID']:
            cookies = cookies + '; JSESSIONID=' + \
                request.session['JSESSIONID']
        headers['Cookie'] = cookies

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    access_token = None
    site_url = urlparse.urlsplit(settings.SITEURL)
    allowed_hosts += [url.hostname]
    # We want to convert HTTP_AUTH into a Beraer Token only when hitting the local GeoServer
    if site_url.hostname in allowed_hosts:
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
        headers['Authorization'] = 'Bearer %s' % access_token

    pragma = "no-cache"
    referer = request.META[
        "HTTP_REFERER"] if "HTTP_REFERER" in request.META else \
        "{scheme}://{netloc}/".format(scheme=site_url.scheme,
                                      netloc=site_url.netloc)
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
    username, password = base64.b64decode(auth).split(':')
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
            accum += ' ' + kw
            if kw.endswith('"'):
                keywords.append(accum[0:-1])
                accum = None
    if accum is not None:
        keywords.append(accum)
    return [kw.strip() for kw in keywords if kw.strip()]


def bbox_to_wkt(x0, x1, y0, y1, srid="4326"):
    if srid and str(srid).startswith('EPSG:'):
        srid = srid[5:]
    if None not in [x0, x1, y0, y1]:
        wkt = 'SRID=%s;POLYGON((%s %s,%s %s,%s %s,%s %s,%s %s))' % (
            srid, x0, y0, x0, y1, x1, y1, x1, y0, x0, y0)
    else:
        wkt = 'SRID=4326;POLYGON((-180 -90,-180 90,180 90,180 -90,-180 -90))'
    return wkt


def _v(coord, x, source_srid=4326, target_srid=3857):
    if source_srid == 4326 and x and abs(coord) != 180.0:
        coord = coord - (round(coord / 360.0) * 360.0)
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
    except BaseException:
        source_srid = target_srid

    if source_srid != target_srid:
        try:
            wkt = bbox_to_wkt(_v(minx, x=True, source_srid=source_srid, target_srid=target_srid),
                              _v(maxx, x=True, source_srid=source_srid, target_srid=target_srid),
                              _v(miny, x=False, source_srid=source_srid, target_srid=target_srid),
                              _v(maxy, x=False, source_srid=source_srid, target_srid=target_srid),
                              srid=source_srid)
            poly = GEOSGeometry(wkt, srid=source_srid)
            poly.transform(target_srid)
            projected_bbox = [str(x) for x in poly.extent]
            # Must be in the form : [x0, x1, y0, y1, EPSG:<target_srid>)
            return tuple([projected_bbox[0], projected_bbox[2], projected_bbox[1], projected_bbox[3]]) + \
                ("EPSG:%s" % target_srid,)
        except BaseException:
            tb = traceback.format_exc()
            logger.info(tb)

    return native_bbox


def bounds_to_zoom_level(bounds, width, height):
    WORLD_DIM = {'height': 256., 'width': 256.}
    ZOOM_MAX = 21

    def latRad(lat):
        _sin = sin(lat * pi / 180.0)
        if abs(_sin) != 1.0:
            radX2 = log((1.0 + _sin) / (1.0 - _sin)) / 2.0
        else:
            radX2 = log(1.0) / 2.0
        return max(min(radX2, pi), -pi) / 2.0

    def zoom(mapPx, worldPx, fraction):
        try:
            return floor(log(mapPx / worldPx / fraction) / log(2.0))
        except BaseException:
            return 0

    ne = [float(bounds[2]), float(bounds[3])]
    sw = [float(bounds[0]), float(bounds[1])]
    latFraction = (latRad(ne[1]) - latRad(sw[1])) / pi
    lngDiff = ne[0] - sw[0]
    lngFraction = ((lngDiff + 360.0) if (lngDiff < 0) else lngDiff) / 360.0
    latZoom = zoom(float(height), WORLD_DIM['height'], latFraction)
    lngZoom = zoom(float(width), WORLD_DIM['width'], lngFraction)
    ratio = float(max(width, height)) / float(min(width, height))
    z_offset = 0 if ratio >= 1.5 else -1
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
    x = lonlat[0] * 20037508.34 / 180
    try:
        # With data sets that only have one point the value of this
        # expression becomes negative infinity. In order to continue,
        # we wrap this in a try catch block.
        n = tan((90 + lonlat[1]) * pi / 360)
    except ValueError:
        n = 0
    if n <= 0:
        y = float("-inf")
    else:
        y = log(n) / pi * 20037508.34
    return (x, y)


def inverse_mercator(xy):
    """
        Given coordinates in spherical mercator, return a lon,lat tuple.
    """
    lon = (xy[0] / 20037508.34) * 180
    lat = (xy[1] / 20037508.34) * 180
    lat = 180 / pi * \
        (2 * atan(exp(lat * pi / 180)) - pi / 2)
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
              "fixed", "group", "visibility", "source", "getFeatureInfo"]:
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
        opacity=layer.get("opacity", 1),
        styles=styles,
        transparent=layer.get("transparent", False),
        fixed=layer.get("fixed", False),
        group=layer.get('group', None),
        visibility=layer.get("visibility", True),
        ows_url=source.get("url", None),
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
            cfg = cache.get("viewer_json_" +
                            str(self.id) +
                            "_" +
                            str(0 if user is None else user.id))
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

        configs = [l.source_config(access_token) for l in layers]

        i = 0
        for source in uniqify(configs):
            while str(i) in sources:
                i = i + 1
            sources[str(i)] = source
            server_lookup[json.dumps(source)] = str(i)

        def source_lookup(source):
            for k, v in sources.iteritems():
                if v == source:
                    return k
            return None

        def layer_config(l, user=None):
            cfg = l.layer_config(user=user)
            src_cfg = l.source_config(access_token)
            source = source_lookup(src_cfg)
            if source:
                cfg["source"] = source
            return cfg

        source_urls = [source['url']
                       for source in sources.values() if source and 'url' in source]

        if 'geonode.geoserver' in settings.INSTALLED_APPS:
            if len(sources.keys()) > 0 and \
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

        for idx, lyr in enumerate(settings.MAP_BASELAYERS):
            if _base_source(
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
                    'title': "[R] %s" % service.title
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
                'layers': [layer_config(l, user=user) for l in layers],
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
            layers = def_map_layers

        config["map"].update(_get_viewer_projection_info(self.projection))

        # Create user-specific cache of maplayer config
        if self is not None:
            cache.set("viewer_json_" +
                      str(self.id) +
                      "_" +
                      str(0 if user is None else user.id), config)

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
            for name, server in settings.OGC_SERVER.iteritems():
                url = urlparse.urlsplit(server['PUBLIC_LOCATION'])
                urls.append(url.netloc)

            my_url = urlparse.urlsplit(self.ows_url)

            if str(access_token) and my_url.netloc in urls:
                request_params = urlparse.parse_qs(my_url.query)
                if 'access_token' in request_params:
                    del request_params['access_token']
                # request_params['access_token'] = [access_token]
                encoded_params = urllib.urlencode(request_params, doseq=True)

                parsed_url = urlparse.SplitResult(
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
                    if isinstance(self.styles, six.string_types) else self.styles
            except BaseException:
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
            source=lyr["source"],
            ordering=order
        )

    DEFAULT_BASE_LAYERS = [
        _baselayer(
            lyr, idx) for idx, lyr in enumerate(
            settings.MAP_BASELAYERS)]

    DEFAULT_MAP_CONFIG = _default_map.viewer_json(
        request, *DEFAULT_BASE_LAYERS)

    return DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS


_viewer_projection_lookup = {
    "EPSG:900913": {
        "maxResolution": 156543.03390625,
        "units": "m",
        "maxExtent": [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
    },
    "EPSG:3857": {
        "maxResolution": 156543.03390625,
        "units": "m",
        "maxExtent": [-20037508.34, -20037508.34, 20037508.34, 20037508.34],
    },
    "EPSG:4326": {
        "max_resolution": (180 - (-180)) / 256,
        "units": "degrees",
        "maxExtent": [-180, -90, 180, 90]
    }
}


def _get_viewer_projection_info(srid):
    # TODO: Look up projection details in EPSG database
    return _viewer_projection_lookup.get(srid, {})


def resolve_object(request, model, query, permission='base.view_resourcebase',
                   permission_required=True, permission_msg=None):
    """Resolve an object using the provided query and check the optional
    permission. Model views should wrap this function as a shortcut.

    query - a dict to use for querying the model
    permission - an optional permission to check
    permission_required - if False, allow get methods to proceed
    permission_msg - optional message to use in 403
    """
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
                        request.user) and request.user not in obj_group_members:
                    obj_group_members.append(request.user)
            except GroupProfile.DoesNotExist:
                pass

    if settings.RESOURCE_PUBLISHING or settings.ADMIN_MODERATE_UPLOADS:
        is_admin = False
        is_manager = False
        is_owner = True if request.user == obj_to_check.owner else False
        if request.user:
            is_admin = request.user.is_superuser if request.user else False
            try:
                is_manager = request.user.groupmember_set.all().filter(role='manager').exists()
            except BaseException:
                is_manager = False
        if (not obj_to_check.is_published):
            if not is_admin:
                if is_owner or (
                        is_manager and request.user in obj_group_managers):
                    if (not request.user.has_perm('publish_resourcebase', obj_to_check)) and (
                        not request.user.has_perm('view_resourcebase', obj_to_check)) and (
                            not request.user.has_perm('change_resourcebase_metadata', obj_to_check)) and (
                                not is_owner and not settings.ADMIN_MODERATE_UPLOADS):
                        raise Http404
                    else:
                        assign_perm(
                            'view_resourcebase', request.user, obj_to_check)
                        assign_perm(
                            'publish_resourcebase',
                            request.user,
                            obj_to_check)
                        assign_perm(
                            'change_resourcebase_metadata',
                            request.user,
                            obj_to_check)
                        assign_perm(
                            'download_resourcebase',
                            request.user,
                            obj_to_check)

                        if is_owner:
                            assign_perm(
                                'change_resourcebase', request.user, obj_to_check)
                            assign_perm(
                                'delete_resourcebase', request.user, obj_to_check)
                            assign_perm(
                                'change_resourcebase_permissions',
                                request.user,
                                obj_to_check)
                else:
                    if request.user in obj_group_members:
                        if (not request.user.has_perm('publish_resourcebase', obj_to_check)) and (
                            not request.user.has_perm('view_resourcebase', obj_to_check)) and (
                                not request.user.has_perm('change_resourcebase_metadata', obj_to_check)):
                            raise Http404
                    else:
                        raise Http404

    allowed = True
    if permission.split('.')[-1] in ['change_layer_data',
                                     'change_layer_style']:
        if obj.__class__.__name__ == 'Layer':
            obj_to_check = obj
    if permission:
        if permission_required or request.method != 'GET':
            if request.user in obj_group_managers:
                allowed = True
            else:
                allowed = request.user.has_perm(
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
        if isinstance(errors, basestring):
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
            body = "Unexpected exception %s" % exception
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

    if not isinstance(body, basestring):
        body = json.dumps(body, cls=DjangoJSONEncoder)
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
            j['url'] = unicode(j['url']).format(**values)
        except KeyError:
            j['url'] = None
        b.append(j)
    return b


def build_abstract(resourcebase, url=None, includeURL=True):
    if resourcebase.abstract and url and includeURL:
        return u"{abstract} -- [{url}]({url})".format(
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
        return u"- " + u"%0A- ".join(caveats)
    else:
        return u""


def build_social_links(request, resourcebase):
    social_url = u"{protocol}://{host}{path}".format(
        protocol=("https" if request.is_secure() else "http"),
        host=request.get_host(),
        path=request.get_full_path())
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


def fixup_shp_columnnames(inShapefile, charset, tempdir=None):
    """ Try to fix column names and warn the user
    """

    if not tempdir:
        tempdir = tempfile.mkdtemp()
    if is_zipfile(inShapefile):
        inShapefile = unzip_file(inShapefile, '.shp', tempdir=tempdir)

    inDriver = ogr.GetDriverByName('ESRI Shapefile')
    try:
        inDataSource = inDriver.Open(inShapefile, 1)
    except BaseException:
        tb = traceback.format_exc()
        logger.debug(tb)
        inDataSource = None
    if inDataSource is None:
        logger.warning('Could not open %s' % (inShapefile))
        return False, None, None
    else:
        inLayer = inDataSource.GetLayer()

    # TODO we may need to improve this regexp
    # first character must be any letter or "_"
    # following characters can be any letter, number, "#", ":"
    regex = r'^[a-zA-Z,_][a-zA-Z,_,#,:\d]*$'
    a = re.compile(regex)
    regex_first_char = r'[a-zA-Z,_]{1}'
    b = re.compile(regex_first_char)
    inLayerDefn = inLayer.GetLayerDefn()

    list_col_original = []
    list_col = {}

    for i in range(0, inLayerDefn.GetFieldCount()):
        field_name = inLayerDefn.GetFieldDefn(i).GetName()

        if a.match(field_name):
            list_col_original.append(field_name)

    for i in range(0, inLayerDefn.GetFieldCount()):
        charset = charset if charset and 'undefined' not in charset \
            else 'UTF-8'

        field_name = inLayerDefn.GetFieldDefn(i).GetName()
        if not a.match(field_name):
            # once the field_name contains Chinese, to use slugify_zh
            has_ch = False
            for ch in field_name:
                try:
                    if u'\u4e00' <= ch.decode("utf-8", "replace") <= u'\u9fff':
                        has_ch = True
                        break
                except UnicodeDecodeError:
                    has_ch = True
                    break
            if has_ch:
                new_field_name = slugify_zh(field_name, separator='_')
            else:
                new_field_name = slugify(field_name)
            if not b.match(new_field_name):
                new_field_name = '_' + new_field_name
            j = 0
            while new_field_name in list_col_original or new_field_name in list_col.values():
                if j == 0:
                    new_field_name += '_0'
                if new_field_name.endswith('_' + str(j)):
                    j += 1
                    new_field_name = new_field_name[:-2] + '_' + str(j)
            list_col.update({field_name: new_field_name})

    if len(list_col) == 0:
        return True, None, None
    else:
        try:
            for key in list_col.keys():
                qry = u"ALTER TABLE {} RENAME COLUMN \"".format(inLayer.GetName())
                qry = qry + key.decode(charset) + u"\" TO \"{}\"".format(list_col[key])
                inDataSource.ExecuteSQL(qry.encode(charset))
        except UnicodeDecodeError:
            raise GeoNodeException(
                "Could not decode SHAPEFILE attributes by using the specified charset '{}'.".format(charset))
    return True, None, list_col


def id_to_obj(id_):
    if id_ == id_none:
        return None

    for obj in gc.get_objects():
        if id(obj) == id_:
            return obj
            break
    raise Exception("Not found")


def printsignals():
    for signalname in signalnames:
        logger.debug("SIGNALNAME: %s" % signalname)
        signaltype = getattr(models.signals, signalname)
        signals = signaltype.receivers[:]
        for signal in signals:
            logger.debug(signal)


def designals():
    global signals_store

    for signalname in signalnames:
        if signalname in signals_store:
            try:
                signaltype = getattr(models.signals, signalname)
            except BaseException:
                continue
            logger.debug("RETRIEVE: %s: %d" %
                         (signalname, len(signaltype.receivers)))
            signals_store[signalname] = []
            signals = signaltype.receivers[:]
            for signal in signals:
                uid = receiv_call = None
                sender_ista = sender_call = None
                # first tuple element:
                # - case (id(instance), id(method))
                if not isinstance(signal[0], tuple):
                    raise "Malformed signal"

                lookup = signal[0]

                if isinstance(lookup[0], tuple):
                    # receiv_ista = id_to_obj(lookup[0][0])
                    receiv_call = id_to_obj(lookup[0][1])
                else:
                    # - case id(function) or uid
                    try:
                        receiv_call = id_to_obj(lookup[0])
                    except BaseException:
                        uid = lookup[0]

                if isinstance(lookup[1], tuple):
                    sender_call = id_to_obj(lookup[1][0])
                    sender_ista = id_to_obj(lookup[1][1])
                else:
                    sender_ista = id_to_obj(lookup[1])

                # second tuple element
                if (isinstance(signal[1], weakref.ReferenceType)):
                    is_weak = True
                    receiv_call = signal[1]()
                else:
                    is_weak = False
                    receiv_call = signal[1]

                signals_store[signalname].append({
                    'uid': uid, 'is_weak': is_weak,
                    'sender_ista': sender_ista, 'sender_call': sender_call,
                    'receiv_call': receiv_call,
                })

                signaltype.disconnect(
                    receiver=receiv_call,
                    sender=sender_ista,
                    weak=is_weak,
                    dispatch_uid=uid)


def resignals():
    global signals_store

    for signalname in signalnames:
        if signalname in signals_store:
            signals = signals_store[signalname]
            signaltype = getattr(models.signals, signalname)
            for signal in signals:
                signaltype.connect(
                    signal['receiv_call'],
                    sender=signal['sender_ista'],
                    weak=signal['is_weak'],
                    dispatch_uid=signal['uid'])


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
        except BaseException:
            # tb = traceback.format_exc()
            # logger.error(tb)
            pass
    raise ValueError("Invalid datetime input: {}".format(value))


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
    except BaseException:
        pass
    return False


class HttpClient(object):

    def __init__(self):
        self.timeout = 5
        self.retries = 5
        self.pool_maxsize = 10
        self.backoff_factor = 0.3
        self.pool_connections = 10
        self.status_forcelist = (500, 502, 503, 504)
        self.username = 'admin'
        self.password = 'admin'
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            ogc_server_settings = settings.OGC_SERVER['default']
            self.timeout = ogc_server_settings['TIMEOUT'] if 'TIMEOUT' in ogc_server_settings else 5
            self.retries = ogc_server_settings['MAX_RETRIES'] if 'MAX_RETRIES' in ogc_server_settings else 5
            self.backoff_factor = ogc_server_settings['BACKOFF_FACTOR'] if \
            'BACKOFF_FACTOR' in ogc_server_settings else 0.3
            self.pool_maxsize = ogc_server_settings['POOL_MAXSIZE'] if 'POOL_MAXSIZE' in ogc_server_settings else 10
            self.pool_connections = ogc_server_settings['POOL_CONNECTIONS'] if \
            'POOL_CONNECTIONS' in ogc_server_settings else 10
            self.username = ogc_server_settings['USER'] if 'USER' in ogc_server_settings else 'admin'
            self.password = ogc_server_settings['PASSWORD'] if 'PASSWORD' in ogc_server_settings else 'geoserver'

    def request(self, url, method='GET', data=None, headers={}, stream=False, timeout=None, user=None):
        if (user or self.username != 'admin') and \
        check_ogc_backend(geoserver.BACKEND_PACKAGE) and 'Authorization' not in headers:
            if connection.cursor().db.vendor not in ('sqlite', 'sqlite3', 'spatialite'):
                try:
                    if user and isinstance(user, basestring):
                        user = get_user_model().objects.get(username=user)
                    _u = user or get_user_model().objects.get(username=self.username)
                    access_token = get_or_create_token(_u)
                    if access_token and not access_token.is_expired():
                        headers['Authorization'] = 'Bearer %s' % access_token.token
                except BaseException:
                    tb = traceback.format_exc()
                    logger.debug(tb)
                    pass
            elif user == self.username:
                valid_uname_pw = base64.b64encode(
                    b"%s:%s" % (self.username, self.password)).decode("ascii")
                headers['Authorization'] = 'Basic {}'.format(valid_uname_pw)

        response = None
        content = None
        session = requests.Session()
        retry = Retry(
            total=self.retries,
            read=self.retries,
            connect=self.retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=self.status_forcelist,
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry,
            pool_maxsize=self.pool_maxsize,
            pool_connections=self.pool_connections
        )
        session.mount("{scheme}://".format(scheme=urlparse.urlsplit(url).scheme), adapter)
        session.verify = False
        action = getattr(session, method.lower(), None)
        if action:
            response = action(
                url=urllib.unquote(url).decode('utf8'),
                data=data,
                headers=headers,
                timeout=timeout or self.timeout,
                stream=stream)
        else:
            response = session.get(url, headers=headers, timeout=self.timeout)

        try:
            content = response.content if not stream else response.raw
        except BaseException:
            content = None

        return (response, content)

    def get(self, url, data=None, headers={}, stream=False, timeout=None, user=None):
        return self.request(url,
                            method='GET',
                            data=data,
                            headers=headers,
                            timeout=timeout or self.timeout,
                            stream=stream,
                            user=user)

    def post(self, url, data=None, headers={}, stream=False, timeout=None, user=None):
        return self.request(url,
                            method='POST',
                            data=data,
                            headers=headers,
                            timeout=timeout or self.timeout,
                            stream=stream,
                            user=user)


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
                    except BaseException:
                        try:
                            shutil.rmtree(d)
                        except BaseException:
                            pass
                try:
                    shutil.copytree(s, d, symlinks, ignore)
                except BaseException:
                    pass
            else:
                try:
                    shutil.copy2(s, d)
                except BaseException:
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

        for dirname in dirnames:
            path = os.path.join(dirpath, dirname)
            os.chmod(path, permissions)


def slugify_zh(text, separator='_'):
    """
    Make a slug from the given text, which is simplified from slugify.
    It remove the other args and do not convert Chinese into Pinyin
    :param text (str): initial text
    :param separator (str): separator between words
    :return (str):
    """

    QUOTE_PATTERN = re.compile(r'[\']+')
    ALLOWED_CHARS_PATTERN = re.compile(u'[^\u4e00-\u9fa5a-z0-9]+')
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
    from urlparse import urljoin
    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext

    # Prune old links
    if prune:
        logger.info(" -- Resource Links[Prune old links]...")
        _def_link_types = (
            'data', 'image', 'original', 'html', 'OGC:WMS', 'OGC:WFS', 'OGC:WCS')
        Link.objects.filter(resource=instance.resourcebase_ptr, link_type__in=_def_link_types).delete()
        logger.info(" -- Resource Links[Prune old links]...done!")

    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        from geonode.geoserver.ows import wcs_links, wfs_links, wms_links
        from geonode.geoserver.helpers import ogc_server_settings, gs_catalog

        # Compute parameters for the new links
        logger.info(" -- Resource Links[Compute parameters for the new links]...")
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
                    gs_resource = gs_catalog.get_resource(name=instance.name)
                bbox = gs_resource.native_bbox

                dx = float(bbox[1]) - float(bbox[0])
                dy = float(bbox[3]) - float(bbox[2])
                dataAspect = 1 if dy == 0 else dx / dy
                width = int(height * dataAspect)

                srid = bbox[4]
                bbox = ','.join(str(x) for x in [bbox[0], bbox[2], bbox[1], bbox[3]])
            except BaseException as e:
                logger.exception(e)

        # Create Raw Data download link
        if settings.DISPLAY_ORIGINAL_DATASET_LINK:
            logger.info(" -- Resource Links[Create Raw Data download link]...")
            download_url = urljoin(settings.SITEURL,
                                   reverse('download', args=[instance.id]))
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
            logger.info(" -- Resource Links[Create Raw Data download link]...done!")
        else:
            Link.objects.filter(resource=instance.resourcebase_ptr,
                                name='Original Dataset').delete()

        # Set download links for WMS, WCS or WFS and KML
        logger.info(" -- Resource Links[Set download links for WMS, WCS or WFS and KML]...")
        links = wms_links(ogc_server_settings.public_url + 'ows?',
                          instance.alternate.encode('utf-8'),
                          bbox,
                          srid,
                          height,
                          width)

        for ext, name, mime, wms_url in links:
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

        if instance.storeType == "dataStore":
            links = wfs_links(ogc_server_settings.public_url + 'ows?',
                              instance.alternate.encode('utf-8'),
                              bbox=None,  # bbox filter should be set at runtime otherwise conflicting with CQL
                              srid=srid)
            for ext, name, mime, wfs_url in links:
                if mime == 'SHAPE-ZIP':
                    name = 'Zipped Shapefile'
                Link.objects.update_or_create(
                    resource=instance.resourcebase_ptr,
                    url=wfs_url,
                    defaults=dict(
                        extension=ext,
                        name=name,
                        mime=mime,
                        url=wfs_url,
                        link_type='data',
                    )
                )

        elif instance.storeType == 'coverageStore':
            links = wcs_links(ogc_server_settings.public_url + 'wcs?',
                              instance.alternate.encode('utf-8'),
                              bbox,
                              srid)

        for ext, name, mime, wcs_url in links:
            Link.objects.update_or_create(
                resource=instance.resourcebase_ptr,
                url=wcs_url,
                defaults=dict(
                    extension=ext,
                    name=name,
                    mime=mime,
                    link_type='data',
                )
            )

        site_url = settings.SITEURL.rstrip('/') if settings.SITEURL.startswith('http') else settings.SITEURL
        html_link_url = '%s%s' % (
            site_url, instance.get_absolute_url())

        if Link.objects.filter(resource=instance.resourcebase_ptr, url=html_link_url).count() > 1:
            Link.objects.filter(resource=instance.resourcebase_ptr, url=html_link_url).delete()
        Link.objects.get_or_create(
            resource=instance.resourcebase_ptr,
            url=html_link_url,
            defaults=dict(
                extension='html',
                name=instance.alternate,
                mime='text/html',
                link_type='html',
            )
        )
        logger.info(" -- Resource Links[Set download links for WMS, WCS or WFS and KML]...done!")

        # Legend link
        logger.info(" -- Resource Links[Legend link]...")
        try:
            Link.objects.filter(resource=instance.resourcebase_ptr, name='Legend').delete()
        except BaseException:
            pass

        for style in instance.styles.all():
            legend_url = ogc_server_settings.PUBLIC_LOCATION + \
                'ows?service=WMS&request=GetLegendGraphic&format=image/png&WIDTH=20&HEIGHT=20&LAYER=' + \
                instance.alternate + '&STYLE=' + style.name + \
                '&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on'

            if Link.objects.filter(resource=instance.resourcebase_ptr, url=legend_url).count() > 1:
                Link.objects.filter(resource=instance.resourcebase_ptr, url=legend_url).delete()
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
        logger.info(" -- Resource Links[Legend link]...done!")

        # Thumbnail link
        logger.info(" -- Resource Links[Thumbnail link]...")
        from django.contrib.staticfiles.templatetags import staticfiles
        if instance.get_thumbnail_url() == staticfiles.static(settings.MISSING_THUMBNAIL):
            from geonode.geoserver.helpers import create_gs_thumbnail
            create_gs_thumbnail(instance, overwrite=True, check_bbox=True)
        else:
            Link.objects.update_or_create(
                resource=instance.resourcebase_ptr,
                name='Thumbnail',
                url=instance.get_thumbnail_url(),
                defaults=dict(
                    extension='png',
                    mime='image/png',
                    link_type='image',
                )
            )
        logger.info(" -- Resource Links[Thumbnail link]...done!")

        logger.info(" -- Resource Links[OWS Links]...")
        # ogc_wms_path = '%s/ows' % instance.workspace
        ogc_wms_path = 'ows'
        ogc_wms_url = urljoin(ogc_server_settings.public_url, ogc_wms_path)
        ogc_wms_name = 'OGC WMS: %s Service' % instance.workspace
        if Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wms_name, url=ogc_wms_url).count() > 1:
            Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wms_name, url=ogc_wms_url).delete()
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
            ogc_wfs_name = 'OGC WFS: %s Service' % instance.workspace
            if Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wfs_name, url=ogc_wfs_url).count() > 1:
                Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wfs_name, url=ogc_wfs_url).delete()
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
            ogc_wcs_name = 'OGC WCS: %s Service' % instance.workspace
            if Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wcs_name, url=ogc_wcs_url).count() > 1:
                Link.objects.filter(resource=instance.resourcebase_ptr, name=ogc_wcs_name, url=ogc_wcs_url).delete()
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
        logger.info(" -- Resource Links[OWS Links]...done!")
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
        logger.debug('zip_download_url: %s' % zip_download_url)
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
        ogc_wms_name = 'OGC WMS: %s Service' % instance.workspace
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
        logger.debug('qgs_download_url: %s' % ogc_qgs_url)
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
            ogc_wfs_name = 'OGC WFS: %s Service' % instance.workspace
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
        logger.debug('qlr_download_url: %s' % ogc_qlr_url)
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

        logger.debug('Creating the QGIS Project : %s' % response.url)
        if response.content != 'OK':
            logger.debug('Result : %s' % response.content)

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
            logger.debug('geotif_url: %s' % geotiff_url)

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
