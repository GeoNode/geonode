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

import StringIO
import json
import logging
import os
import shutil
import zipfile
from imghdr import what as image_format

import requests
from django.conf import settings
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Point
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404

from geonode.layers.models import Layer
from geonode.qgis_server.gis_tools import num2deg
from geonode.qgis_server.models import QGISServerLayer

logger = logging.getLogger('geonode.qgis_server.views')

QGIS_SERVER_CONFIG = settings.QGIS_SERVER_CONFIG


def download_zip(request, layername, access_token=None):
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
    basename, _ = os.path.splitext(qgis_layer.base_layer_path)
    # Files (local path) to put in the .zip
    filenames = []
    for ext in QGISServerLayer.accepted_format:
        target_file = basename + '.' + ext
        if os.path.exists(target_file):
            filenames.append(target_file)

    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    zip_subdir = layer.name
    zip_filename = "%s.zip" % zip_subdir

    # Open StringIO to grab in-memory ZIP contents
    s = StringIO.StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        logger.debug('fpath: %s' % fpath)
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)
        logger.debug('fdir: %s' % fdir)
        logger.debug('fname: %s' % fname)

        zip_path = os.path.join(zip_subdir, fname)
        logger.debug('zip_path: %s' % zip_path)

        # Add file, at correct path
        zf.write(fpath, zip_path)

    # Must close zip for all contents to be written
    zf.close()

    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(
        s.getvalue(), content_type="application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp


def legend(request, layername, layertitle=None, access_token=None):
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    legend_path = QGIS_SERVER_CONFIG['legend_path']
    legend_filename = legend_path % os.path.basename(basename)

    if not os.path.exists(legend_filename):

        if not os.path.exists(os.path.dirname(legend_filename)):
            os.makedirs(os.path.dirname(legend_filename))

        if not layertitle:
            layertitle = 'FALSE'

        qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']
        query_string = {
            'MAP': basename + '.qgs',
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetLegendGraphic',
            'LAYER': layer.name,
            'LAYERTITLE': layertitle,
            'FORMAT': 'image/png',
            'TILED': 'true',
            'TRANSPARENT': 'true',
            'LEGEND_OPTIONS': (
                'fontAntiAliasing:true;fontSize:11;fontName:Arial')
        }

        response = requests.get(qgis_server, params=query_string, stream=True)
        with open(legend_filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response

        if image_format(legend_filename) != 'png':
            logger.error('%s is not valid PNG.' % legend_filename)
            os.remove(legend_filename)

    if not os.path.exists(legend_filename):
        return HttpResponse('The legend could not be found.', status=409)

    with open(legend_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def tile(request, layername, z, x, y):
    x = int(x)
    y = int(y)
    z = int(z)

    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    tile_path = QGIS_SERVER_CONFIG['tile_path']
    tile_filename = tile_path % (os.path.basename(basename), z, x, y)

    if not os.path.exists(tile_filename):

        if not os.path.exists(os.path.dirname(tile_filename)):
            os.makedirs(os.path.dirname(tile_filename))

        # Call the WMS
        top, left = num2deg(x, y, z)
        bottom, right = num2deg(x + 1, y + 1, z)

        transform = CoordTransform(
            SpatialReference(4326), SpatialReference(3857))
        top_left_corner = Point(left, top, srid=4326)
        bottom_right_corner = Point(right, bottom, srid=4326)
        top_left_corner.transform(transform)
        bottom_right_corner.transform(transform)

        bottom = bottom_right_corner.y
        right = bottom_right_corner.x
        top = top_left_corner.y
        left = top_left_corner.x

        bbox = ','.join([str(val) for val in [left, bottom, right, top]])

        qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'BBOX': bbox,
            'CRS': 'EPSG:3857',
            'WIDTH': '256',
            'HEIGHT': '256',
            'MAP': basename + '.qgs',
            'LAYERS': layer.name,
            'STYLES': 'default',
            'FORMAT': 'image/png',
            'TRANSPARENT': 'true',
            'DPI': '96',
            'MAP_RESOLUTION': '96',
            'FORMAT_OPTIONS': 'dpi:96'
        }

        response = requests.get(qgis_server, params=query_string, stream=True)
        with open(tile_filename, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response

        if image_format(tile_filename) != 'png':
            logger.error('%s is not valid PNG.' % tile_filename)
            os.remove(tile_filename)

    if not os.path.exists(tile_filename):
        return HttpResponse('The legend could not be found.', status=409)

    with open(tile_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def geotiff(request, layername, access_token=None):
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    # get geotiff file if exists
    for ext in QGISServerLayer.geotiff_format:
        target_file = basename + '.' + ext
        if os.path.exists(target_file):
            filename = target_file
            break
    else:
        filename = None

    if not filename:
        msg = 'No Geotiff layer found for %s' % layername
        logger.debug(msg)
        raise Http404(msg)

    with open(filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/tiff')


def ascii(request, layername, access_token=None):
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    # get geotiff file if exists
    for ext in QGISServerLayer.ascii_format:
        target_file = basename + '.' + ext
        if os.path.exists(target_file):
            filename = target_file
            break
    else:
        filename = None

    if not filename:
        msg = 'No ASCII layer found for %s' % layername
        logger.debug(msg)
        raise Http404(msg)

    with open(filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='text/asc')


def qgis_server_request(request):
    """View to forward OGC request to QGIS Server."""
    # Make a copy of the query string with capital letters for the key.
    query = request.GET or request.POST
    params = {
        param.upper(): value for param, value in query.iteritems()}

    # 900913 is deprecated
    if params.get('SRS') == 'EPSG:900913':
        params['SRS'] = 'EPSG:3857'
    if params.get('CRS') == 'EPSG:900913':
        params['CRS'] = 'EPSG:3857'

    # As we have one QGIS project per layer, we don't support GetCapabilities
    # for now without any layer. We know, it's not OGC compliant.
    if params.get('REQUEST') == 'GetCapabilities':
        if not params.get('LAYERS') or params.get('TYPENAME'):
            return HttpResponse('GetCapabilities is not supported yet.')

    # As we have one project per layer, we add the MAP path if the request is
    # specific for one layer.
    if params.get('LAYERS') or params.get('TYPENAME'):
        # LAYERS is for WMS, TYPENAME for WFS
        layer_name = params.get('LAYERS') or params.get('TYPENAME')

        if len(layer_name.split(',')) > 1:
            return HttpResponse(
                'We do not support many layers in the request')

        layer = get_object_or_404(Layer, name=layer_name)
        qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
        basename, _ = os.path.splitext(qgis_layer.base_layer_path)
        params['MAP'] = basename + '.qgs'

    # We have some shortcuts here instead of asking QGIS-Server.
    if params.get('SERVICE') == 'WMS':
        if params.get('REQUEST') == 'GetLegendGraphic':
            if not params.get('LAYERS'):
                raise Http404('LAYERS is not found for a GetLegendGraphic')
            layer = get_object_or_404(Layer, name=params.get('LAYERS'))
            return legend(request, layername=layer.name)

    # if not shortcut, we forward any request to QGIS Server
    response = requests.get(QGIS_SERVER_CONFIG['qgis_server_url'], params)
    return HttpResponse(
        response.content, content_type=response.headers.get('content-type'))


def qgis_server_pdf(request):
    print_url = reverse('qgis-server-map-print')

    response_data = {
        "scales": [
            {"name": "1:25,000", "value": "25000.0"},
            {"name": "1:50,000", "value": "50000.0"},
            {"name": "1:100,000", "value": "100000.0"},
            {"name": "1:200,000", "value": "200000.0"},
            {"name": "1:500,000", "value": "500000.0"},
            {"name": "1:1,000,000", "value": "1000000.0"},
            {"name": "1:2,000,000", "value": "2000000.0"},
            {"name": "1:4,000,000", "value": "4000000.0"}
        ],
        "dpis": [
            {"name": "75", "value": "75"},
            {"name": "150", "value": "150"},
            {"name": "300", "value": "300"}
        ],
        "outputFormats": [
            {"name": "pdf"}
        ],
        "layouts": [
            {
                "name": "A4 portrait",
                "map": {
                    "width": 440,
                    "height": 483
                },
                "rotation": True
            },
            {
                "name": "Legal",
                "map": {
                    "width": 440,
                    "height": 483
                },
                "rotation": False
            }
        ],
        "printURL": "%s" % print_url,
        "createURL": "%s" % print_url
    }

    return HttpResponse(
        json.dumps(response_data), content_type="application/json")


def qgis_server_map_print(request):
    logger.debug('qgis_server_map_print')
    temp = []
    for key, value in request.POST.iteritems():
        temp[key] = value
        print key
        print value
        print '--------'
    return HttpResponse(
        json.dumps(temp), content_type="application/json")
