# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

import math
import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.utils.html import strip_tags
from django.views.decorators.http import require_POST

from geonode.layers.models import Layer
from geonode.layers.views import _resolve_layer
from geonode.maps.models import Map, MapLayer
from geonode.utils import forward_mercator, llbbox_to_mercator
from geonode.utils import DEFAULT_TITLE
from geonode.utils import DEFAULT_ABSTRACT
from geonode.utils import default_map_config
from geonode.utils import resolve_object
from geonode.utils import http_client
from geonode.maps.forms import MapForm
from geonode.security.views import _perms_info_json
from geonode.base.forms import CategoryForm
from geonode.base.models import TopicCategory

from geonode.documents.models import get_related_documents
from geonode.base.models import ContactRole
from geonode.people.forms import ProfileForm, PocForm

if 'geonode.geoserver' in settings.INSTALLED_APPS:
    #FIXME: The post service providing the map_status object
    # should be moved to geonode.geoserver.
    from geonode.geoserver.helpers import ogc_server_settings
 

logger = logging.getLogger("geonode.maps.views")

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10
MAX_MAPS_SEARCH_BATCH_SIZE = 25

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this map.")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this map.')
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this map")
_PERMISSION_MSG_METADATA = _("You are not allowed to modify this map's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this map.")


def _handleThumbNail(req, obj):
    # object will either be a map or a layer, one or the other permission must apply
    if not req.user.has_perm('change_resourcebase', obj=obj.get_self_resource()):
        return HttpResponse(loader.render_to_string('401.html',
            RequestContext(req, {'error_message':
                _("You are not permitted to modify this object")})), status=401)
    if req.method == 'GET':
        return HttpResponseRedirect(obj.get_thumbnail_url())
    elif req.method == 'POST':
        try:
            obj.save_thumbnail(req.body)
            return HttpResponseRedirect(obj.get_thumbnail_url())
        except:
            return HttpResponse(
                content='error saving thumbnail',
                status=500,
                mimetype='text/plain'
            )

