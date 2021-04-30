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
import logging
import math
import os
import re
import shutil
import json
from urllib.parse import unquote, urljoin

import requests
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from defusedxml import lxml as dlxml
from requests import Request

from geonode.compat import ensure_string
from geonode import qgis_server, geoserver
from geonode.utils import check_ogc_backend
from geonode.geoserver.helpers import OGC_Servers_Handler
from geonode.layers.models import Layer
from geonode.qgis_server.gis_tools import num2deg
from geonode.qgis_server.models import (
    QGISServerLayer,
    QGISServerMap,
    QGISServerStyle)

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    # FIXME: The post service providing the map_status object
    # should be moved to geonode.geoserver.
    from geonode.geoserver.helpers import ogc_server_settings
elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']

logger = logging.getLogger("geonode.qgis_server.helpers")


def validate_django_settings():
    """Check that settings file configured correctly for qgis_server backend.
    """
    # geonode.qgis_server must exists in INSTALLED_APPS and not geoserver
    if 'geonode.qgis_server' not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured(
            'geonode.qgis_server module not included in INSTALLED_APPS.')
    if ogc_server_settings.BACKEND == 'geonode.geoserver':
        raise ImproperlyConfigured(
            'You want to use QGIS Server backend, but geonode.geoserver module'
            ' is set as default BACKEND.')

    # LOCAL_GEOSERVER settings should not exists
    if hasattr(settings, 'LOCAL_GEOSERVER'):
        raise ImproperlyConfigured(
            "This setting will not be used when using QGIS Server backend.")

    # Should not include geoserver context_processor
    geoserver_context_processor = \
        'geonode.geoserver.context_processors.geoserver_urls'

    context_processors = settings.TEMPLATES[
        0]['OPTIONS']['context_processors']

    # Should include qgis_server context_processor
    qgis_server_context_processor = \
        'geonode.qgis_server.context_processors.qgis_server_urls'

    if geoserver_context_processor in context_processors:
        raise ImproperlyConfigured(
            'Geoserver context_processors should be excluded.')

    if qgis_server_context_processor not in context_processors:
        raise ImproperlyConfigured(
            'QGIS Server context_processors should be included.')

    if not hasattr(settings, 'QGIS_SERVER_URL'):
        raise ImproperlyConfigured(
            'QGIS_SERVER_URL setting should be configured.')

    if not hasattr(settings, 'QGIS_SERVER_CONFIG'):
        raise ImproperlyConfigured(
            'QGIS_SERVER_CONFIG setting should be configured.')

    if not settings.GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY == 'leaflet':
        raise ImproperlyConfigured(
            'QGIS Server at the moment only works with '
            'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY = leaflet.')

    # Check OGC Server settings
    default_ogc_backend = settings.OGC_SERVER['default']

    if not default_ogc_backend['BACKEND'] == qgis_server.BACKEND_PACKAGE:
        raise ImproperlyConfigured(
            f"OGC_SERVER['default']['BACKEND'] should be set to {qgis_server.BACKEND_PACKAGE}.")

    return True


def transform_layer_bbox(layer, target_crs):
    """Transform layer bbox to a different CRS.

    :param layer: Layer to take the bounding box from
    :type layer: Layer

    :param target_crs: Integer of EPSG crs ID
    :type target_crs: int

    :return: list converted BBox in target CRS, in the format:
        [xmin,ymin,xmax,ymax]
    :rtype: list(int)
    """
    srid, wkt = layer.geographic_bounding_box.split(';')
    srid = re.findall(r'\d+', srid)
    geom = GEOSGeometry(wkt, srid=int(srid[0]))
    geom.transform(target_crs)
    return list(geom.extent)


