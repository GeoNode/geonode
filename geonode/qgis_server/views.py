# -*- coding: utf-8 -*-

import os
import logging
import zipfile
import StringIO
from imghdr import what as image_format

from urllib import urlretrieve
from django.http import HttpResponse, Http404
from django.db.models import ObjectDoesNotExist
from geonode.layers.models import Layer
from geonode.qgis_server.models import QGISServerLayer
from geonode.qgis_server.gis_tools import num2deg
from geonode.settings import QGIS_SERVER_CONFIG

__author__ = 'ismailsunni'
__project_name__ = 'geonode'
__filename__ = 'views'
__date__ = '1/29/16'
__copyright__ = 'imajimatika@gmail.com'

logger = logging.getLogger('geonode.qgis_server.views')


def download_zip(request, layername):
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
    resp = HttpResponse(s.getvalue(), mimetype = "application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp


def legend(request, layername):
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

        qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']
        query_string = {
            'MAP': basename + '.qgs',
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetLegendGraphic',
            'LAYER': layer.name,
            'FORMAT': 'image/png'
        }

        url = qgis_server + '?'
        for param, value in query_string.iteritems():
            url += param + '=' + value + '&'

        urlretrieve(url, legend_filename)

        if image_format(legend_filename) != 'png':
            logger.error('%s is not valid PNG.' % legend_filename)
            os.remove(legend_filename)

    if not os.path.exists(legend_filename):
        return HttpResponse('The legend could not be found.', status=409)

    with open(legend_filename, 'rb') as f:
        return HttpResponse(f.read(), mimetype='image/png')


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
            'DPI': '96',
            'MAP_RESOLUTION': '96',
            'FORMAT_OPTIONS': 'dpi:96'
        }

        url = qgis_server + '?'
        for param, value in query_string.iteritems():
            url += param + '=' + value + '&'

        urlretrieve(url, thumbnail_filename)

        if image_format(thumbnail_filename) != 'png':
            logger.error('%s is not valid PNG.' % thumbnail_filename)
            os.remove(thumbnail_filename)

        if not os.path.exists(thumbnail_filename):
            msg = 'The thumbnail could not be found.'
            return HttpResponse(msg, status=409)

    with open(thumbnail_filename, 'rb') as f:
        return HttpResponse(f.read(), mimetype='image/png')


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
        bbox = ','.join([str(val) for val in [bottom, left, top, right]])

        qgis_server = QGIS_SERVER_CONFIG['qgis_server_url']
        query_string = {
            'SERVICE': 'WMS',
            'VERSION': '1.3.0',
            'REQUEST': 'GetMap',
            'BBOX': bbox,
            'CRS': 'EPSG:4326',
            'WIDTH': '256',
            'HEIGHT': '256',
            'MAP': basename + '.qgs',
            'LAYERS': layer.name,
            'STYLES': 'default',
            'FORMAT': 'image/png',
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
        return HttpResponse(f.read(), mimetype='image/png')


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
        return HttpResponse(f.read(), mimetype='image/png')


def wms(request):
    logger.debug('WMS from QGIS Server')

    # Sample parameters from the geoext.
    # LAYERS : geonode:buildings
    # STYLES :
    # WIDTH : 256
    # SERVICE : WMS
    # FORMAT : image/png
    # REQUEST : GetMap
    # HEIGHT : 256
    # SRS : EPSG:900913
    # VERSION : 1.1.1
    # TILED : true
    # TRANSPARENT : TRUE
    # BBOX : 11891155.614613,-689767.74314941,11892378.607065,-688544.75069702

    params = dict()
    for key, value in request.GET.iteritems():
        params[key] = value
    # We need to replace 900913 with 3857. Deprecated in QGIS 2.14
    if params.get('SRS') == 'EPSG:900913':
        params['SRS'] = 'EPSG:3857'
    if params.get('SERVICE') == 'WMS':
        if params.get('REQUEST') == 'GetMap':
            return wms_get_map(params)