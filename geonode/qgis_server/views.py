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
import logging
import zipfile
import StringIO
import urllib2
import json
from imghdr import what as image_format
from urllib import urlretrieve

from django.conf import settings
from django.http import HttpResponse, Http404
from django.db.models import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import Point

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.qgis_server.models import QGISServerLayer
from geonode.qgis_server.gis_tools import num2deg


logger = logging.getLogger('geonode.qgis_server.views')

QGIS_SERVER_CONFIG = settings.QGIS_SERVER_CONFIG


def download_zip(request, layername, access_token=None):
    try:
        layer = Layer.objects.get(name=layername)
    except ObjectDoesNotExist:
        logger.debug('No layer found for %s' % layername)
        return

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        logger.debug('No QGIS Server Layer for existing layer %s' % layername)
        return

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
    try:
        layer = Layer.objects.get(name=layername)
    except ObjectDoesNotExist:
        msg = 'No layer found for %s' % layername
        logger.debug(msg)
        raise Http404(msg)

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layername
        logger.debug(msg)
        raise Http404(msg)

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
            'LEGEND_OPTIONS': 'fontAntiAliasing:true;fontSize:11;fontName:Arial'
        }

        url = qgis_server + '?'
        for param, value in query_string.iteritems():
            url += param + '=' + value + '&'

        urlretrieve(url, legend_filename)
        logger.info(url)

        if image_format(legend_filename) != 'png':
            logger.error('%s is not valid PNG.' % legend_filename)
            os.remove(legend_filename)

    if not os.path.exists(legend_filename):
        return HttpResponse('The legend could not be found.', status=409)

    with open(legend_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def map_thumbnail(request, map_id):
    logger.debug('Fetching thumbnail for the map %s.' % map_id)
    try:
        map_object = Map.objects.get(id=map_id)
    except ObjectDoesNotExist:
        msg = 'Maps not found for %s' % map_id
        logger.debug(msg)
        raise Http404(msg)

    map_file = 'map_%s' % map_id
    map_project = os.path.join(
        QGIS_SERVER_CONFIG['layer_directory'], map_file + '.qgs')
    if not os.path.exists(map_project):
        msg = 'Map project not found for %s' % map_project
        logger.debug(msg)
        raise Http404(msg)

    thumbnail_filename = QGIS_SERVER_CONFIG['thumbnail_path'] % map_file

    if not os.path.exists(thumbnail_filename):

        if not os.path.exists(os.path.dirname(thumbnail_filename)):
            os.makedirs(os.path.dirname(thumbnail_filename))

        # We get the extent of these layers.
        bbox = [float(i) for i in map_object.bbox_string.split(',')]
        x_min, x_max, y_min, y_max = bbox

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
        qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'BBOX': bbox,
            'CRS': 'EPSG:4326',
            'WIDTH': '250',
            'HEIGHT': '250',
            'MAP': map_project,
            'LAYERS': map_file,
            'STYLES': 'default',
            'FORMAT': 'image/png',
            'TRANSPARENT': 'true',
            'DPI': '96',
            'MAP_RESOLUTION': '96',
            'FORMAT_OPTIONS': 'dpi:96'
        }

        url = qgis_server + '?'
        for param, value in query_string.iteritems():
            url += param + '=' + value + '&'

        urlretrieve(url, thumbnail_filename)
        logger.info(url)

        if image_format(thumbnail_filename) != 'png':
            logger.error('%s is not valid PNG.' % thumbnail_filename)
            os.remove(thumbnail_filename)

        if not os.path.exists(thumbnail_filename):
            msg = 'The thumbnail could not be found.'
            return HttpResponse(msg, status=409)

    with open(thumbnail_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def thumbnail(request, layername):
    try:
        layer = Layer.objects.get(name=layername)
    except ObjectDoesNotExist:
        msg = 'No layer found for %s' % layername
        logger.debug(msg)
        raise Http404(msg)

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layername
        logger.debug(msg)
        raise Http404(msg)

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    thumbnail_path = QGIS_SERVER_CONFIG['thumbnail_path']
    thumbnail_filename = thumbnail_path % os.path.basename(basename)

    if not os.path.exists(thumbnail_filename):

        if not os.path.exists(os.path.dirname(thumbnail_filename)):
            os.makedirs(os.path.dirname(thumbnail_filename))

        # We get the extent of the layer.
        x_min = layer.resourcebase_ptr.bbox_x0
        x_max = layer.resourcebase_ptr.bbox_x1
        y_min = layer.resourcebase_ptr.bbox_y0
        y_max = layer.resourcebase_ptr.bbox_y1

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

        qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'BBOX': bbox,
            'CRS': 'EPSG:4326',
            'WIDTH': '250',
            'HEIGHT': '250',
            'MAP': basename + '.qgs',
            'LAYERS': layer.name,
            'STYLES': 'default',
            'FORMAT': 'image/png',
            'TRANSPARENT': 'true',
            'DPI': '96',
            'MAP_RESOLUTION': '96',
            'FORMAT_OPTIONS': 'dpi:96'
        }

        url = qgis_server + '?'
        for param, value in query_string.iteritems():
            url += param + '=' + value + '&'

        urlretrieve(url, thumbnail_filename)
        logger.info(url)

        if image_format(thumbnail_filename) != 'png':
            logger.error('%s is not valid PNG.' % thumbnail_filename)
            os.remove(thumbnail_filename)

        if not os.path.exists(thumbnail_filename):
            msg = 'The thumbnail could not be found.'
            return HttpResponse(msg, status=409)

    with open(thumbnail_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def tile(request, layername, z, x, y):
    x = int(x)
    y = int(y)
    z = int(z)

    try:
        layer = Layer.objects.get(name=layername)
    except ObjectDoesNotExist:
        msg = 'No layer found for %s' % layername
        logger.debug(msg)
        raise Http404(msg)

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layername
        logger.debug(msg)
        raise Http404(msg)

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

        url = qgis_server + '?'
        for param, value in query_string.iteritems():
            url += param + '=' + value + '&'

        urlretrieve(url, tile_filename)

        if image_format(tile_filename) != 'png':
            logger.error('%s is not valid PNG.' % tile_filename)
            os.remove(tile_filename)

    if not os.path.exists(tile_filename):
        return HttpResponse('The legend could not be found.', status=409)

    with open(tile_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def geotiff(request, layername, access_token=None):
    try:
        layer = Layer.objects.get(name=layername)
    except ObjectDoesNotExist:
        msg = 'No layer found for %s' % layername
        logger.debug(msg)
        raise Http404(msg)

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layername
        logger.debug(msg)
        return Http404(msg)

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


def wms_get_map(params):
    logger.debug('WMS GetMap')

    qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']

    layer = Layer.objects.get(typename=params.pop('LAYERS'))
    params['LAYERS'] = layer.name
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layer.name
        logger.debug(msg)
        raise Http404(msg)

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    params['map'] = basename + '.qgs'

    url = qgis_server + '?'
    for param, value in params.iteritems():
        url += param + '=' + value + '&'

    logger.debug(url)

    bbox_string = params['BBOX'].replace('-', 'n')
    bbox = bbox_string.split(',')

    map_tile_path = QGIS_SERVER_CONFIG['map_tile_path']
    tile_filename = map_tile_path % (
        os.path.basename(basename), bbox[0], bbox[1], bbox[2], bbox[3])

    logger.debug(tile_filename)

    if not os.path.exists(tile_filename):
        if not os.path.exists(os.path.dirname(tile_filename)):
            os.makedirs(os.path.dirname(tile_filename))

        urlretrieve(url, tile_filename)

        if image_format(tile_filename) != 'png':
            logger.error('%s is not valid PNG.' % tile_filename)
            os.remove(tile_filename)

    if not os.path.exists(tile_filename):
        return HttpResponse('The legend could not be found.', status=409)

    with open(tile_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def wms_describe_layer(params):
    logger.debug('WMS DescribeLayer')
    for k, v in params.iteritems():
        logger.debug('%s %s' % (k, v))
    params['SLD_VERSION'] = '1.1.0'

    qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']

    layer = Layer.objects.get(typename=params.pop('LAYERS'))
    params['LAYERS'] = layer.name
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layer.name
        logger.debug(msg)
        raise Http404(msg)

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    params['map'] = basename + '.qgs'

    url = qgis_server + '?'
    for param, value in params.iteritems():
        url += param + '=' + value + '&'

    logger.debug(url)

    result = urllib2.urlopen(url)
    result_list = result.readlines()
    return HttpResponse(
        ''.join(result_list).replace('\n', ''), content_type='text/xml')


def wfs_describe_feature_type(params):
    logger.debug('WFS Describe Feature Type')
    qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']

    layer = Layer.objects.get(typename=params.pop('TYPENAME'))
    params['LAYERS'] = layer.name
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layer.name
        logger.debug(msg)
        raise Http404(msg)

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    params['map'] = basename + '.qgs'

    url = qgis_server + '?'
    for param, value in params.iteritems():
        url += param + '=' + value + '&'

    logger.debug(url)

    result = urllib2.urlopen(url)
    result_list = result.readlines()
    return HttpResponse(
        ''.join(result_list).replace('\n', ''), content_type='text/xml')


def wms_get_feature_info(params):
    logger.debug('WMS GetFeatureInfo')

    qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']

    layer = Layer.objects.get(typename=params.pop('LAYERS'))
    params['LAYERS'] = layer.name
    params['QUERY_LAYERS'] = layer.name
    logger.debug(params['QUERY_LAYERS'])
    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        msg = 'No QGIS Server Layer for existing layer %s' % layer.name
        logger.debug(msg)
        raise Http404(msg)

    basename, _ = os.path.splitext(qgis_layer.base_layer_path)

    params['map'] = basename + '.qgs'

    url = qgis_server + '?'
    for param, value in params.iteritems():
        url += param + '=' + value + '&'

    logger.debug(url)

    result = urllib2.urlopen(url)
    result_list = result.readlines()
    return HttpResponse(
        ''.join(result_list).replace('\n', ''), content_type='text/xml')


def qgis_server_request(request):
    logger.debug('WMS/WFS request to QGIS Server')

    params = dict()
    for key, value in request.GET.iteritems():
        params[key] = value
    # We need to replace 900913 with 3857. Deprecated in QGIS 2.14
    if params.get('SRS') == 'EPSG:900913':
        params['SRS'] = 'EPSG:3857'

    if params.get('SERVICE') == 'WMS':
        if params.get('REQUEST') == 'GetMap':
            return wms_get_map(params)
        elif params.get('REQUEST') == 'DescribeLayer':
            return wms_describe_layer(params)
        elif params.get('REQUEST') == 'GetLegendGraphic':
            layer = Layer.objects.get(typename=params.get('LAYER'))
            return legend(request, layername=layer.name)
        elif params.get('REQUEST') == 'GetFeatureInfo':
            return wms_get_feature_info(params)
        # May be we need to implement for GetStyle also
    elif params.get('SERVICE') == 'WFS':
        if params.get('REQUEST') == 'DescribeFeatureType':
            return wfs_describe_feature_type(params)
        # May be we need to implement for GetFeature, Transaction also


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