def qgis_server_endpoint(internal=True):
    """Return QGIS Server endpoint.

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: Base url endpoint
    :rtype: str
    """
    if internal:
        try:
            return settings.QGIS_SERVER_CONFIG['qgis_server_url']
        except AttributeError:
            logging.error(
                'QGIS_SERVER_CONFIG option is missing "qgis_server_url" key')
            raise
    else:
        # The generated URL is not a direct URL to QGIS Server,
        # but it was a proxy from django instead.
        endpoint_url = reverse('qgis_server:request')

        if hasattr(settings, 'TESTING') and settings.TESTING:
            site_url = 'http://localhost:8000'
        else:
            site_url = settings.SITEURL
        qgis_server_url = urljoin(site_url, endpoint_url)
        return qgis_server_url


def tile_url_format(layer_name, style=None):
    """Construct proxied QGIS Server URL format for tiles.

    This url is not an actual request, but rather a format url
    that can be used by TMS service to generate tile request according
    to this layer.

    :param layer_name: The layer name from the QGIS backend
    :type layer_name: basestring

    :return: Tile url
    :rtype: basestring
    """
    url_kwargs = {
        'layername': layer_name
    }
    if style:
        url_kwargs['style'] = style
    url = reverse(
        'qgis_server:tile',
        kwargs=url_kwargs)
    # unquote url
    # so that {z}/{x}/{y} is not quoted
    url = unquote(url)
    url = urljoin(settings.SITEURL, url)
    return url


def tile_url(layer, z, x, y, style=None, internal=True):
    """Construct actual tile request to QGIS Server.

    Different than tile_url_format, this method will return url for requesting
    a tile, with all parameters filled out.

    :param layer: Layer to use
    :type layer: Layer

    :param z: TMS coordinate, zoom parameter
    :type z: int, str

    :param x: TMS coordinate, longitude parameter
    :type x: int, str

    :param y: TMS coordinate, latitude parameter
    :type y: int, str

    :param style: Layer style to choose
    :type style: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: Tile url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {layer.name}'
        logger.debug(msg)
        raise

    x = int(x)
    y = int(y)
    z = int(z)

    # Call the WMS
    top, left = num2deg(x, y, z)
    bottom, right = num2deg(x + 1, y + 1, z)

    transform = CoordTransform(SpatialReference(4326), SpatialReference(3857))
    top_left_corner = Point(left, top, srid=4326)
    bottom_right_corner = Point(right, bottom, srid=4326)
    top_left_corner.transform(transform)
    bottom_right_corner.transform(transform)

    bottom = bottom_right_corner.y
    right = bottom_right_corner.x
    top = top_left_corner.y
    left = top_left_corner.x

    bbox = ','.join([str(val) for val in [left, bottom, right, top]])

    if not style:
        style = 'default'

    if style not in [s.name for s in qgis_layer.styles.all()]:
        if qgis_layer.default_style:
            style = qgis_layer.default_style.name

    query_string = {
        'SERVICE': 'WMS',
        'VERSION': '1.1.1',
        'REQUEST': 'GetMap',
        'BBOX': bbox,
        'CRS': 'EPSG:3857',
        'WIDTH': '256',
        'HEIGHT': '256',
        'MAP': qgis_layer.qgis_project_path,
        'LAYERS': layer.name,
        'STYLE': style,
        'FORMAT': 'image/png',
        'TRANSPARENT': 'true',
        'DPI': '96',
        'MAP_RESOLUTION': '96',
        'FORMAT_OPTIONS': 'dpi:96'
    }
    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url

    return url


def map_thumbnail_url(instance, bbox=None, internal=True):
    """Construct QGIS Server Url to fetch remote map thumbnail.

    :param instance: Map object
    :type instance: geonode.maps.models.Map

    :param bbox: Bounding box of thumbnail in 4 tuple format
        [xmin,ymin,xmax,ymax]
    :type bbox: list(float)

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: thumbnail url
    :rtype: str
    """
    try:
        qgis_map = QGISServerMap.objects.get(map=instance)
    except QGISServerMap.DoesNotExist:
        msg = f'No QGIS Server Map for existing map {instance.title}'
        logger.debug(msg)
        raise

    qgis_project = qgis_map.qgis_project_path
    if not os.path.exists(qgis_project):
        msg = f'Map project not found for {qgis_project}'
        logger.debug(msg)
        raise ValueError(msg)

    if not bbox:
        # We get the extent of these layers.
        # Reproject, in case of different CRS
        bbox = transform_layer_bbox(instance, 4326)
    return thumbnail_url(
        bbox, qgis_map.qgis_map_name, qgis_project, internal=internal)


def layer_thumbnail_url(instance, style=None, bbox=None, internal=True):
    """Construct QGIS Server Url to fetch remote layer thumbnail.

    :param instance: Layer object
    :type instance: geonode.layers.models.Layer

    :param style: Layer style to choose
    :type style: str

    :param bbox: Bounding box of thumbnail in 4 tuple format
        [xmin,ymin,xmax,ymax]
    :type bbox: list(float)

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: Thumbnail URL.
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=instance)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {instance.name}'
        logger.debug(msg)
        raise

    qgis_project = qgis_layer.qgis_project_path
    layers = instance.name

    if not style:
        style = 'default'

    if style not in [s.name for s in qgis_layer.styles.all()]:
        if qgis_layer.default_style:
            style = qgis_layer.default_style.name

    if not bbox:
        # We get the extent of the layer.
        # Reproject, in case of different CRS
        bbox = transform_layer_bbox(instance, 4326)

    return thumbnail_url(bbox, layers, qgis_project, style=style, internal=internal)


