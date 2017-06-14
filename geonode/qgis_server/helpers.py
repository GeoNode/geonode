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
from requests import Request
from urlparse import urljoin

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse

from geonode.qgis_server.models import QGISServerLayer

from geonode import qgis_server
from geonode.geoserver.helpers import OGC_Servers_Handler

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


def tile_url(layer_name):
    """Construct QGIS Server URL for tiles according to a layer.

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


def map_thumbnail_url(instance):
    """Construct QGIS Server Url to fetch remote map thumbnail.

    :param instance: Map object
    :type instance: geonode.maps.models.Map

    :return: thumbnail url
    :rtype: str
    """
    map_id = instance.id
    layers = 'map_%s' % map_id
    qgis_server_config = settings.QGIS_SERVER_CONFIG
    qgis_project = os.path.join(
        qgis_server_config['layer_directory'], '{0}.qgs'.format(layers))
    if not os.path.exists(qgis_project):
        msg = 'Map project not found for %s' % qgis_project
        logger.debug(msg)
        return None

    # We get the extent of these layers.
    bbox = [float(i) for i in instance.bbox_string.split(',')]
    return thumbnail_url(bbox, layers, qgis_project)


def layer_thumbnail_url(instance):
    """Construct QGIS Server Url to fetch remote layer thumbnail.

    :param instance: Layer object
    :type instance: geonode.layers.models.Layer

    :return: Thumbnail URL.
    :rtype: str
    """
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=instance)
    except QGISServerLayer.DoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % instance.name
        logger.debug(msg)
        return None

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)
    qgis_project = basename + '.qgs'
    layers = instance.name

    # We get the extent of the layer.
    x_min = instance.resourcebase_ptr.bbox_x0
    x_max = instance.resourcebase_ptr.bbox_x1
    y_min = instance.resourcebase_ptr.bbox_y0
    y_max = instance.resourcebase_ptr.bbox_y1
    bbox = [x_min, y_min, x_max, y_max]

    return thumbnail_url(bbox, layers, qgis_project)


def thumbnail_url(bbox, layers, qgis_project):
    """Internal function to generate the URL for the thumbnail.

    :param bbox: The bounding box to use in the format [left,bottom,right,top].
    :type bbox: list

    :param layers: Name of the layer to use.
    :type layers: basestring

    :param qgis_project: The path to the QGIS project.
    :type qgis_project: basestring

    :return: The WMS URL to fetch the thumbnail.
    :rtype: basestring
    """
    # The generated URL is not a direct URL to QGIS Server,
    # but it was a proxy from django instead.
    endpoint_url = reverse('qgis_server:request')
    site_url = settings.SITEURL
    qgis_server_url = urljoin(site_url, endpoint_url)
    x_min, y_min, x_max, y_max = bbox
    # We calculate the margins according to 10 percent.
    percent = 10
    delta_x = (x_max - x_min) / 100 * percent
    delta_y = (y_max - y_min) / 100 * percent
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
    url = Request('GET', qgis_server_url, params=query_string).prepare().url
    return url
