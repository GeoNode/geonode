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

import itertools
import os
import gc
import re
import json
import time
import base64
import select
import shutil
import string
import typing
import logging
import tarfile
import datetime
import requests
import tempfile
import traceback
import subprocess

from lxml import etree
from osgeo import ogr
from PIL import Image
from urllib3 import Retry
from io import BytesIO, StringIO
from decimal import Decimal
from threading import local
from slugify import slugify
from contextlib import closing
from requests.exceptions import RetryError
from collections import namedtuple, defaultdict
from rest_framework.exceptions import APIException
from math import atan, exp, log, pi, sin, tan, floor
from zipfile import ZipFile, is_zipfile, ZIP_DEFLATED
from geonode.upload.api.exceptions import GeneralUploadException

from django.conf import settings
from django.db.models import signals
from django.utils.http import is_safe_url
from django.apps import apps as django_apps
from django.middleware.csrf import get_token
from django.http import HttpResponse
from django.forms.models import model_to_dict
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ImproperlyConfigured
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models, connection, transaction
from django.utils.translation import ugettext_lazy as _

from geonode import geoserver, GeoNodeException  # noqa
from geonode.compat import ensure_string
from geonode.layers.enumerations import GXP_PTYPES
from geonode.storage.manager import storage_manager
from geonode.services.serviceprocessors import get_available_service_types
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
    parse_qsl,
    ParseResult,
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

FORWARDED_HEADERS = [
    'content-type',
    'content-disposition'
]

# explicitly disable resolving XML entities in order to prevent malicious attacks
XML_PARSER: typing.Final = etree.XMLParser(resolve_entities=False)

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


class ServerDoesNotExist(Exception):
    pass


class OGC_Server(object):  # LGTM: @property will not work in old-style classes

    """
    OGC Server object.
    """

    def __init__(self, ogc_server, alias):
        self.alias = alias
        self.server = ogc_server

    def __getattr__(self, item):
        return self.server.get(item)

    @property
    def credentials(self):
        """
        Returns a tuple of the server's credentials.
        """
        creds = namedtuple('OGC_SERVER_CREDENTIALS', ['username', 'password'])
        return creds(username=self.USER, password=self.PASSWORD)

    @property
    def datastore_db(self):
        """
        Returns the server's datastore dict or None.
        """
        if self.DATASTORE and settings.DATABASES.get(self.DATASTORE, None):
            datastore_dict = settings.DATABASES.get(self.DATASTORE, dict())
            return datastore_dict
        else:
            return dict()

    @property
    def ows(self):
        """
        The Open Web Service url for the server.
        """
        location = self.PUBLIC_LOCATION if self.PUBLIC_LOCATION else self.LOCATION
        return self.OWS_LOCATION if self.OWS_LOCATION else urljoin(location, 'ows')

    @property
    def rest(self):
        """
        The REST endpoint for the server.
        """
        return urljoin(self.LOCATION, 'rest') if not self.REST_LOCATION else self.REST_LOCATION

    @property
    def public_url(self):
        """
        The global public endpoint for the server.
        """
        return self.LOCATION if not self.PUBLIC_LOCATION else self.PUBLIC_LOCATION

    @property
    def internal_ows(self):
        """
        The Open Web Service url for the server used by GeoNode internally.
        """
        location = self.LOCATION
        return urljoin(location, 'ows')

    @property
    def hostname(self):
        return urlsplit(self.LOCATION).hostname

    @property
    def netloc(self):
        return urlsplit(self.LOCATION).netloc

    def __str__(self):
        return str(self.alias)


class OGC_Servers_Handler:

    """
    OGC Server Settings Convenience dict.
    """

    def __init__(self, ogc_server_dict):
        self.servers = ogc_server_dict
        # FIXME(Ariel): Are there better ways to do this without involving
        # local?
        self._servers = local()

    def ensure_valid_configuration(self, alias):
        """
        Ensures the settings are valid.
        """
        try:
            server = self.servers[alias]
        except KeyError:
            raise ServerDoesNotExist(f"The server {alias} doesn't exist")

        if 'PRINTNG_ENABLED' in server:
            raise ImproperlyConfigured("The PRINTNG_ENABLED setting has been removed, use 'PRINT_NG_ENABLED' instead.")

    def ensure_defaults(self, alias):
        """
        Puts the defaults into the settings dictionary for a given connection where no settings is provided.
        """
        try:
            server = self.servers[alias]
        except KeyError:
            raise ServerDoesNotExist(f"The server {alias} doesn't exist")

        server.setdefault('BACKEND', 'geonode.geoserver')
        server.setdefault('LOCATION', 'http://localhost:8080/geoserver/')
        server.setdefault('USER', 'admin')
        server.setdefault('PASSWORD', 'geoserver')
        server.setdefault('DATASTORE', '')

        for option in ['MAPFISH_PRINT_ENABLED', 'PRINT_NG_ENABLED', 'GEONODE_SECURITY_ENABLED',
                       'GEOFENCE_SECURITY_ENABLED', 'BACKEND_WRITE_ENABLED']:
            server.setdefault(option, True)

        for option in ['WMST_ENABLED', 'WPS_ENABLED']:
            server.setdefault(option, False)

    def __getitem__(self, alias):
        if hasattr(self._servers, alias):
            return getattr(self._servers, alias)

        self.ensure_defaults(alias)
        self.ensure_valid_configuration(alias)
        server = self.servers[alias]
        server = OGC_Server(alias=alias, ogc_server=server)
        setattr(self._servers, alias, server)
        return server

    def __setitem__(self, key, value):
        setattr(self._servers, key, value)

    def __iter__(self):
        return iter(self.servers)

    def all(self):
        return [self[alias] for alias in self]