def thumbnail_url(bbox, layers, qgis_project, style=None, internal=True):
    """Internal function to generate the URL for the thumbnail.

    :param bbox: The bounding box to use in the format [left,bottom,right,top].
    :type bbox: list

    :param layers: Name of the layer to use.
    :type layers: basestring

    :param qgis_project: The path to the QGIS project.
    :type qgis_project: basestring

    :param style: Layer style to choose
    :type style: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: The WMS URL to fetch the thumbnail.
    :rtype: basestring
    """

    x_min, y_min, x_max, y_max = bbox
    # We calculate the margins according to 10 percent.
    percent = 10
    delta_x = (x_max - x_min) / 100 * percent
    delta_x = math.fabs(delta_x)
    delta_y = (y_max - y_min) / 100 * percent
    delta_y = math.fabs(delta_y)
    # We apply the margins to the extent.
    margin = [
        y_min - delta_y,
        x_min - delta_x,
        y_max + delta_y,
        x_max + delta_x
    ]
    # Call the WMS.
    bbox = ','.join([str(val) for val in margin])
    query_string = {
        'SERVICE': 'WMS',
        'VERSION': '1.1.1',
        'REQUEST': 'GetMap',
        'BBOX': bbox,
        'SRS': 'EPSG:4326',
        'WIDTH': '250',
        'HEIGHT': '250',
        'MAP': qgis_project,
        'LAYERS': layers,
        'STYLE': style,
        'FORMAT': 'image/png',
        'TRANSPARENT': 'true',
        'DPI': '96',
        'MAP_RESOLUTION': '96',
        'FORMAT_OPTIONS': 'dpi:96'
    }
    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def legend_url(layer, layertitle=False, style=None, internal=True):
    """Construct QGIS Server url to fetch legend.

    :param layer: Layer to use
    :type layer: Layer

    :param layertitle: Layer title flag. Set to True to include layer title
    :type layertitle: bool

    :param style: Layer style to choose
    :type style: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {layer.name}'
        logger.debug(msg)
        raise

    qgis_project_path = qgis_layer.qgis_project_path

    if not style:
        style = 'default'

    if style not in [s.name for s in qgis_layer.styles.all()]:
        if qgis_layer.default_style:
            style = qgis_layer.default_style.name

    query_string = {
        'MAP': qgis_project_path,
        'SERVICE': 'WMS',
        'VERSION': '1.1.1',
        'REQUEST': 'GetLegendGraphic',
        'LAYER': layer.name,
        'LAYERTITLE': str(layertitle).lower(),
        'FORMAT': 'image/png',
        'STYLE': style,
        'TILED': 'true',
        'TRANSPARENT': 'true',
        'LEGEND_OPTIONS': (
            'fontAntiAliasing:true;fontSize:11;fontName:Arial')
    }
    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def qgs_url(layer, style=None, internal=True):
    """Construct QGIS Server url to fetch QGS.

    :param layer: Layer to use
    :type layer: Layer

    :param style: Layer style to choose
    :type style: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url for QGS
    :rtype: str
    """
    qgis_server_url = qgis_server_endpoint(internal)

    url = requests.compat.urljoin(
        settings.SITEURL,
        reverse('qgis_server:layer-request',
                kwargs={'layername': layer.name}))

    # for now, style always set to ''
    if not style:
        style = ''
    else:
        style = 'default'

    layers = [{
        'type': 'raster',
        'display': layer.name,
        'driver': 'wms',
        'crs': 'EPSG:4326',
        'format': 'image/png',
        'styles': style,
        'layers': layer.name,
        'url': url
    }]

    json_layers = json.dumps(layers)

    url_server = f"{qgis_server_url}?SERVICE=PROJECTDEFINITIONS&LAYERS={json_layers}"

    return url_server


def qlr_url(layer, style=None, internal=True):
    """Construct QGIS Server url to fetch QLR.

    :param layer: Layer to use
    :type layer: Layer

    :param style: Layer style to choose
    :type style: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url for QLR
    :rtype: str
    """
    qgis_server_url = qgis_server_endpoint(internal)
    url = requests.compat.urljoin(
        settings.SITEURL,
        reverse('qgis_server:layer-request',
                kwargs={'layername': layer.name}))

    # for now, style always set to ''
    if not style:
        style = ''
    else:
        style = 'default'

    layers = [{
        'type': 'raster',
        'display': layer.name,
        'driver': 'wms',
        'crs': 'EPSG:4326',
        'format': 'image/png',
        'styles': style,
        'layers': layer.name,
        'url': url
    }]
    json_layers = json.dumps(layers)

    url_server = f"{qgis_server_url}?SERVICE=LAYERDEFINITIONS&LAYERS={json_layers}"

    return url_server


def wms_get_capabilities_url(layer=None, internal=True):
    """Construct WMS GetCapabilities request.

    :param layer: Layer to inspect
    :type layer: Layer

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {layer.name}'
        logger.debug(msg)
        raise

    qgis_project_path = qgis_layer.qgis_project_path

    query_string = {
        'MAP': qgis_project_path,
        'SERVICE': 'WMS',
        'VERSION': '1.1.1',
        'REQUEST': 'GetCapabilities',
        'LAYER': layer.name
    }

    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def style_get_url(layer, style_name, internal=True):
    """Get QGIS Server style as xml.

    :param layer: Layer to inspect
    :type layer: Layer

    :param style_name: Style name as given by QGIS Server
    :type style_name: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {layer.name}'
        logger.debug(msg)
        raise

    qgis_project_path = qgis_layer.qgis_project_path

    query_string = {
        'PROJECT': qgis_project_path,
        'SERVICE': 'STYLEMANAGER',
        'REQUEST': 'GetStyle',
        'LAYER': layer.name,
        'NAME': style_name
    }

    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def style_add_url(layer, style_name, internal=True):
    """Add QGIS Server style to QGIS Project.

    This style file is stored on qml LayerFile in upload_session.
    After the file is uploaded, it has to be deleted.

    :param layer: Layer to inspect
    :type layer: Layer

    :param style_name: Style name as given by QGIS Server
    :type style_name: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {layer.name}'
        logger.debug(msg)
        raise

    qgis_project_path = qgis_layer.qgis_project_path

    # QML File is taken from uploaded file
    query_string = {
        'SERVICE': 'STYLEMANAGER',
        'PROJECT': qgis_project_path,
        'REQUEST': 'AddStyle',
        'LAYER': layer.name,
        'NAME': style_name,
        'QML': qgis_layer.qml_path,
        'REMOVEQML': 'TRUE'
    }

    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def style_remove_url(layer, style_name, internal=True):
    """Remove QGIS Server style from QGIS Project.

    :param layer: Layer to inspect
    :type layer: Layer

    :param style_name: Style name as given by QGIS Server
    :type style_name: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {layer.name}'
        logger.debug(msg)
        raise

    qgis_project_path = qgis_layer.qgis_project_path

    query_string = {
        'SERVICE': 'STYLEMANAGER',
        'PROJECT': qgis_project_path,
        'REQUEST': 'RemoveStyle',
        'LAYER': layer.name,
        'NAME': style_name
    }

    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def style_set_default_url(layer, style_name, internal=True):
    """Remove QGIS Server style from QGIS Project.

    :param layer: Layer to inspect
    :type layer: Layer

    :param style_name: Style name as given by QGIS Server
    :type style_name: str

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = f'No QGIS Server Layer for existing layer {layer.name}'
        logger.debug(msg)
        raise

    qgis_project_path = qgis_layer.qgis_project_path

    query_string = {
        'SERVICE': 'STYLEMANAGER',
        'PROJECT': qgis_project_path,
        'REQUEST': 'SetDefaultStyle',
        'LAYER': layer.name,
        'NAME': style_name
    }

    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def style_list(layer, internal=True, generating_qgis_capabilities=False):
    """Query list of styles from QGIS Server.

    :param layer: Layer to inspect
    :type layer: Layer

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :param generating_qgis_capabilities: internal Flag for the method to tell
        that this function were executed to generate QGIS GetCapabilities
        request for querying Style list. This flag is used for recursion.
        Default to False as recursion base.
    :type generating_qgis_capabilities: bool

    :return: List of QGISServerStyle
    :rtype: list(QGISServerStyle)
    """
    # We get the list of style from GetCapabilities request
    # Must call from public URL because we need public LegendURL
    url = wms_get_capabilities_url(layer, internal=internal)
    try:
        response = requests.get(url)

        root_xml = dlxml.fromstring(ensure_string(response.content))
        styles_xml = root_xml.xpath(
            'wms:Capability/wms:Layer/wms:Layer/wms:Style',
            namespaces={
                'xlink': 'http://www.w3.org/1999/xlink',
                'wms': 'http://www.opengis.net/wms'
            })

        # Fetch styles body
        try:
            qgis_layer = QGISServerLayer.objects.get(layer=layer)
        except QGISServerLayer.DoesNotExist:
            msg = f'No QGIS Server Layer for existing layer {layer.name}'
            logger.debug(msg)
            raise

        styles_obj = [
            QGISServerStyle.from_get_capabilities_style_xml(
                qgis_layer, style_xml)[0]
            for style_xml in styles_xml]

        # Only tried to generate/fix QGIS GetCapabilities to return correct style
        # list, if:
        # - the current request return empty styles_obj (no styles, not possible)
        # - does not currently tried to generate QGIS GetCapabilities to fix this
        #   problem
        if not styles_obj and not generating_qgis_capabilities:
            # It's not possible to have empty style. There will always be default
            # style.
            # Initiate a dummy requests to trigger build style list on QGIS Server
            # side

            # write an empty file if it doesn't exists
            open(qgis_layer.qml_path, 'a').close()

            # Basically add a new style then deletes it to force QGIS to refresh
            # style list in project properties. We don't care the request result.
            dummy_style_name = '__tmp__dummy__name__'
            style_url = style_add_url(layer, dummy_style_name)
            requests.get(style_url)
            style_url = style_remove_url(layer, dummy_style_name)
            requests.get(style_url)

            # End the requests and rely on the next request to build style models
            # to avoid infinite recursion

            # Set generating_qgis_capabilities flag to True to avoid next
            # recursion
            return style_list(
                layer, internal=internal, generating_qgis_capabilities=True)

        # Manage orphaned styles
        style_names = [s.name for s in styles_obj]
        for style in qgis_layer.styles.all():
            if style.name not in style_names:
                if style == qgis_layer.default_style:
                    qgis_layer.default_style = None
                    qgis_layer.save()
                style.delete()

        # Set default style if not yet set
        set_default_style = False
        try:
            if not qgis_layer.default_style:
                set_default_style = True
        except Exception:
            set_default_style = True

        if set_default_style and styles_obj:
            qgis_layer.default_style = styles_obj[0]
            qgis_layer.save()

        return styles_obj
    except Exception:
        msg = f'No QGIS Style for existing layer {layer.name}'
        logger.debug(msg)
        raise


