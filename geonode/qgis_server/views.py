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

import io
import json
import logging
import os
import zipfile
from imghdr import what as image_format

import re

import datetime
import requests
import shutil
from django.conf import settings
from django.urls import reverse
from django.forms.models import model_to_dict
from django.http import HttpResponse, Http404
from django.http.response import (
    HttpResponseBadRequest,
    HttpResponseServerError)
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from geonode.compat import ensure_string
from geonode.maps.models import MapLayer
from geonode.layers.models import Layer, LayerFile
from geonode.qgis_server.forms import QGISLayerStyleUploadForm
from geonode.qgis_server.helpers import (
    tile_url_format,
    legend_url,
    tile_url,
    qgs_url,
    qlr_url,
    qgis_server_endpoint, style_get_url, style_list, style_add_url,
    style_remove_url, style_set_default_url)
from geonode.qgis_server.models import QGISServerLayer
from geonode.qgis_server.tasks.update import (
    create_qgis_server_thumbnail,
    cache_request)

logger = logging.getLogger('geonode.qgis_server.views')

QGIS_SERVER_CONFIG = settings.QGIS_SERVER_CONFIG if hasattr(settings, 'QGIS_SERVER_CONFIG') else None


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
    zip_filename = f"{zip_subdir}.zip"

    # Open StringIO to grab in-memory ZIP contents
    s = io.StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w", allowZip64=True)

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
    resp['Content-Disposition'] = f'attachment; filename={zip_filename}'

    return resp


def download_qgs(request, layername):
    """Download QGS file for a layer.

    :param request: The request from frontend.
    :type request: HttpRequest

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :return: QGS file.
    """
    layer = get_object_or_404(Layer, name=layername)
    url = qgs_url(layer, internal=True)
    result = requests.get(url)

    # use layer.name if layer.title is empty.
    if layer.title:
        layer_title = layer.title
    else:
        layer_title = layer.name

    response = HttpResponse(
        result.content, content_type="application/x-qgis-project",
        status=result.status_code)
    response['Content-Disposition'] = \
        f'attachment; filename={layer_title}.qgs'

    return response


def download_map(request, mapid):
    """Download a zip file containing every layers on a map.

    :param mapid: The map id in Geonode.
    :type mapid: basestring

    :return: The HTTPResponse with a ZIP.
    """
    map_layers = MapLayer.objects.filter(
        map_id=mapid).order_by('stack_order')
    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    zip_subdir = mapid
    zip_filename = f"{zip_subdir}.zip"

    # Open StringIO to grab in-memory ZIP contents
    s = io.StringIO()

    # The zip compressor
    zf = zipfile.ZipFile(s, "w", allowZip64=True)

    for map_layer in map_layers:
        if 'osm' not in map_layer.layer_title and 'OpenMap' not in map_layer.layer_title:
            layer = get_object_or_404(Layer, name=map_layer.layer_title)
            qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
            # Files (local path) to put in the .zip
            filenames = qgis_layer.files
            # Exclude qgis project files, because it contains server specific path
            filenames = [f for f in filenames if f.endswith('.asc') or
                         f.endswith('.shp') or f.endswith('.tif')]

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
    resp['Content-Disposition'] = f'attachment; filename={zip_filename}'

    return resp


def legend(request, layername, layertitle=False, style=None):
    """Get the legend from a layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :param layertitle: Add the layer title in the legend. Default to False.
    :type layertitle: bool

    :param style: Layer style to choose
    :type style: str

    :return: The HTTPResponse with a PNG.
    """
    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

    # get default style name
    if not style:
        # generate style cache
        if not qgis_layer.default_style:
            try:
                style_list(layer, internal=False)
            except Exception:
                print("Failed to fetch styles")

            # refresh values
            qgis_layer.refresh_from_db()
        if qgis_layer.default_style:
            style = qgis_layer.default_style.name

    legend_path = QGIS_SERVER_CONFIG['legend_path']
    legend_filename = legend_path % (qgis_layer.qgis_layer_name, style)

    if not os.path.exists(legend_filename):
        if not os.path.exists(os.path.dirname(legend_filename)):
            os.makedirs(os.path.dirname(legend_filename))
        url = legend_url(layer, layertitle, style=style, internal=True)
        result = cache_request.apply_async((url, legend_filename))

        # Attempt to run task synchronously
        if not result.get():
            # If not succeded, provides error message.
            return HttpResponseServerError('Failed to fetch legend.')

    if image_format(legend_filename) != 'png':
        logger.error(f'{legend_filename} is not valid PNG.')
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