def mkdtemp(dir=settings.MEDIA_ROOT):
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)
    tempdir = None
    while not tempdir:
        try:
            tempdir = tempfile.mkdtemp(dir=dir)
            if os.path.exists(tempdir) and os.path.isdir(tempdir):
                if os.listdir(tempdir):
                    raise Exception("Directory is not empty")
            else:
                raise Exception("Directory does not exist or is not accessible")
        except Exception as e:
            logger.exception(e)
            tempdir = None
    return tempdir


def unzip_file(upload_file, extension='.shp', tempdir=None):
    """
    Unzips a zipfile into a temporary directory and returns the full path of the .shp file inside (if any)
    """
    absolute_base_file = None
    if tempdir is None:
        tempdir = mkdtemp()

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
        tempdir = mkdtemp()

    the_tar = tarfile.open(upload_file)
    the_tar.extractall(tempdir)
    for item in the_tar.getnames():
        if item.endswith(extension):
            absolute_base_file = os.path.join(tempdir, item)

    return absolute_base_file


def get_dataset_name(dataset):
    """Get the workspace where the input layer belongs"""
    _name = dataset.name
    if _name and ':' in _name:
        _name = _name.split(':')[1]
    try:
        if not _name and dataset.alternate:
            if ':' in dataset.alternate:
                _name = dataset.alternate.split(':')[1]
            else:
                _name = dataset.alternate
    except Exception:
        pass
    return _name


def get_dataset_workspace(dataset):
    """Get the workspace where the input layer belongs"""
    alternate = None
    workspace = None
    try:
        alternate = dataset.alternate
    except Exception:
        alternate = dataset.name
    try:
        workspace = dataset.workspace
    except Exception:
        workspace = None
    if not workspace and alternate and ':' in alternate:
        workspace = alternate.split(":")[1]
    if not workspace:
        default_workspace = getattr(settings, "DEFAULT_WORKSPACE", "geonode")
        try:
            from geonode.services.enumerations import CASCADED
            if dataset.remote_service.method == CASCADED:
                workspace = getattr(
                    settings, "CASCADE_WORKSPACE", default_workspace)
            else:
                raise RuntimeError("Dataset is not cascaded")
        except Exception:  # layer does not have a service
            workspace = default_workspace
    return workspace