def create_qgis_project(
        layer, qgis_project_path, overwrite=False, internal=True):
    """Create a new QGS Project for a given layer.

    :param layer: Layer or list of layers
    :type layer: geonode.layers.models.Layer,
        list(geonode.layers.models.Layer)

    :param qgis_project_path: Path to to create qgis project
    :type qgis_project_path: str

    :param overwrite: Flag to recreate QGIS Project if necessary
    :type overwrite: bool

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool
    """
    if isinstance(layer, Layer):
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
        files = qgis_layer.base_layer_path
        names = layer.name
        logger.debug(f'File {files} is exists: {str(os.path.exists(files))}')
    elif isinstance(layer, list):
        qgis_layer = []
        for lyr in layer:
            qgis_layer.append(QGISServerLayer.objects.get(layer=lyr))
        files = [ql.base_layer_path for ql in qgis_layer]

        for fl in files:
            logger.debug(f'File {fl} is exists: {str(os.path.exists(fl))}')

        files = ';'.join(files)

        names = [lyr.name for lyr in layer]
        names = ';'.join(names)
    else:
        raise ValueError(
            f'Unexpected argument layer: {layer}')

    overwrite = str(overwrite).lower()

    query_string = {
        'SERVICE': 'MAPCOMPOSITION',
        'PROJECT': qgis_project_path,
        'FILES': files,
        'NAMES': names,
        'OVERWRITE': overwrite,
        'REMOVEQML': True
    }
    qgis_server_url = qgis_server_endpoint(internal)
    response = requests.get(qgis_server_url, params=query_string)
    return response