def tile(request, layername, z, x, y, style=None):
    """Get the tile from a layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :param z: TMS coordinate, zoom parameter
    :type z: int, str

    :param x: TMS coordinate, longitude parameter
    :type x: int, str

    :param y: TMS coordinate, latitude parameter
    :type y: int, str

    :param style: Layer style to choose
    :type style: str

    :return: The HTTPResponse with a PNG.
    """
    x = int(x)
    y = int(y)
    z = int(z)

    layer = get_object_or_404(Layer, name=layername)
    qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

    # get default style name
    if not style:
        # generate style cache
        if not qgis_layer.default_style:
            try:
                style_list(layer, internal=False)
            except Exception:
                print("Failed to fetch styles")

            # refresh values
            qgis_layer.refresh_from_db()
        if qgis_layer.default_style:
            style = qgis_layer.default_style.name

    tile_path = QGIS_SERVER_CONFIG['tile_path']
    tile_filename = tile_path % (qgis_layer.qgis_layer_name, style, z, x, y)

    if not os.path.exists(tile_filename):

        if not os.path.exists(os.path.dirname(tile_filename)):
            os.makedirs(os.path.dirname(tile_filename))
        # Use internal url
        url = tile_url(layer, z, x, y, style=style, internal=True)
        result = cache_request.apply_async((url, tile_filename))

        # Attempt to run task synchronously
        if not result.get():
            # If not succeded, provides error message.
            return HttpResponseServerError('Failed to fetch tile.')

    if image_format(tile_filename) != 'png':
        logger.error(f'{tile_filename} is not valid PNG.')
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
    raw = ensure_string(response.content)
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
        target_file = f"{qgis_layer.qgis_layer_path_prefix}.{ext}"
        if os.path.exists(target_file):
            filename = target_file
            break
    else:
        filename = None

    if not filename:
        msg = f'No Geotiff layer found for {layername}'
        logger.debug(msg)
        raise Http404(msg)

    with open(filename, 'rb') as f:
        return HttpResponse(f.read(), content_type='image/tiff')


def qgis_server_request(request):
    """View to forward OGC request to QGIS Server."""
    # Make a copy of the query string with capital letters for the key.
    query = request.GET or request.POST
    params = {param.upper(): value for param, value in query.items()}

    # 900913 is deprecated
    if params.get('SRS') == 'EPSG:900913':
        params['SRS'] = 'EPSG:3857'
    if params.get('CRS') == 'EPSG:900913':
        params['CRS'] = 'EPSG:3857'

    map_param = params.get('MAP')

    # As we have one QGIS project per layer, we don't support GetCapabilities
    # for now without any layer. We know, it's not OGC compliant.
    if params.get('REQUEST') == 'GetCapabilities':
        if (not map_param and
                not (params.get('LAYERS') or params.get('TYPENAME'))):
            return HttpResponse('GetCapabilities is not supported yet.')

    # As we have one project per layer, we add the MAP path if the request is
    # specific for one layer.
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
            layer_name = params.get('LAYER')
            if not layer_name:
                raise Http404('LAYER is not found for a GetLegendGraphic')
            layer = get_object_or_404(Layer, name=layer_name)
            return legend(request, layername=layer.name)

    # Validation for STYLEMANAGER service
    if params.get('SERVICE') == 'STYLEMANAGER':
        project_param = params.get('PROJECT')
        layer_name = params.get('LAYER')
        if not project_param and layer_name:
            layer = get_object_or_404(Layer, name=layer_name)
            qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)
            params['PROJECT'] = qgis_layer.qgis_project_path

    # if not shortcut, we forward any request to internal QGIS Server
    qgis_server_url = qgis_server_endpoint(internal=True)
    response = requests.get(qgis_server_url, params)

    content = ensure_string(response.content)

    # if it is GetCapabilities request, we need to replace all reference to
    # our proxy
    if params.get('REQUEST') == 'GetCapabilities':
        qgis_server_base_url = qgis_server_endpoint(internal=True)
        pattern = f'{qgis_server_base_url}'
        content = re.sub(
            pattern, qgis_server_endpoint(internal=False), content)

    return HttpResponse(
        content, content_type=response.headers.get('content-type'))


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
        "printURL": f"{print_url}",
        "createURL": f"{print_url}"
    }

    return HttpResponse(
        json.dumps(response_data), content_type="application/json")


def qgis_server_map_print(request):
    logger.debug('qgis_server_map_print')
    temp = []
    for key, value in request.POST.items():
        temp[key] = value
        print(f"{key}\n{value}\n--------")
    return HttpResponse(
        json.dumps(temp), content_type="application/json")


