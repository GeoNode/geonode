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
from django.core.files import File
from django.core.urlresolvers import reverse
from django.http import HttpResponse, Http404
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseServerError)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from geonode.layers.models import Layer
from geonode.qgis_server.forms import QGISLayerStyleUploadForm
from geonode.qgis_server.helpers import (
    tile_url_format,
    create_qgis_project,
    legend_url,
    tile_url,
    qgis_server_endpoint)
from geonode.qgis_server.models import QGISServerLayer
from geonode.qgis_server.tasks.update import (
    create_qgis_server_thumbnail,
    cache_request)

logger = logging.getLogger('geonode.qgis_server.views')

QGIS_SERVER_CONFIG = settings.QGIS_SERVER_CONFIG


def download_zip(request, layername):
    """Download a zip file containing every files we have about the layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :return: The HTTPResponse with a ZIP.
    """
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
    # Files (local path) to put in the .zip
    filenames = qgis_layer.files
    # Exclude qgis project files, because it contains server specific path
    filenames = [f for f in filenames if not f.endswith('.qgs')]

    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    zip_subdir = layer.name
    zip_filename = "%s.zip" % zip_subdir

    # Open StringIO to grab in-memory ZIP contents
    s = StringIO.StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    for fpath in filenames:
        # Calculate path for file in zip
        fdir, fname = os.path.split(fpath)

        zip_path = os.path.join(zip_subdir, fname)

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


