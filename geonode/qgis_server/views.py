# -*- coding: utf-8 -*-

import os
import logging
import zipfile
import StringIO

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
        logger.debug('No layer found for %s' % layername)
        return

    try:
        qgis_layer = QGISServerLayer.objects.get(layer=layer)
    except ObjectDoesNotExist:
        logger.debug('No QGIS Server Layer for existing layer %s' % layername)
        return

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

    if not os.path.exists(legend_filename):
        raise Http404('The legend could not be found')

    with open(legend_filename, 'rb') as f:
        return HttpResponse(f.read(), mimetype='image/png')


def tile(request, layername, z, x, y):
    x = int(x)
    y = int(y)
    z = int(z)

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

    if not os.path.exists(tile_filename):
        raise Http404('The tile could not be found.')

    with open(tile_filename, 'rb') as f:
        return HttpResponse(f.read(), mimetype='image/png')
