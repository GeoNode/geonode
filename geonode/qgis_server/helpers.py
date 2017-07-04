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
import os
import re
import shutil
from urlparse import urljoin

import math
import requests
from django.conf import settings
from django.contrib.gis.gdal import CoordTransform, SpatialReference
from django.contrib.gis.geos import GEOSGeometry, Point
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from requests import Request

from geonode import qgis_server
from geonode.geoserver.helpers import OGC_Servers_Handler
from geonode.layers.models import Layer
from geonode.qgis_server.gis_tools import num2deg
from geonode.qgis_server.models import QGISServerLayer, QGISServerMap

logger = logging.getLogger(__file__)
ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)['default']


def validate_django_settings():
    """Check that settings file configured correctly for qgis_server backend.
    """
    # geonode.qgis_server must exists in INSTALLED_APPS and not geoserver
    if 'geonode.qgis_server' not in settings.INSTALLED_APPS:
        raise ImproperlyConfigured(
            'geonode.qgis_server module not included in INSTALLED_APPS.')
    if 'geonode.geoserver' in settings.INSTALLED_APPS:
        raise ImproperlyConfigured(
            'You want to use QGIS Server backend, but geonode.geoserver module'
            ' is still included in INSTALLED_APPS.')

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

    if not settings.LAYER_PREVIEW_LIBRARY == 'leaflet':
        raise ImproperlyConfigured(
            'QGIS Server at the moment only works with '
            'LAYER_PREVIEW_LIBRARY = leaflet.')

    # Check OGC Server settings
    default_ogc_backend = settings.OGC_SERVER['default']

    if not default_ogc_backend['BACKEND'] == qgis_server.BACKEND_PACKAGE:
        raise ImproperlyConfigured(
            "OGC_SERVER['default']['BACKEND'] should be set to "
            "{package}.".format(package=qgis_server.BACKEND_PACKAGE))

    return True


def transform_layer_bbox(layer, target_crs):
    """

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
        site_url = settings.SITEURL
        qgis_server_url = urljoin(site_url, endpoint_url)
        return qgis_server_url


def tile_url_format(layer_name):
    """Construct proxied QGIS Server URL format for tiles.

    This url is not an actual request, but rather a format url
    that can be used by TMS service to generate tile request according
    to this layer.

    :param layer_name: The layer name from the QGIS backend
    :type layer_name: basestring

    :return: Tile url
    :rtype: basestring
    """
    # We request a fake tile to get the real URL.
    url = reverse(
        'qgis_server:tile',
        kwargs={
            'layername': layer_name,
            'x': 5678,
            'y': 910,
            'z': 1234
        })
    url = urljoin(settings.SITEURL, url)
    url = url.replace('1234/5678/910', '{z}/{x}/{y}')
    return url


def tile_url(layer, z, x, y, internal=True):
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

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: Tile url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = 'No QGIS Server Layer for existing layer {0}'.format(
            layer.name)
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

    query_string = {
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetMap',
        'BBOX': bbox,
        'CRS': 'EPSG:3857',
        'WIDTH': '256',
        'HEIGHT': '256',
        'MAP': qgis_layer.qgis_project_path,
        'LAYERS': layer.name,
        'STYLES': 'default',
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
        msg = 'No QGIS Server Map for existing map {0}'.format(instance.title)
        logger.debug(msg)
        raise

    qgis_project = qgis_map.qgis_project_path
    if not os.path.exists(qgis_project):
        msg = 'Map project not found for {0}'.format(qgis_project)
        logger.debug(msg)
        raise ValueError(msg)

    if not bbox:
        # We get the extent of these layers.
        # Reproject, in case of different CRS
        bbox = transform_layer_bbox(instance, 4326)
    return thumbnail_url(
        bbox, qgis_map.qgis_map_name, qgis_project, internal=internal)


def layer_thumbnail_url(instance, bbox=None, internal=True):
    """Construct QGIS Server Url to fetch remote layer thumbnail.

    :param instance: Layer object
    :type instance: geonode.layers.models.Layer

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
        msg = 'No QGIS Server Layer for existing layer {0}'.format(
            instance.name)
        logger.debug(msg)
        raise

    qgis_project = qgis_layer.qgis_project_path
    layers = instance.name

    if not bbox:
        # We get the extent of the layer.
        # Reproject, in case of different CRS
        bbox = transform_layer_bbox(instance, 4326)

    return thumbnail_url(bbox, layers, qgis_project, internal=internal)