def get_headers(request, url, raw_url, allowed_hosts=[]):
    cookies = None
    csrftoken = None
    headers = {}

    for _header_key, _header_value in dict(request.headers.copy()).items():
        if _header_key.lower() in FORWARDED_HEADERS:
            headers[_header_key] = _header_value
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
        cook = f"csrftoken={csrftoken}"
        cookies = cook if not cookies else (f"{cookies}; {cook}")

    if cookies and request and hasattr(request, 'session'):
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
    headers.update(
        {
            "Pragma": pragma,
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
        wkt = 'POLYGON(({:f} {:f},{:f} {:f},{:f} {:f},{:f} {:f},{:f} {:f}))'.format(
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
        return tuple(
            [float(projected_bbox[0]), float(projected_bbox[1]), float(projected_bbox[2]), float(projected_bbox[3])]) + \
            (f"EPSG:{target_srid}",)

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

    from guardian.shortcuts import get_groups_with_perms
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

    allowed = True
    if permission.split('.')[-1] in ['change_dataset_data',
                                     'change_dataset_style']:
        if obj.__class__.__name__ == 'Dataset':
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
        if isinstance(exception, APIException):
            raise exception
        if body is None:
            body = f"Unexpected exception {exception}"
        else:
            body = body % exception
        body = {
            'success': False,
            'errors': [body]
        }
        raise GeneralUploadException(detail=body)
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
        return f"{resourcebase.abstract} -- [{url}]({url})"
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
    netschema = ("https" if request.is_secure() else "http")
    host = request.get_host()
    path = request.get_full_path()
    social_url = f"{netschema}://{host}{path}"
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
        tempdir = mkdtemp()

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
            tb = traceback.format_exc()
            logger.debug(tb)
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


class HttpClient:

    def __init__(self):
        self.timeout = 5
        self.retries = 1
        self.pool_maxsize = 10
        self.backoff_factor = 0.3
        self.pool_connections = 10
        self.status_forcelist = (500, 502, 503, 504)
        self.username = 'admin'
        self.password = 'admin'
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            ogc_server_settings = settings.OGC_SERVER['default']
            self.timeout = ogc_server_settings.get('TIMEOUT', 5)
            self.retries = ogc_server_settings.get('MAX_RETRIES', 1)
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

        headers['User-Agent'] = 'GeoNode'
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
        scheme = urlsplit(url).scheme
        session.mount(f"{scheme}://", adapter)
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
            except (requests.exceptions.RequestException, ValueError, RetryError) as e:
                msg = f"Request exception [{e}] - TOUT [{_req_tout}] to URL: {url} - headers: {headers}"
                logger.exception(Exception(msg))
                response = None
                content = str(e)
        else:
            response = session.get(url, headers=headers, timeout=self.timeout)
        if response:
            try:
                content = ensure_string(response.content) if not stream else response.raw
            except Exception as e:
                content = str(e)

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
                if os.path.exists(d):
                    try:
                        os.remove(d)
                    except Exception:
                        shutil.rmtree(d, ignore_errors=True)
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
        os.makedirs(target_folder, exist_ok=True)

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


def get_legend_url(
        instance, style_name, /,
        service_url=None,
        dataset_name=None,
        version='1.3.0',
        sld_version='1.1.0',
        width=20,
        height=20,
        params=None):
    from geonode.geoserver.helpers import ogc_server_settings

    _service_url = service_url or f"{ogc_server_settings.PUBLIC_LOCATION}ows"
    _dataset_name = dataset_name or instance.alternate
    _params = f"&{params}" if params else ""
    return (f"{_service_url}?"
            f"service=WMS&request=GetLegendGraphic&format=image/png&WIDTH={width}&HEIGHT={height}&"
            f"LAYER={_dataset_name}&STYLE={style_name}&version={version}&"
            f"sld_version={sld_version}&legend_options=fontAntiAliasing:true;fontSize:12;forceLabels:on{_params}")


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

        # Parse Dataset BBOX and SRID
        bbox = None
        srid = instance.srid if instance.srid else getattr(settings, 'DEFAULT_MAP_CRS', 'EPSG:4326')
        if not prune and instance.srid and instance.bbox_polygon:
            bbox = instance.bbox_string
        else:
            try:
                gs_resource = gs_catalog.get_resource(
                    name=instance.name,
                    store=instance.store,
                    workspace=instance.workspace)
                if not gs_resource:
                    gs_resource = gs_catalog.get_resource(
                        name=instance.name,
                        workspace=instance.workspace)
                if not gs_resource:
                    gs_resource = gs_catalog.get_resource(name=instance.name)

                if gs_resource:
                    srid = gs_resource.projection
                    bbox = gs_resource.native_bbox
                    ll_bbox = gs_resource.latlon_bbox
                    try:
                        instance.set_bbox_polygon([bbox[0], bbox[2], bbox[1], bbox[3]], srid)
                    except GeoNodeException as e:
                        if not ll_bbox:
                            raise
                        else:
                            logger.exception(e)
                            instance.srid = 'EPSG:4326'
                    instance.set_ll_bbox_polygon([ll_bbox[0], ll_bbox[2], ll_bbox[1], ll_bbox[3]])
                    if instance.srid:
                        instance.srid_url = f"http://www.spatialreference.org/ref/{instance.srid.replace(':', '/').lower()}/"
                    elif instance.bbox_polygon is not None:
                        # Guessing 'EPSG:4326' by default
                        instance.srid = 'EPSG:4326'
                    else:
                        raise GeoNodeException(_("Invalid Projection. Dataset is missing CRS!"))
                    dx = float(bbox[1]) - float(bbox[0])
                    dy = float(bbox[3]) - float(bbox[2])
                    dataAspect = 1 if dy == 0 else dx / dy
                    width = int(height * dataAspect)
                    # Rewriting BBOX as a plain string
                    bbox = ','.join(str(x) for x in [bbox[0], bbox[2], bbox[1], bbox[3]])
                else:
                    bbox = instance.bbox_string
            except Exception as e:
                logger.exception(e)
                bbox = instance.bbox_string

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
        instance_ows_url = f"{instance.ows_url}?" if instance.ows_url else f"{ogc_server_settings.public_url}ows?"
        links = wms_links(instance_ows_url,
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

        if instance.subtype == "vector":
            links = wfs_links(instance_ows_url,
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

        elif instance.subtype == 'raster':
            """
            Going to create the WCS GetCoverage Default download links.
            By providing 'None' bbox and srid, we are going to ask to the WCS to
            skip subsetting, i.e. output the whole coverage in the netive SRS.

            Notice that the "wcs_links" method also generates 1 default "outputFormat":
             - "geotiff"; GeoTIFF which will be compressed and tiled by passing to the WCS the default query params compression='DEFLATE' and tile_size=512
            """
            links = wcs_links(instance_ows_url,
                              instance.alternate)
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
                name=instance.alternate or instance.name,
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
            if instance.subtype not in ['tileStore', 'remote']:
                for style in set(list(instance.styles.all()) + [instance.default_style, ]):
                    if style:
                        style_name = os.path.basename(
                            urlparse(style.sld_url).path).split('.')[0]
                        legend_url = get_legend_url(instance, style_name)
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
            else:
                from geonode.services.serviceprocessors import get_service_handler
                handler = get_service_handler(
                    instance.remote_service.service_url, service_type=instance.remote_service.type)
                if handler and hasattr(handler, '_create_dataset_legend_link'):
                    handler._create_dataset_legend_link(instance)

            logger.debug(" -- Resource Links[Legend link]...done!")
        except Exception as e:
            logger.debug(f" -- Resource Links[Legend link]...error: {e}")

        # Thumbnail link
        if instance.get_thumbnail_url():
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
        try:
            if not hasattr(instance.get_real_instance(), 'ptype') or instance.get_real_instance().ptype == GXP_PTYPES["WMS"]:
                ogc_wms_url = instance.ows_url or urljoin(ogc_server_settings.public_url, 'ows')
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

                if instance.subtype == "vector":
                    ogc_wfs_url = instance.ows_url or urljoin(ogc_server_settings.public_url, 'ows')
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

                if instance.subtype == "raster":
                    ogc_wcs_url = instance.ows_url or urljoin(ogc_server_settings.public_url, 'ows')
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

            elif hasattr(instance.get_real_instance(), 'ptype') and instance.get_real_instance().ptype:
                ptype_link = dict((v, k) for k, v in GXP_PTYPES.items()).get(instance.get_real_instance().ptype)
                ptype_link_name = get_available_service_types().get(ptype_link)
                ptype_link_url = instance.ows_url
                if Link.objects.filter(resource=instance.resourcebase_ptr, name=ptype_link_name, url=ptype_link_url).count() < 2:
                    Link.objects.get_or_create(
                        resource=instance.resourcebase_ptr,
                        url=ptype_link_url,
                        name=ptype_link_name,
                        defaults=dict(
                            extension='html',
                            url=ptype_link_url,
                            mime='text/html',
                            link_type='image',
                        )
                    )
            logger.debug(" -- Resource Links[OWS Links]...done!")
        except Exception as e:
            logger.error(" -- Resource Links[OWS Links]...error!")
            logger.exception(e)


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
    'default_style': 'datasets.Style',
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
        if storage_manager.exists(_thumb_path):
            return storage_manager.open(_thumb_path)
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
        logger.debug(e)
        return False


def find_by_attr(lst, val, attr="id"):
    """ Returns an object if the id matches in any list of objects """
    for item in lst:
        if attr in item and item[attr] == val:
            return item

    return None


def build_absolute_uri(url):
    if url and 'http' not in url:
        url = urljoin(settings.SITEURL, url)
    return url


def get_xpath_value(
        element: etree.Element,
        xpath_expression: str,
        nsmap: typing.Optional[dict] = None
) -> typing.Optional[str]:
    if not nsmap:
        nsmap = element.nsmap
    values = element.xpath(f"{xpath_expression}//text()", namespaces=nsmap)
    return "".join(values).strip() or None


def get_geonode_app_types():
    from geonode.geoapps.models import GeoApp
    return list(set(GeoApp.objects.values_list('resource_type', flat=True)))


def get_supported_datasets_file_types():
    from django.conf import settings as gn_settings
    '''
    Return a list of all supported file type in geonode
    If one of the type provided in the custom type exists in the default
    is going to override it
    '''
    default_types = settings.SUPPORTED_DATASET_FILE_TYPES
    types_module = (
        gn_settings.ADDITIONAL_DATASET_FILE_TYPES
        if hasattr(gn_settings, "ADDITIONAL_DATASET_FILE_TYPES")
        else []
    )
    supported_types = default_types.copy()
    default_types_id = [t.get('id') for t in default_types]
    for _type in types_module:
        if _type.get("id") in default_types_id:
            supported_types[default_types_id.index(_type.get("id"))] = _type
        else:
            supported_types.extend([_type])
    return supported_types


def get_allowed_extensions():
    return list(itertools.chain.from_iterable([_type['ext'] for _type in get_supported_datasets_file_types()]))