def qml_style(request, layername, style_name=None):
    """Update/Retrieve QML style of a given QGIS Layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :param style_name: The style name recognized by QGIS Server
    :type style_name: str
    """
    layer = get_object_or_404(Layer, name=layername)

    if request.method == 'GET':

        # Request QML from QGIS server
        if not style_name:
            # If no style name provided, then it is a List request
            styles_obj = None
            try:
                styles_obj = style_list(layer, internal=False)
            except Exception:
                print("Failed to fetch styles")

            styles_dict = []
            if styles_obj:
                styles_dict = [model_to_dict(s) for s in styles_obj]

                # If no style returned by GetCapabilities, this is a bug in QGIS
                # Attempt to generate default style name
                if not styles_dict:
                    style_url = style_get_url(layer, 'default')
                    response = requests.get(style_url)
                    if response.status_code == 200:
                        style_url = style_add_url(layer, 'default')
                        with open(layer.qgis_layer.qml_path, 'w') as f:
                            f.write(ensure_string(response.content))
                        response = requests.get(style_url)
                        if response.status_code == 200:
                            styles_obj = style_list(layer, internal=False)
                            styles_dict = [model_to_dict(s) for s in styles_obj]

            response = HttpResponse(
                json.dumps(styles_dict), content_type='application/json')
            return response

        # Return XML file of the style
        style_url = style_get_url(layer, style_name, internal=False)
        response = requests.get(style_url)
        if response.status_code == 200:
            response = HttpResponse(
                ensure_string(response.content), content_type='text/xml')
            response[
                'Content-Disposition'] = f'attachment; filename={style_name}.qml'
        else:
            response = HttpResponse(
                ensure_string(response.content), status=response.status_code)
        return response
    elif request.method == 'POST':

        # For people who uses API request
        if not request.user.has_perm(
                'change_resourcebase', layer.get_self_resource()):
            return HttpResponse(
                'User does not have permission to change QML style.',
                status=403)

        # Request about adding new QML style

        form = QGISLayerStyleUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            return TemplateResponse(
                request,
                'qgis_server/forms/qml_style.html',
                {
                    'resource': layer,
                    'style_upload_form': form
                },
                status=400).render()

        try:
            uploaded_qml = request.FILES['qml']

            # update qml in uploaded media folder
            # check upload session, is qml file exists?
            layerfile_set = layer.upload_session.layerfile_set
            try:
                qml_layer_file = layerfile_set.get(name='qml')
                # if it is exists, we need to delete it, because it won't be
                # managed by geonode
                qml_layer_file.delete()
            except LayerFile.DoesNotExist:
                pass

            # update qml in QGIS Layer folder
            content = uploaded_qml.read()
            qgis_layer = get_object_or_404(QGISServerLayer, layer=layer)

            with open(qgis_layer.qml_path, mode='w') as f:
                f.write(content)

            # construct URL to post new QML
            style_name = request.POST['name']
            style_title = request.POST['title']
            if not style_name:
                # Assign default name
                name_format = 'style_%Y%m%d%H%M%S'
                current_time = datetime.datetime.utcnow()
                style_name = current_time.strftime(name_format)

            # Add new style
            style_url = style_add_url(layer, style_name)

            response = requests.get(style_url)

            if not (response.status_code == 200 and ensure_string(response.content) == 'OK'):
                try:
                    style_list(layer, internal=False)
                except Exception:
                    print("Failed to fetch styles")

                return TemplateResponse(
                    request,
                    'qgis_server/forms/qml_style.html',
                    {
                        'resource': layer,
                        'style_upload_form': QGISLayerStyleUploadForm(),
                        'alert': True,
                        'alert_message': ensure_string(response.content),
                        'alert_class': 'alert-danger'
                    },
                    status=response.status_code).render()

            # We succeeded on adding new style

            # Refresh style models
            try:
                style_list(layer, internal=False)
                qgis_style = layer.qgis_layer.styles.get(name=style_name)
                qgis_style.title = style_title
                qgis_style.save()

                alert_message = f'Successfully add style {style_name}'
            except Exception:
                alert_message = 'Failed to fetch styles'

            return TemplateResponse(
                request,
                'qgis_server/forms/qml_style.html',
                {
                    'resource': layer,
                    'style_upload_form': form,
                    'alert': True,
                    'alert_class': 'alert-success',
                    'alert_message': alert_message
                },
                status=201).render()

        except Exception as e:
            logger.exception(e)
            return HttpResponseServerError()
    elif request.method == 'DELETE':
        # Request to delete particular QML Style

        if not style_name:
            # Style name should exists
            return HttpResponseBadRequest('Style name not provided.')

        # Handle removing tile-style cache
        try:
            style = layer.qgis_layer.styles.get(name=style_name)
            shutil.rmtree(style.style_tile_cache_path)
        except Exception:
            pass

        style_url = style_remove_url(layer, style_name)

        response = requests.get(style_url)

        if not (response.status_code == 200 and ensure_string(response.content) == 'OK'):
            alert_message = ensure_string(response.content)
            if 'NAME is NOT an existing style.' in ensure_string(response.content):
                alert_message = f'{style_name} is not an existing style'
            try:
                style_list(layer, internal=False)
            except Exception:
                print("Failed to fetch styles")

            return TemplateResponse(
                request,
                'qgis_server/forms/qml_style.html',
                {
                    'resource': layer,
                    'style_upload_form': QGISLayerStyleUploadForm(),
                    'alert': True,
                    'alert_message': alert_message,
                    'alert_class': 'alert-danger'
                },
                status=response.status_code).render()

        # Successfully removed styles
        # Handle when default style is deleted.
        # Will be handled by style_list method
        try:
            style_list(layer, internal=False)

            alert_message = f'Successfully deleted style {style_name}'
        except Exception:
            alert_message = 'Failed to fetch styles'

        return TemplateResponse(
            request,
            'qgis_server/forms/qml_style.html',
            {
                'resource': layer,
                'style_upload_form': QGISLayerStyleUploadForm(),
                'alert': True,
                'alert_message': alert_message,
                'alert_class': 'alert-success'
            },
            status=200).render()

    return HttpResponseBadRequest()