def delete_orphaned_qgis_server_layers():
    """Delete orphaned QGIS Server files."""
    layer_path = settings.QGIS_SERVER_CONFIG['layer_directory']
    if not os.path.exists(layer_path):
        print(f"{layer_path} not exists")
        return
    for filename in os.listdir(layer_path):
        basename, __ = os.path.splitext(filename)
        fn = os.path.join(layer_path, filename)
        if QGISServerLayer.objects.filter(
                base_layer_path__icontains=basename).count() == 0:
            print(f"Removing orphan layer file {fn}")
            try:
                os.remove(fn)
            except OSError:
                print(f"Could not delete file {fn}")


def delete_orphaned_qgis_server_caches():
    """Delete orphaned QGIS Server tile caches."""
    tiles_path = settings.QGIS_SERVER_CONFIG['tiles_directory']
    if not os.path.exists(tiles_path):
        print(f"{tiles_path} not exists")
        return
    for basename in os.listdir(tiles_path):
        path = os.path.join(tiles_path, basename)
        if QGISServerLayer.objects.filter(
                base_layer_path__icontains=basename).count() == 0:
            print(f"Removing orphan layer file {path}")
            try:
                shutil.rmtree(path)
            except OSError:
                print(f"Could not delete file {path}")


def get_model_path(instance):
    """Get a Django model instance's app label and name.

    :param instance: An instance of a Django model
    :type instance: django.db.models.Model
    """

    model_type = ContentType.objects.get_for_model(instance)
    return f"{model_type.app_label}.{model_type.model}"
