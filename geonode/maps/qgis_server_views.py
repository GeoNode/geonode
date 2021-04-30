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
import json
import requests
import math
import logging

from django.conf import settings
from django.views.generic import CreateView, DetailView, UpdateView
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.shortcuts import render
from django.http import HttpResponse

from geonode.maps.views import _PERMISSION_MSG_VIEW, _resolve_map, _resolve_layer
from geonode.maps.models import Map, MapLayer
from geonode.layers.models import Layer

from geonode.utils import default_map_config, forward_mercator, \
    llbbox_to_mercator, check_ogc_backend
from geonode import geoserver, qgis_server

from urllib.parse import urlsplit

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    # FIXME: The post service providing the map_status object
    # should be moved to geonode.geoserver.
    from geonode.geoserver.helpers import ogc_server_settings

elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    from geonode.qgis_server.helpers import ogc_server_settings
    from geonode.qgis_server.tasks.update import create_qgis_server_thumbnail

logger = logging.getLogger("geonode.maps.qgis_server_views")


class MapCreateView(CreateView):
    model = Map
    fields = '__all__'
    template_name = 'leaflet/maps/map_view.html'
    context_object_name = 'map'

    def get_context_data(self, **kwargs):
        request = self.request
        if request and 'access_token' in request.session:
            access_token = request.session['access_token']
        else:
            access_token = None

        DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)

        layers = Layer.objects.all()

        if request.method == 'GET' and 'copy' in request.GET:
            """Prepare context data."""
            request = self.request
            mapid = self.request.GET['copy']

            map_obj = _resolve_map(
                request, mapid, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

            config = map_obj.viewer_json(request)

            # list all required layers
            map_layers = MapLayer.objects.filter(
                map_id=mapid).order_by('stack_order')
            context = {
                'config': json.dumps(config),
                'create': False,
                'layers': layers,
                'map': map_obj,
                'map_layers': map_layers,
                'preview': getattr(
                    settings,
                    'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
                    'leaflet')
            }
            return context
        else:
            if request.method == 'GET':
                params = request.GET
            elif request.method == 'POST':
                params = request.POST
            else:
                return self.render_to_response(status=405)

            if 'layer' in params:
                bbox = None
                map_obj = Map(projection=getattr(
                    settings, 'DEFAULT_MAP_CRS', 'EPSG:3857'))

                for layer_name in params.getlist('layer'):
                    try:
                        layer = _resolve_layer(request, layer_name)
                    except ObjectDoesNotExist:
                        # bad layer, skip
                        continue

                    if not request.user.has_perm(
                            'view_resourcebase',
                            obj=layer.get_self_resource()):
                        # invisible layer, skip inclusion
                        continue

                    layer_bbox = layer.bbox
                    # assert False, str(layer_bbox)
                    if bbox is None:
                        bbox = list(layer_bbox[0:4])
                    else:
                        bbox[0] = min(bbox[0], layer_bbox[0])
                        bbox[1] = min(bbox[1], layer_bbox[1])
                        bbox[2] = max(bbox[2], layer_bbox[2])
                        bbox[3] = max(bbox[3], layer_bbox[3])

                    config = layer.attribute_config()

                    # Add required parameters for GXP lazy-loading
                    config["title"] = layer.title
                    config["queryable"] = True

                    config["srs"] = getattr(settings,
                                            'DEFAULT_MAP_CRS', 'EPSG:3857')
                    config["bbox"] = bbox if config["srs"] != 'EPSG:3857' \
                        else llbbox_to_mercator(
                        [float(coord) for coord in bbox])

                    if layer.storeType == "remoteStore":
                        service = layer.remote_service
                        # Probably not a good idea to send the access token to every remote service.
                        # This should never match, so no access token should be sent to remote services.
                        ogc_server_url = urlsplit(
                            ogc_server_settings.PUBLIC_LOCATION).netloc
                        service_url = urlsplit(
                            service.base_url).netloc

                        if access_token and ogc_server_url == service_url and \
                                'access_token' not in service.base_url:
                            url = f'{service.base_url}?access_token={access_token}'
                        else:
                            url = service.base_url
                        map_layers = MapLayer(map=map_obj,
                                              name=layer.typename,
                                              ows_url=layer.ows_url,
                                              layer_params=json.dumps(config),
                                              visibility=True,
                                              source_params=json.dumps({
                                                  "ptype": service.ptype,
                                                  "remote": True,
                                                  "url": url,
                                                  "name": service.name,
                                                  "title": f"[R] {service.title}"}))
                    else:
                        ogc_server_url = urlsplit(
                            ogc_server_settings.PUBLIC_LOCATION).netloc
                        layer_url = urlsplit(layer.ows_url).netloc

                        if access_token and ogc_server_url == layer_url and \
                                'access_token' not in layer.ows_url:
                            url = f"{layer.ows_url}?access_token={access_token}"
                        else:
                            url = layer.ows_url
                        map_layers = MapLayer(
                            map=map_obj,
                            name=layer.typename,
                            ows_url=url,
                            # use DjangoJSONEncoder to handle Decimal values
                            layer_params=json.dumps(
                                config,
                                cls=DjangoJSONEncoder),
                            visibility=True
                        )

                if bbox and len(bbox) >= 4:
                    minx, miny, maxx, maxy = [float(coord) for coord in bbox]
                    x = (minx + maxx) / 2
                    y = (miny + maxy) / 2

                    if getattr(settings,
                               'DEFAULT_MAP_CRS', 'EPSG:3857') == "EPSG:4326":
                        center = list((x, y))
                    else:
                        center = list(forward_mercator((x, y)))

                    if center[1] == float('-inf'):
                        center[1] = 0

                    BBOX_DIFFERENCE_THRESHOLD = 1e-5

                    # Check if the bbox is invalid
                    valid_x = (maxx - minx) ** 2 > BBOX_DIFFERENCE_THRESHOLD
                    valid_y = (maxy - miny) ** 2 > BBOX_DIFFERENCE_THRESHOLD

                    if valid_x:
                        width_zoom = math.log(360 / abs(maxx - minx), 2)
                    else:
                        width_zoom = 15

                    if valid_y:
                        height_zoom = math.log(360 / abs(maxy - miny), 2)
                    else:
                        height_zoom = 15

                    map_obj.center_x = center[0]
                    map_obj.center_y = center[1]
                    map_obj.zoom = math.ceil(min(width_zoom, height_zoom))

                map_obj.handle_moderated_uploads()

                config = map_obj.viewer_json(request)
                config['fromLayer'] = True
                context = {
                    'config': json.dumps(config),
                    'create': True,
                    'layers': layers,
                    'map': map_obj,
                    'map_layers': map_layers,
                    'preview': getattr(
                        settings,
                        'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
                        'leaflet')
                }

            else:
                # list all required layers
                layers = Layer.objects.all()
                context = {
                    'create': True,
                    'layers': layers
                }
            return context

    def get_success_url(self):
        pass

    def get_form_kwargs(self):
        kwargs = super(MapCreateView, self).get_form_kwargs()
        return kwargs


class MapDetailView(DetailView):
    model = Map
    template_name = 'leaflet/maps/map_view.html'
    context_object_name = 'map'

    def get_context_data(self, **kwargs):
        """Prepare context data."""

        mapid = self.kwargs.get('mapid')
        request = self.request

        map_obj = _resolve_map(
            request, mapid, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

        config = map_obj.viewer_json(request)
        # list all required layers
        layers = Layer.objects.all()
        map_layers = MapLayer.objects.filter(
            map_id=mapid).order_by('stack_order')
        context = {
            'config': json.dumps(config),
            'create': False,
            'layers': layers,
            'map': map_obj,
            'map_layers': map_layers,
            'preview': getattr(
                settings,
                'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
                'leaflet')
        }
        return context

    def get_object(self):
        return Map.objects.get(id=self.kwargs.get("mapid"))


class MapEmbedView(DetailView):
    model = Map
    template_name = 'leaflet/maps/map_detail.html'
    context_object_name = 'map'

    def get_context_data(self, **kwargs):
        """Prepare context data."""

        mapid = self.kwargs.get('mapid')
        request = self.request

        map_obj = _resolve_map(
            request, mapid, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

        config = map_obj.viewer_json(request)
        # list all required layers
        map_layers = MapLayer.objects.filter(
            map_id=mapid).order_by('stack_order')
        context = {
            'config': json.dumps(config),
            'create': False,
            'resource': map_obj,
            'layers': map_layers,
            'preview': getattr(
                settings,
                'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
                'leaflet')
        }
        return context

    def get_object(self):
        return Map.objects.get(id=self.kwargs.get("mapid"))

    @method_decorator(xframe_options_exempt)
    def dispatch(self, *args, **kwargs):
        return super(MapEmbedView, self).dispatch(*args, **kwargs)


class MapEditView(UpdateView):
    model = Map
    fields = '__all__'
    template_name = 'leaflet/maps/map_edit.html'
    context_object_name = 'map'

    def get_context_data(self, **kwargs):
        # list all required layers
        mapid = self.kwargs.get('mapid')
        request = self.request
        map_obj = _resolve_map(request,
                               mapid,
                               'base.view_resourcebase',
                               _PERMISSION_MSG_VIEW)

        config = map_obj.viewer_json(request)
        layers = Layer.objects.all()
        map_layers = MapLayer.objects.filter(
            map_id=mapid).order_by('stack_order')

        context = {
            'create': False,
            'config': json.dumps(config),
            'layers': layers,
            'map_layers': map_layers,
            'map': map_obj,
            'preview': getattr(
                settings,
                'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
                'leaflet')
        }
        return context

    def get(self, request, **kwargs):
        self.object = Map.objects.get(
            id=self.kwargs.get('mapid'))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(
            object=self.object, form=form)
        return self.render_to_response(context)

    def get_success_url(self):
        pass

    def get_form_kwargs(self):
        kwargs = super(MapEditView, self).get_form_kwargs()
        return kwargs


class MapUpdateView(UpdateView):
    model = Map
    fields = '__all__'
    template_name = 'leaflet/maps/map_edit.html'
    context_object_name = 'map'

    def get_context_data(self, **kwargs):
        mapid = self.kwargs.get('mapid')
        request = self.request
        map_obj = _resolve_map(request,
                               mapid,
                               'base.view_resourcebase',
                               _PERMISSION_MSG_VIEW)

        if request.method == 'POST':
            if not request.user.is_authenticated:
                return self.render_to_response(
                    'You must be logged in to save new maps',
                    content_type="text/plain",
                    status=401
                )
            map_obj.overwrite = True
            map_obj.save()
            map_obj.set_default_permissions()
            map_obj.handle_moderated_uploads()
            # If the body has been read already, use an empty string.
            # See https://github.com/django/django/commit/58d555caf527d6f1bdfeab14527484e4cca68648
            # for a better exception to catch when we move to Django 1.7.
            try:
                body = request.body
            except Exception:
                body = ''

            try:
                # Call the base implementation first to get a context
                context = super(MapUpdateView, self).get_context_data(**kwargs)
                map_obj.update_from_viewer(body, context=context)
            except ValueError as e:
                return self.render_to_response(str(e), status=400)
            else:
                context = {
                    'create': False,
                    'status': 200,
                    'map': map_obj,
                    'content_type': 'application/json'
                }
                return context
        else:
            return self.render_to_response(status=405)

    def get(self, request, **kwargs):
        self.object = Map.objects.get(
            id=self.kwargs.get('mapid'))
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        context = self.get_context_data(object=self.object,
                                        form=form)
        return self.render_to_response(context)

    def get_object(self, queryset=None):
        obj = Map.objects.get(
            id=self.kwargs.get('mapid'))
        return obj


def map_download_qlr(request, mapid):
    """Download QLR file to open the maps' layer in QGIS desktop.

    :param request: The request from the frontend.
    :type request: HttpRequest

    :param mapid: The id of the map.
    :type mapid: String

    :return: QLR file.
    """

    map_obj = _resolve_map(request,
                           mapid,
                           'base.view_resourcebase',
                           _PERMISSION_MSG_VIEW)

    def perm_filter(layer):
        return request.user.has_perm(
            'base.view_resourcebase',
            obj=layer.get_self_resource())

    mapJson = map_obj.json(perm_filter)

    # we need to remove duplicate layers
    j_map = json.loads(mapJson)
    j_layers = j_map["layers"]
    for j_layer in j_layers:
        if j_layer["service"] is None:
            j_layers.remove(j_layer)
            continue
        if (len([_l for _l in j_layers if _l == j_layer])) > 1:
            j_layers.remove(j_layer)

    map_layers = []
    for layer in j_layers:
        layer_name = layer["name"].split(":")[1]
        ogc_url = reverse('qgis_server:layer-request',
                          kwargs={'layername': layer_name})
        url = settings.SITEURL + ogc_url.replace("/", "", 1)

        map_layers.append({
            'type': 'raster',
            'display': layer_name,
            'driver': 'wms',
            'crs': 'EPSG:4326',
            'format': 'image/png',
            'styles': '',
            'layers': layer_name,
            'url': url
        })

    json_layers = json.dumps(map_layers)
    url_server = f"{settings.QGIS_SERVER_URL}?SERVICE=LAYERDEFINITIONS&LAYERS={json_layers}"
    fwd_request = requests.get(url_server)
    response = HttpResponse(
        fwd_request.content,
        content_type="application/x-qgis-layer-definition",
        status=fwd_request.status_code)
    response['Content-Disposition'] = f'attachment; filename={map_obj.title}.qlr'

    return response


def map_download_leaflet(request, mapid,
                         template='leaflet/maps/map_embed.html'):
    """Download leaflet map as static HTML.

    :param request: The request from the frontend.
    :type request: HttpRequest

    :param mapid: The id of the map.
    :type mapid: String

    :return: HTML file.
    """

    map_obj = _resolve_map(request,
                           mapid,
                           'base.view_resourcebase',
                           _PERMISSION_MSG_VIEW)
    map_layers = MapLayer.objects.filter(
        map_id=mapid).order_by('stack_order')
    layers = []
    for layer in map_layers:
        if layer.group != 'background':
            layers.append(layer)

    context = {
        'resource': map_obj,
        'map_layers': layers,
        'for_download': True
    }

    the_page = render(request, template, context=context)

    response = HttpResponse(
        the_page.content, content_type="html",
        status=the_page.status_code)
    response['Content-Disposition'] = f'attachment; filename={map_obj.title}.html'

    return response


def set_thumbnail_map(request, mapid):
    """Update thumbnail based on map extent

    :param layername: The layer name in Geonode.
    :type layername: basestring

    :return success: true if success, None if fail.
    :type success: bool
    """
    if request.method != 'POST':
        return HttpResponse('Bad Request')

    map_layers = MapLayer.objects.filter(map__id=mapid)
    local_layers = [_l for _l in map_layers if _l.local]

    layers = {}
    for layer in local_layers:
        try:
            _l = Layer.objects.get(typename=layer.name)
            layers[_l.name] = _l
        except Layer.DoesNotExist:
            msg = f'No Layer found for typename: {layer.name}'
            logger.debug(msg)

    if not layers:
        # The signal is called too early, or the map has no layer yet.
        return

    bbox = _get_bbox_from_layers(layers)

    # Give thumbnail creation to celery tasks, and exit.
    create_qgis_server_thumbnail.apply_async(
        ('maps.map', mapid, True, bbox))
    retval = {
        'success': True
    }
    return HttpResponse(
        json.dumps(retval), content_type="application/json")


def _get_bbox_from_layers(layers):
    """
    Calculate the bbox from a given list of Layer objects
    """
    bbox = None
    for layer in layers:
        layer_bbox = layers[layer].bbox_string.split(',')
        if bbox is None:
            bbox = [float(key) for key in layer_bbox]
        else:
            bbox[0] = float(min(bbox[0], layer_bbox[0]))
            bbox[1] = float(min(bbox[1], layer_bbox[1]))
            bbox[2] = float(max(bbox[2], layer_bbox[2]))
            bbox[3] = float(max(bbox[3], layer_bbox[3]))

    return bbox