def _resolve_map(request, id, permission='base.change_resourcebase',
                 msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the Map by the provided typename and check the optional permission.
    '''
    return resolve_object(request, Map, {'pk':id}, permission = permission,
                          permission_msg=msg, **kwargs)

#### BASIC MAP VIEWS ####

def map_detail(request, mapid, template='maps/map_detail.html'):
    '''
    The view that show details of each map
    '''
    map_obj = _resolve_map(request, mapid, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

    map_obj.popular_count += 1
    map_obj.save()

    config = map_obj.viewer_json()
    config = json.dumps(config)
    layers = MapLayer.objects.filter(map=map_obj.id)
    return render_to_response(template, RequestContext(request, {
        'config': config,
        'resource': map_obj,
        'layers': layers,
        'permissions_json': _perms_info_json(map_obj),
        "documents": get_related_documents(map_obj),
    }))

@login_required
def map_metadata(request, mapid, template='maps/map_metadata.html'):
    
    map_obj = _resolve_map(request, mapid, msg=_PERMISSION_MSG_METADATA)

    poc = map_obj.poc

    metadata_author = map_obj.metadata_author

    topic_category = map_obj.category

    if request.method == "POST":
        map_form = MapForm(request.POST, instance=map_obj, prefix="resource")
        category_form = CategoryForm(request.POST,prefix="category_choice_field",
             initial=int(request.POST["category_choice_field"]) if "category_choice_field" in request.POST else None)        
    else:
        map_form = MapForm(instance=map_obj, prefix="resource")
        category_form = CategoryForm(prefix="category_choice_field", initial=topic_category.id if topic_category else None)

    if request.method == "POST" and map_form.is_valid() and category_form.is_valid():
        new_poc = map_form.cleaned_data['poc']
        new_author = map_form.cleaned_data['metadata_author']
        new_keywords = map_form.cleaned_data['keywords']
        new_title = strip_tags(map_form.cleaned_data['title'])
        new_abstract = strip_tags(map_form.cleaned_data['abstract'])
        new_category = TopicCategory.objects.get(id=category_form.cleaned_data['category_choice_field'])

        if new_poc is None:
            if poc.user is None:
                poc_form = ProfileForm(request.POST, prefix="poc", instance=poc)
            else:
                poc_form = ProfileForm(request.POST, prefix="poc")
            if poc_form.has_changed and poc_form.is_valid():
                new_poc = poc_form.save()

        if new_author is None:
            if metadata_author.user is None:
                author_form = ProfileForm(request.POST, prefix="author", 
                    instance=metadata_author)
            else:
                author_form = ProfileForm(request.POST, prefix="author")
            if author_form.has_changed and author_form.is_valid():
                new_author = author_form.save()

        if new_poc is not None and new_author is not None:
            the_map = map_form.save()
            the_map.poc = new_poc
            the_map.metadata_author = new_author
            the_map.title = new_title
            the_map.abstract = new_abstract
            the_map.save()
            the_map.keywords.clear()
            the_map.keywords.add(*new_keywords)
            the_map.category = new_category
            the_map.save()
            return HttpResponseRedirect(reverse('map_detail', args=(map_obj.id,)))

    if poc is None:
        poc_form = ProfileForm(request.POST, prefix="poc")
    else:
        if poc.user is None:
            poc_form = ProfileForm(instance=poc, prefix="poc")
        else:
            map_form.fields['poc'].initial = poc.id
            poc_form = ProfileForm(prefix="poc")
            poc_form.hidden=True

    if metadata_author is None:
            author_form = ProfileForm(request.POST, prefix="author")
    else:
        if metadata_author.user is None:
            author_form = ProfileForm(instance=metadata_author, prefix="author")
        else:
            map_form.fields['metadata_author'].initial = metadata_author.id
            author_form = ProfileForm(prefix="author")
            author_form.hidden=True

    return render_to_response(template, RequestContext(request, {
        "map": map_obj,
        "map_form": map_form,
        "poc_form": poc_form,
        "author_form": author_form,
        "category_form": category_form,
    }))

@login_required
def map_remove(request, mapid, template='maps/map_remove.html'):
    ''' Delete a map, and its constituent layers. '''
    try:
        map_obj = _resolve_map(request, mapid, 'base.delete_resourcebase',
                               _PERMISSION_MSG_DELETE, permission_required=True)

        if request.method == 'GET':
            return render_to_response(template, RequestContext(request, {
                "map": map_obj
            }))

        elif request.method == 'POST':
            layers = map_obj.layer_set.all()
            for layer in layers:
                layer.delete()
            map_obj.delete()

            return HttpResponseRedirect(reverse("maps_browse"))

    except PermissionDenied:
            return HttpResponse(
                   'You are not allowed to delete this map',
                   mimetype="text/plain",
                   status=401
            )

def map_embed(request, mapid=None, template='maps/map_embed.html'):
    if mapid is None:
        config = default_map_config()[0]
    else:
        map_obj = _resolve_map(request, mapid, 'base.view_resourcebase')
        config = map_obj.viewer_json()
    return render_to_response(template, RequestContext(request, {
        'config': json.dumps(config)
    }))


#### MAPS VIEWER ####


def map_view(request, mapid, template='maps/map_view.html'):
    """
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    map_obj = _resolve_map(request, mapid, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

    config = map_obj.viewer_json()
    return render_to_response(template, RequestContext(request, {
        'config': json.dumps(config),
        'map': map_obj
    }))


def map_view_js(request, mapid):
    map_obj = _resolve_map(request, mapid, 'view_resourcebase')
    config = map_obj.viewer_json()
    return HttpResponse(json.dumps(config), mimetype="application/javascript")

def map_json(request, mapid):
    if request.method == 'GET':
        map_obj = _resolve_map(request, mapid, 'view_resourcebase')
        return HttpResponse(json.dumps(map_obj.viewer_json()))
    elif request.method == 'PUT':
        if not request.user.is_authenticated():
            return HttpResponse(
                _PERMISSION_MSG_LOGIN,
                status=401,
                mimetype="text/plain"
            )
        map_obj = _resolve_map(request, mapid, 'change_resourcebase')
        try:
            map_obj.update_from_viewer(request.body)
            return HttpResponse(json.dumps(map_obj.viewer_json()))
        except ValueError, e:
            return HttpResponse(
                "The server could not understand the request." + str(e),
                mimetype="text/plain",
                status=400
            )

#### NEW MAPS ####

def new_map(request, template='maps/map_view.html'):
    config = new_map_config(request)
    if isinstance(config, HttpResponse):
        return config
    else:
        return render_to_response(template, RequestContext(request, {
            'config': config,
        }))


def new_map_json(request):
    if request.method == 'GET':
        config = new_map_config(request)
        if isinstance(config, HttpResponse):
            return config
        else:
            return HttpResponse(config)

    elif request.method == 'POST':
        if not request.user.is_authenticated():
            return HttpResponse(
                   'You must be logged in to save new maps',
                   mimetype="text/plain",
                   status=401
            )

        map_obj = Map(owner=request.user, zoom=0,
                      center_x=0, center_y=0)
        map_obj.save()
        map_obj.set_default_permissions()
        try:
            map_obj.update_from_viewer(request.body)
        except ValueError, e:
            return HttpResponse(str(e), status=400)
        else:
            return HttpResponse(
                json.dumps({'id':map_obj.id }),
                status=200,
                mimetype='application/json'
            )
    else:
        return HttpResponse(status=405)

def new_map_config(request):
    '''
    View that creates a new map.

    If the query argument 'copy' is given, the initial map is
    a copy of the map with the id specified, otherwise the
    default map configuration is used.  If copy is specified
    and the map specified does not exist a 404 is returned.
    '''
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()

    if request.method == 'GET' and 'copy' in request.GET:
        mapid = request.GET['copy']
        map_obj = _resolve_map(request, mapid, 'base.view_resourcebase')

        map_obj.abstract = DEFAULT_ABSTRACT
        map_obj.title = DEFAULT_TITLE
        if request.user.is_authenticated(): map_obj.owner = request.user
        config = map_obj.viewer_json()
        del config['id']
    else:
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        else:
            return HttpResponse(status=405)

        if 'layer' in params:
            bbox = None
            map_obj = Map(projection="EPSG:900913")
            layers = []
            for layer_name in params.getlist('layer'):
                try:
                    layer = _resolve_layer(request, layer_name)
                except ObjectDoesNotExist:
                    # bad layer, skip
                    continue

                if not request.user.has_perm('view_resourcebase', obj=layer.get_self_resource()):
                    # invisible layer, skip inclusion
                    continue

                layer_bbox = layer.bbox
                # assert False, str(layer_bbox)
                if bbox is None:
                    bbox = list(layer_bbox[0:4])
                else:
                    bbox[0] = min(bbox[0], layer_bbox[0])
                    bbox[1] = max(bbox[1], layer_bbox[1])
                    bbox[2] = min(bbox[2], layer_bbox[2])
                    bbox[3] = max(bbox[3], layer_bbox[3])

                config = layer.attribute_config()

                #Add required parameters for GXP lazy-loading
                config["srs"] = layer.srid
                config["title"] = layer.title
                config["bbox"] =  [float(coord) for coord in bbox] \
                    if layer.srid == "EPSG:4326" else llbbox_to_mercator([float(coord) for coord in bbox])

                if layer.storeType == "remoteStore":
                    service = layer.service
                    maplayer = MapLayer(map = map_obj,
                                        name = layer.typename,
                                        ows_url = layer.ows_url,
                                        layer_params=json.dumps( config),
                                        visibility=True,
                                        source_params=json.dumps({
                                            "ptype":service.ptype,
                                            "remote": True,
                                            "url": service.base_url,
                                            "name": service.name}))
                else:
                    maplayer = MapLayer(
                    map = map_obj,
                    name = layer.typename,
                    ows_url = layer.ows_url,
                    layer_params=json.dumps(config),
                    visibility = True
                )

                layers.append(maplayer)

            if bbox is not None:
                minx, miny, maxx, maxy = [float(c) for c in bbox]
                x = (minx + maxx) / 2
                y = (miny + maxy) / 2

                center = list(forward_mercator((x, y)))
                if center[1] == float('-inf'):
                    center[1] = 0

                BBOX_DIFFERENCE_THRESHOLD = 1e-5

                #Check if the bbox is invalid
                valid_x = (maxx - minx)**2 > BBOX_DIFFERENCE_THRESHOLD
                valid_y = (maxy - miny)**2 > BBOX_DIFFERENCE_THRESHOLD

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


            config = map_obj.viewer_json(*(DEFAULT_BASE_LAYERS + layers))
            config['fromLayer'] = True
        else:
            config = DEFAULT_MAP_CONFIG
    return json.dumps(config)


#### MAPS DOWNLOAD ####

def map_download(request, mapid, template='maps/map_download.html'):
    """
    Download all the layers of a map as a batch
    XXX To do, remove layer status once progress id done
    This should be fix because
    """
    mapObject = _resolve_map(request, mapid, 'base.view_resourcebase')

    map_status = dict()
    if request.method == 'POST':
        url = "%srest/process/batchDownload/launch/" % ogc_server_settings.LOCATION

        def perm_filter(layer):
            return request.user.has_perm('base.view_resourcebase', obj=layer.get_self_resource())

        mapJson = mapObject.json(perm_filter)

        # we need to remove duplicate layers
        j_map = json.loads(mapJson)
        j_layers = j_map["layers"]
        for j_layer in j_layers:
            if(len([l for l in j_layers if l == j_layer]))>1:
                j_layers.remove(j_layer)
        mapJson = json.dumps(j_map)

        resp, content = http_client.request(url, 'POST', body=mapJson)

        status = int(resp.status)

        if status == 200:
            map_status = json.loads(content)
            request.session["map_status"] = map_status
        else:
            raise Exception('Could not start the download of %s. Error was: %s' % (mapObject.title, content))

    locked_layers = []
    remote_layers = []
    downloadable_layers = []

    for lyr in mapObject.layer_set.all():
        if lyr.group != "background":
            if not lyr.local:
                remote_layers.append(lyr)
            else:
                ownable_layer = Layer.objects.get(typename=lyr.name)
                if not request.user.has_perm('view_resourcebase', obj=ownable_layer.get_self_resource()):
                    locked_layers.append(lyr)
                else:
                    # we need to add the layer only once
                    if len([l for l in downloadable_layers if l.name == lyr.name]) == 0:
                        downloadable_layers.append(lyr)

    return render_to_response(template, RequestContext(request, {
         "map_status" : map_status,
         "map" : mapObject,
         "locked_layers": locked_layers,
         "remote_layers": remote_layers,
         "downloadable_layers": downloadable_layers,
         "site" : settings.SITEURL
    }))


def map_download_check(request):
    """
    this is an endpoint for monitoring map downloads
    """
    try:
        layer = request.session["map_status"]
        if type(layer) == dict:
            url = "%srest/process/batchDownload/status/%s" % (ogc_server_settings.LOCATION,layer["id"])
            resp,content = http_client.request(url,'GET')
            status= resp.status
            if resp.status == 400:
                return HttpResponse(content="Something went wrong",status=status)
        else:
            content = "Something Went wrong"
            status  = 400
    except ValueError:
        # TODO: Is there any useful context we could include in this log?
        logger.warn("User tried to check status, but has no download in progress.")
    return HttpResponse(content=content,status=status)

def map_wmc(request, mapid, template="maps/wmc.xml"):
    """Serialize an OGC Web Map Context Document (WMC) 1.1"""

    mapObject = _resolve_map(request, mapid, 'base.view_resourcebase')

    return render_to_response(template, RequestContext(request, {
        'map': mapObject,
        'siteurl': settings.SITEURL,
    }), mimetype='text/xml')

def map_wms(request, mapid):
    """
    Publish local map layers as group layer in local OWS.

    /maps/:id/wms

    GET: return endpoint information for group layer,
    PUT: update existing or create new group layer.
    """
    mapObject = _resolve_map(request, mapid, 'base.view_resourcebase')

    if request.method == 'PUT':
        try:
            layerGroupName = mapObject.publish_layer_group()
            response = dict(
                layerGroupName=layerGroupName,
                ows=getattr(ogc_server_settings, 'ows', ''),
            )
            return HttpResponse(json.dumps(response), mimetype="application/json")
        except FailedRequestError:
            return HttpResponseServerError()
        
    if request.method == 'GET':
        response = dict(
            layerGroupName=getattr(mapObject.layer_group, 'name', ''),
            ows=getattr(ogc_server_settings, 'ows', ''),
        )
        return HttpResponse(json.dumps(response), mimetype="application/json")

    return HttpResponseNotAllowed(['PUT', 'GET'])


def map_thumbnail(request, mapid):
    return _handleThumbNail(request, _resolve_map(request, mapid))

def maplayer_attributes(request, layername):
    #Return custom layer attribute labels/order in JSON format
    layer = Layer.objects.get(typename=layername)
    return HttpResponse(json.dumps(layer.attribute_config()), mimetype="application/json")