def legend(request, layername, layertitle=False):
    """Get the legend from a layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :param layertitle: Add the layer title in the legend. Default to False.
    :type layertitle: bool

    :return: The HTTPResponse with a PNG.
    """
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

    legend_path = QGIS_SERVER_CONFIG['legend_path']
    legend_filename = legend_path % qgis_layer.qgis_layer_name

    if not os.path.exists(legend_filename):

        if not os.path.exists(os.path.dirname(legend_filename)):
            os.makedirs(os.path.dirname(legend_filename))

        url = legend_url(layer, layertitle, internal=True)

        result = cache_request.delay(url, legend_filename)

        # Attempt to run task synchronously
        if not result.get():
            # If not succeded, provides error message.
            return HttpResponseServerError('Failed to fetch legend.')

    if image_format(legend_filename) != 'png':
        logger.error('%s is not valid PNG.' % legend_filename)
        os.remove(legend_filename)

    if not os.path.exists(legend_filename):
        return HttpResponse('The legend could not be found.', status=409)

    with open(legend_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def tile_404(request, layername):
    """This view is used when the user try to use the raw tile URL.

    When the URL contains {z}/{x}/{y}.png, display this page.

    :param layername: The layer name in Geonode.
    :type layername: basestring
    """
    layer = get_object_or_404(Layer, name=layername)
    get_object_or_404(QGISServerLayer, layer=layer)

    msg = _(
        'You should use a GIS software or a library which support TMS service '
        'to use this URL : {url}').format(url=tile_url_format(layername))
    return TemplateResponse(
        request,
        '404.html',
        {
            'message': msg
        },
        status=404).render()


def tile(request, layername, z, x, y):
    """Get the tile from a layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :param z: TMS coordinate, zoom parameter
    :type z: int, str

    :param x: TMS coordinate, longitude parameter
    :type x: int, str

    :param y: TMS coordinate, latitude parameter
    :type y: int, str

    :return: The HTTPResponse with a PNG.
    """
    x = int(x)
    y = int(y)
    z = int(z)

    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

    tile_path = QGIS_SERVER_CONFIG['tile_path']
    tile_filename = tile_path % (qgis_layer.qgis_layer_name, z, x, y)

    if not os.path.exists(tile_filename):

        if not os.path.exists(os.path.dirname(tile_filename)):
            os.makedirs(os.path.dirname(tile_filename))

        # Use internal url
        url = tile_url(layer, z, x, y, internal=True)

        result = cache_request.delay(url, tile_filename)

        # Attempt to run task synchronously
        if not result.get():
            # If not succeded, provides error message.
            return HttpResponseServerError('Failed to fetch tile.')

    if image_format(tile_filename) != 'png':
        logger.error('%s is not valid PNG.' % tile_filename)
        os.remove(tile_filename)

    if not os.path.exists(tile_filename):
        return HttpResponse('The tile could not be found.', status=409)

    with open(tile_filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/png')


def layer_ogc_request(request, layername):
    """Provide one OGC server per layer, with their own GetCapabilities.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :return: The HTTPResponse with the response from QGIS Server.
    """
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

    params = {
        'MAP': qgis_layer.qgis_project_path,
    }
    params.update(request.GET or request.POST)
    response = requests.get(QGIS_SERVER_CONFIG['qgis_server_url'], params)

    # We need to replace every references to the internal QGIS Server IP to
    # the public Geonode URL.
    public_url = requests.compat.urljoin(
        settings.SITEURL,
        reverse('qgis_server:layer-request', kwargs={'layername': layername}))

    is_text = response.headers.get('content-type').startswith('text')
    raw = response.content
    if is_text:
        raw = raw.replace(
           QGIS_SERVER_CONFIG['qgis_server_url'], public_url)

    return HttpResponse(raw, content_type=response.headers.get('content-type'))


def geotiff(request, layername):
    """Get the GeoTiff from a layer if available.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :return: The HTTPResponse with a geotiff.
    """
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

    # get geotiff file if exists
    for ext in QGISServerLayer.geotiff_format:
        target_file = qgis_layer.qgis_layer_path_prefix + '.' + ext
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
    map_param = params.get('MAP')
    if not map_param and (params.get('LAYERS') or params.get('TYPENAME')):
        # LAYERS is for WMS, TYPENAME for WFS
        layer_name = params.get('LAYERS') or params.get('TYPENAME')

        if len(layer_name.split(',')) > 1:
            return HttpResponse(
                'We do not support many layers in the request')

        layer = get_object_or_404(Layer, name=layer_name)
        qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
        params['MAP'] = qgis_layer.qgis_project_path

    # We have some shortcuts here instead of asking QGIS-Server.
    if params.get('SERVICE') == 'WMS':
        if params.get('REQUEST') == 'GetLegendGraphic':
            if not params.get('LAYERS'):
                raise Http404('LAYERS is not found for a GetLegendGraphic')
            layer = get_object_or_404(Layer, name=params.get('LAYERS'))
            return legend(request, layername=layer.name)

    # if not shortcut, we forward any request to internal QGIS Server
    qgis_server_url = qgis_server_endpoint(internal=True)
    response = requests.get(qgis_server_url, params)
    return HttpResponse(
        response.content, content_type=response.headers.get('content-type'))


def qgis_server_pdf(request):
    print_url = reverse('qgis_server:map-print')

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


def qml_style(request, layername):
    """Update/Retrieve QML style of a given QGIS Layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring
    :return:
    """
    layer = get_object_or_404(Layer, name=layername)

    if request.method == 'GET':
        # Take QML file from QGIS Server directory
        qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
        qml_path = qgis_layer.qml_path

        if not os.path.exists(qml_path):
            raise Http404(
                'This layer does not have current default QML style.')

        response = HttpResponse(
            open(qml_path), content_type="application/text")
        # ..and correct content-disposition
        response['Content-Disposition'] = (
            'attachment; filename={filename}'.format(
                filename=os.path.basename(qml_path)))
        return response
    elif request.method == 'POST':

        # For people who uses API request
        if not request.user.has_perm(
                'change_resourcebase', layer.get_self_resource()):
            return HttpResponse(
                'User does not have permission to change QML style.',
                status=401)

        form = QGISLayerStyleUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return TemplateResponse(
                request,
                'qgis_server/forms/qml_style.html',
                {
                    'resource': layer,
                    'style_upload_form': form
                },
                status=200).render()

        try:
            uploaded_qml = request.FILES['qml']

            # update qml in uploaded media folder
            # check upload session, is qml file exists?
            layerfile_set = layer.upload_session.layerfile_set
            qml_layer_file, created = layerfile_set.get_or_create(name='qml')

            try:
                qml_path = qml_layer_file.file.path
                content = uploaded_qml.read()
                with open(qml_path, mode='w') as f:
                    f.write(content)
            except ValueError:
                layer_base_path, __ = layer.get_base_file()
                layer_prefix, __ = os.path.splitext(
                    layer_base_path.file.path)
                qml_path = '{prefix}.qml'.format(prefix=layer_prefix)

                content = uploaded_qml.read()

                qml_layer_file.file = File(
                    uploaded_qml,
                    name=os.path.basename(qml_path))
                qml_layer_file.base = False
                qml_layer_file.upload_session = layer.upload_session
                qml_layer_file.save()

            # update qml in QGIS Layer folder
            qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

            with open(qgis_layer.qml_path, mode='w') as f:
                f.write(content)

            # update QGIS Project files
            response = create_qgis_project(
                layer,
                qgis_layer.qgis_project_path,
                overwrite=True,
                internal=True)
            if not response.content == 'OK':
                return HttpResponseServerError(
                    'Failed to create new QGIS Project.'
                    'Error: {0}'.format(response.content))

            # Because we update a style, we need to recache
            qgis_tiles_directory = settings.QGIS_SERVER_CONFIG['tiles_directory']

            layer_tiles_path = os.path.join(
                qgis_tiles_directory, qgis_layer.qgis_layer_name)

            try:
                shutil.rmtree(layer_tiles_path)
            except:
                pass

            return TemplateResponse(
                request,
                'qgis_server/forms/qml_style.html',
                {
                    'resource': layer,
                    'style_upload_form': form,
                    'success': True
                },
                status=200).render()

        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError()

    return HttpResponseBadRequest()


def set_thumbnail(request, layername):
    """Update thumbnail based on map extent

    :param layername: The layer name in Geonode.
    :type layername: basestring
    :return:
    """
    if request.method != 'POST':
        return HttpResponseBadRequest()

    layer = get_object_or_404(Layer, name=layername)

    # For people who uses API request
    if not request.user.has_perm(
            'change_resourcebase', layer.get_self_resource()):
        return HttpResponse(
            'User does not have permission to change thumbnail.',
            status=401)

    # extract bbox
    bbox_string = request.POST['bbox']
    # BBox should be in the format: [xmin,ymin,xmax,ymax], EPSG:4326
    bbox = bbox_string.split(',')
    bbox = [float(s) for s in bbox]

    # Give thumbnail creation to celery tasks, and exit.
    create_qgis_server_thumbnail.delay(layer, overwrite=True, bbox=bbox)
    retval = {
        'success': True
    }
    return HttpResponse(
        json.dumps(retval), content_type="application/json")