def default_qml_style(request, layername, style_name=None):
    """Set default style used by layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :param style_name: The style name recognized by QGIS Server
    :type style_name: str
    """
    layer = get_object_or_404(Layer, name=layername)

    if request.method == 'GET':
        # Handle querying default style name request
        default_style = layer.qgis_layer.default_style
        retval = {
            'name': default_style.name,
            'title': default_style.title,
            'style_url': default_style.style_url
        }
        return HttpResponse(
            json.dumps(retval), content_type='application/json')
    elif request.method == 'POST':
        # For people who uses API request
        if not request.user.has_perm(
                'change_resourcebase', layer.get_self_resource()):
            return HttpResponse(
                'User does not have permission to change QML style.',
                status=403)

        if not style_name:
            return HttpResponseBadRequest()

        style_url = style_set_default_url(layer, style_name)

        response = requests.get(style_url)

        if not (response.status_code == 200 and ensure_string(response.content) == 'OK'):
            return HttpResponseServerError(
                'Failed to change default Style.'
                'Error: {0}'.format(ensure_string(response.content)))

        # Succesfully change default style
        # Synchronize models
        style = layer.qgis_layer.styles.get(name=style_name)
        qgis_layer = layer.qgis_layer
        qgis_layer.default_style = style
        qgis_layer.save()

        alert_message = f'Successfully changed default style {style_name}'

        return TemplateResponse(
            request,
            'qgis_server/forms/qml_style.html',
            {
                'resource': layer,
                'style_upload_form': QGISLayerStyleUploadForm(),
                'alert': True,
                'alert_message': alert_message,
                'alert_class': 'alert-success'
            },
            status=200).render()


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
            status=403)

    # extract bbox
    bbox_string = request.POST['bbox']
    # BBox should be in the format: [xmin,ymin,xmax,ymax], EPSG:4326
    # coming from leafletjs
    bbox = bbox_string.split(',')
    bbox = [float(s) for s in bbox]

    # Give thumbnail creation to celery tasks, and exit.
    create_qgis_server_thumbnail.apply_async(
        ('layers.layer', layer.id, True, bbox))
    retval = {
        'success': True
    }
    return HttpResponse(
        json.dumps(retval), content_type="application/json")


def download_qlr(request, layername):
    """Download QLR file for a layer.

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :return: QLR file.
    """
    layer = get_object_or_404(Layer, name=layername)
    url = qlr_url(layer, internal=True)

    # use layer.name if layer.title is empty.
    if layer.title:
        layer_title = layer.title
    else:
        layer_title = layer.name

    result = requests.get(url)
    response = HttpResponse(
        result.content,
        content_type="application/x-qgis-layer-definition",
        status=result.status_code)
    response['Content-Disposition'] = \
        f'attachment; filename={layer_title}.qlr'

    return response