def thumbnail_url(bbox, layers, qgis_project, internal=True):
    """Internal function to generate the URL for the thumbnail.

    :param bbox: The bounding box to use in the format [left,bottom,right,top].
    :type bbox: list

    :param layers: Name of the layer to use.
    :type layers: basestring

    :param qgis_project: The path to the QGIS project.
    :type qgis_project: basestring

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
        'VERSION': '1.3.0',
        'REQUEST': 'GetMap',
        'BBOX': bbox,
        'SRS': 'EPSG:4326',
        'WIDTH': '250',
        'HEIGHT': '250',
        'MAP': qgis_project,
        'LAYERS': layers,
        'STYLES': 'default',
        'FORMAT': 'image/png',
        'TRANSPARENT': 'true',
        'DPI': '96',
        'MAP_RESOLUTION': '96',
        'FORMAT_OPTIONS': 'dpi:96'
    }
    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


def legend_url(layer, layertitle=False, internal=True):
    """Construct QGIS Server url to fetch legend.

    :param layer: Layer to use
    :type layer: Layer

    :param layertitle: Layer title flag. Set to True to include layer title
    :type layertitle: bool

    :param internal: Flag to switch between public url and internal url.
        Public url will be served by Django Geonode (proxified).
    :type internal: bool

    :return: QGIS Server request url
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except QGISServerLayer.DoesNotExist:
        msg = 'No QGIS Server Layer for existing layer {0}'.format(layer.name)
        logger.debug(msg)
        raise

    qgis_project_path = qgis_layer.qgis_project_path

    query_string = {
        'MAP': qgis_project_path,
        'SERVICE': 'WMS',
        'VERSION': '1.3.0',
        'REQUEST': 'GetLegendGraphic',
        'LAYER': layer.name,
        'LAYERTITLE': str(layertitle).lower(),
        'FORMAT': 'image/png',
        'TILED': 'true',
        'TRANSPARENT': 'true',
        'LEGEND_OPTIONS': (
            'fontAntiAliasing:true;fontSize:11;fontName:Arial')
    }
    qgis_server_url = qgis_server_endpoint(internal)
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url


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
    elif isinstance(layer, list):
        qgis_layer = []
        for l in layer:
            qgis_layer.append(QGISServerLayer.objects.get(layer=l))
        files = [ql.base_layer_path for ql in qgis_layer]
        files = ';'.join(files)

        names = [l.name for l in layer]
        names = ';'.join(names)
    else:
        raise ValueError(
            'Unexpected argument layer: {0}'.format(layer))

    overwrite = str(overwrite).lower()

    query_string = {
        'SERVICE': 'MAPCOMPOSITION',
        'PROJECT': qgis_project_path,
        'FILES': files,
        'NAMES': names,
        'OVERWRITE': overwrite,
    }
    qgis_server_url = qgis_server_endpoint(internal)
    response = requests.get(qgis_server_url, params=query_string)
    return response


def delete_orphaned_qgis_server_layers():
    """Delete orphaned QGIS Server files."""
    layer_path = settings.QGIS_SERVER_CONFIG['layer_directory']
    for filename in os.listdir(layer_path):
        basename, __ = os.path.splitext(filename)
        fn = os.path.join(layer_path, filename)
        if QGISServerLayer.objects.filter(
                base_layer_path__icontains=basename).count() == 0:
            print 'Removing orphan layer file %s' % fn
            try:
                os.remove(fn)
            except OSError:
                print 'Could not delete file %s' % fn


def delete_orphaned_qgis_server_caches():
    """Delete orphaned QGIS Server tile caches."""
    tiles_path = settings.QGIS_SERVER_CONFIG['tiles_directory']
    for basename in os.listdir(tiles_path):
        path = os.path.join(tiles_path, basename)
        if QGISServerLayer.objects.filter(
                base_layer_path__icontains=basename).count() == 0:
            print 'Removing orphan layer file %s' % path
            try:
                shutil.rmtree(path)
            except OSError:
                print 'Could not delete file %s' % path
