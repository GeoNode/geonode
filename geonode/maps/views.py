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
import unicodedata
import logging

from urllib import urlencode

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from django.views.generic.list import ListView
from django.db.models import Q
from django.views.decorators.http import require_POST

from geonode.utils import _split_query, http_client
from geonode.layers.models import Layer, TopicCategory
from geonode.maps.models import Map, MapLayer
from geonode.utils import forward_mercator
from geonode.utils import DEFAULT_TITLE
from geonode.utils import DEFAULT_ABSTRACT
from geonode.utils import default_map_config
from geonode.utils import resolve_object
from geonode.maps.forms import MapForm
from geonode.people.models import Profile
from geonode.security.models import AUTHENTICATED_USERS, ANONYMOUS_USERS
from geonode.security.views import _perms_info

logger = logging.getLogger("geonode.maps.views")

_user, _password = settings.GEOSERVER_CREDENTIALS

DEFAULT_MAPS_SEARCH_BATCH_SIZE = 10
MAX_MAPS_SEARCH_BATCH_SIZE = 25

MAP_LEV_NAMES = {
    Map.LEVEL_NONE  : _('No Permissions'),
    Map.LEVEL_READ  : _('Read Only'),
    Map.LEVEL_WRITE : _('Read/Write'),
    Map.LEVEL_ADMIN : _('Administrative')
}

_PERMISSION_MSG_DELETE = _("You are not permitted to delete this map.")
_PERMISSION_MSG_GENERIC = _('You do not have permissions for this map.')
_PERMISSION_MSG_LOGIN = _("You must be logged in to save this map")
_PERMISSION_MSG_METADATA = _("You are not allowed to modify this map's metadata.")
_PERMISSION_MSG_VIEW = _("You are not allowed to view this map.")


def _resolve_map(request, id, permission='maps.change_map',
                 msg=_PERMISSION_MSG_GENERIC, **kwargs):
    '''
    Resolve the Map by the provided typename and check the optional permission.
    '''
    return resolve_object(request, Map, {'pk':id}, permission = permission,
                          permission_msg=msg, **kwargs)


def bbox_to_wkt(x0, x1, y0, y1, srid="4326"):
    return 'SRID='+srid+';POLYGON(('+x0+' '+y0+','+x0+' '+y1+','+x1+' '+y1+','+x1+' '+y0+','+x0+' '+y0+'))'


#### BASIC MAP VIEWS ####

class MapListView(ListView):

    map_filter = "last_modified"
    queryset = Map.objects.all()

    def __init__(self, *args, **kwargs):
        self.map_filter = kwargs.pop("map_filter", "last_modified")
        self.queryset = self.queryset.order_by("-{0}".format(self.map_filter))
        super(MapListView, self).__init__(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs.update({"map_filter": self.map_filter})
        return kwargs


def maps_category(request, slug, template='maps/map_list.html'):
    category = get_object_or_404(TopicCategory, slug=slug)
    map_list = category.map_set.all()
    return render_to_response(
        template,
        RequestContext(request, {
            "object_list": map_list,
            "layer_category": category
            }
        )
    )


def maps_tag(request, slug, template='maps/map_list.html'):
    map_list = Map.objects.filter(keywords__slug__in=[slug])
    return render_to_response(
        template,
        RequestContext(request, {
            "object_list": map_list,
            "map_tag": slug
            }
        )
    )


def map_detail(request, mapid, template='maps/map_detail.html'):
    '''
    The view that show details of each map
    '''
    map_obj = _resolve_map(request, mapid, 'maps.view_map', _PERMISSION_MSG_VIEW)

    map_obj.popular_count += 1
    map_obj.save()

    config = map_obj.viewer_json()
    config = json.dumps(config)
    layers = MapLayer.objects.filter(map=map_obj.id)
    return render_to_response(template, RequestContext(request, {
        'config': config,
        'map': map_obj,
        'layers': layers,
        'permissions_json': json.dumps(_perms_info(map_obj, MAP_LEV_NAMES)),
    }))


@login_required
def map_metadata(request, mapid, template='maps/map_metadata.html'):
    '''
    The view that displays a form for
    editing map metadata
    '''
    map_obj = _resolve_map(request, mapid, msg=_PERMISSION_MSG_METADATA)

    if request.method == "POST":
        # Change metadata, return to map info page
        map_form = MapForm(request.POST, instance=map_obj, prefix="map")
        if map_form.is_valid():
            map_obj = map_form.save(commit=False)
            if map_form.cleaned_data["keywords"]:
                map_obj.keywords.add(*map_form.cleaned_data["keywords"])
            else:
                map_obj.keywords.clear()
            map_obj.save()

            return HttpResponseRedirect(reverse('map_detail', args=(map_obj.id,)))
    else:
        # Show form
        map_form = MapForm(instance=map_obj, prefix="map")

    return render_to_response(template, RequestContext(request, {
        "map": map_obj,
        "map_form": map_form
    }))


@login_required
def map_remove(request, mapid, template='maps/map_remove.html'):
    ''' Delete a map, and its constituent layers. '''
    map_obj = _resolve_map(request, mapid, 'maps.delete_map',
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


def map_embed(request, mapid=None, template='maps/map_embed.html'):
    if mapid is None:
        config = default_map_config()[0]
    else:
        map_obj = _resolve_map(request, mapid, 'maps.view_map')
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
    map_obj = _resolve_map(request, mapid, 'maps.view_map', _PERMISSION_MSG_VIEW)

    config = map_obj.viewer_json()
    return render_to_response(template, RequestContext(request, {
        'config': json.dumps(config),
        'DB_DATASTORE' : settings.DB_DATASTORE
    }))


def map_view_js(request, mapid):
    map_obj = _resolve_map(request, mapid, 'maps.view_map')
    config = map_obj.viewer_json()
    return HttpResponse(json.dumps(config), mimetype="application/javascript")

def map_json(request, mapid):
    if request.method == 'GET':
        map_obj = _resolve_map(request, mapid, 'maps.view_map')
        return HttpResponse(json.dumps(map_obj.viewer_json()))
    elif request.method == 'PUT':
        if not request.user.is_authenticated():
            return HttpResponse(
                _PERMISSION_MSG_LOGIN,
                status=401,
                mimetype="text/plain"
            )
        map_obj = _resolve_map(request, mapid, 'maps.change_map')
        try:
            map_obj.update_from_viewer(request.raw_post_data)
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
            'DB_DATASTORE' : settings.DB_DATASTORE
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
            map_obj.update_from_viewer(request.raw_post_data)
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

    If the query argument 'copy' is given, the inital map is
    a copy of the map with the id specified, otherwise the
    default map configuration is used.  If copy is specified
    and the map specified does not exist a 404 is returned.
    '''
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config()

    if request.method == 'GET' and 'copy' in request.GET:
        mapid = request.GET['copy']
        map_obj = _resolve_map(request, mapid, 'maps.view_map')

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
                    layer = Layer.objects.get(typename=layer_name)
                except ObjectDoesNotExist:
                    # bad layer, skip
                    continue

                if not request.user.has_perm('maps.view_layer', obj=layer):
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

                layers.append(MapLayer(
                    map = map_obj,
                    name = layer.typename,
                    ows_url = settings.GEOSERVER_BASE_URL + "wms",
                    layer_params=json.dumps( layer.attribute_config()),
                    visibility = True
                ))

            if bbox is not None:
                minx, maxx, miny, maxy = [float(c) for c in bbox]
                x = (minx + maxx) / 2
                y = (miny + maxy) / 2

                center = forward_mercator((x, y))
                if center[1] == float('-inf'):
                    center[1] = 0

                if maxx == minx:
                    width_zoom = 15
                else:
                    width_zoom = math.log(360 / (maxx - minx), 2)
                if maxy == miny:
                    height_zoom = 15
                else:
                    height_zoom = math.log(360 / (maxy - miny), 2)

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
    mapObject = _resolve_map(request, mapid, 'maps.view_map')

    map_status = dict()
    if request.method == 'POST':
        url = "%srest/process/batchDownload/launch/" % settings.GEOSERVER_BASE_URL

        def perm_filter(layer):
            return request.user.has_perm('layers.view_layer', obj=layer)

        mapJson = mapObject.json(perm_filter)

        # we need to remove duplicate layers
        j_map = json.loads(mapJson)
        j_layers = j_map["layers"]
        for j_layer in j_layers:
            if(len([l for l in j_layers if l == j_layer]))>1:
                j_layers.remove(j_layer)
        mapJson = json.dumps(j_map)

        resp, content = http_client.request(url, 'POST', body=mapJson)

        if resp.status not in (400, 404, 417):
            map_status = json.loads(content)
            request.session["map_status"] = map_status
        else:
            pass # XXX fix

    locked_layers = []
    remote_layers = []
    downloadable_layers = []

    for lyr in mapObject.layer_set.all():
        if lyr.group != "background":
            if not lyr.local:
                remote_layers.append(lyr)
            else:
                ownable_layer = Layer.objects.get(typename=lyr.name)
                if not request.user.has_perm('layers.view_layer', obj=ownable_layer):
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
         "geoserver" : settings.GEOSERVER_BASE_URL,
         "site" : settings.SITEURL
    }))


def map_download_check(request):
    """
    this is an endpoint for monitoring map downloads
    """
    try:
        layer = request.session["map_status"]
        if type(layer) == dict:
            url = "%srest/process/batchDownload/status/%s" % (settings.GEOSERVER_BASE_URL,layer["id"])
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

    mapObject = _resolve_map(request, mapid, 'maps.view_map')

    return render_to_response(template, RequestContext(request, {
        'map': mapObject,
        'siteurl': settings.SITEURL,
    }), mimetype='text/xml')

#### MAPS PERMISSIONS ####

def map_set_permissions(m, perm_spec):
    if "authenticated" in perm_spec:
        m.set_gen_level(AUTHENTICATED_USERS, perm_spec['authenticated'])
    if "anonymous" in perm_spec:
        m.set_gen_level(ANONYMOUS_USERS, perm_spec['anonymous'])
    users = [n[0] for n in perm_spec['users']]
    excluded = users + [m.owner]
    existing = m.get_user_levels().exclude(user__username__in=excluded)
    existing.delete()
    for username, level in perm_spec['users']:
        user = User.objects.get(username=username)
        m.set_user_level(user, level)


@require_POST
def map_permissions(request, mapid):
    try:
        map_obj = _resolve_map(request, mapid, 'maps.change_map_permissions')
    except PermissionDenied:
        # we are handling this differently for the client
        return HttpResponse(
            'You are not allowed to change permissions for this map',
            status=401,
            mimetype='text/plain'
        )


    permission_spec = json.loads(request.raw_post_data)
    map_set_permissions(map_obj, permission_spec)

    return HttpResponse(
        json.dumps({'success': True}),
        status=200,
        mimetype='text/plain'
    )


def _map_fix_perms_for_editor(info):
    perms = {
        Map.LEVEL_READ: Layer.LEVEL_READ,
        Map.LEVEL_WRITE: Layer.LEVEL_WRITE,
        Map.LEVEL_ADMIN: Layer.LEVEL_ADMIN,
    }

    def fix(x): return perms.get(x, "_none")

    info[ANONYMOUS_USERS] = fix(info[ANONYMOUS_USERS])
    info[AUTHENTICATED_USERS] = fix(info[AUTHENTICATED_USERS])
    info['users'] = [(u, fix(level)) for u, level in info['users']]

    return info


#### MAPS SEARCHING ####


def maps_search_page(request, template='maps/map_search.html'):
    # for non-ajax requests, render a generic search page

    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    return render_to_response(template, RequestContext(request, {
        'init_search': json.dumps(params or {}),
        "site" : settings.SITEURL,
        "search_api": reverse("maps_search_api"),
        "search_action": reverse("maps_search"),
        "search_type": "map"
    }))


def maps_search(request):
    """
    handles a basic search for maps using the Catalogue.

    the search accepts:
    q - general query for keywords across all fields
    start - skip to this point in the results
    limit - max records to return
    sort - field to sort results on
    dir - ASC or DESC, for ascending or descending order

    for ajax requests, the search returns a json structure
    like this:

    {
    'total': <total result count>,
    'next': <url for next batch if exists>,
    'prev': <url for previous batch if exists>,
    'query_info': {
        'start': <integer indicating where this batch starts>,
        'limit': <integer indicating the batch size used>,
        'q': <keywords used to query>,
    },
    'rows': [
      {
        'title': <map title,
        'abstract': '...',
        'detail' : <url geonode detail page>,
        'owner': <name of the map's owner>,
        'owner_detail': <url of owner's profile page>,
        'last_modified': <date and time of last modification>
      },
      ...
    ]}
    """
    if request.method == 'GET':
        params = request.GET
    elif request.method == 'POST':
        params = request.POST
    else:
        return HttpResponse(status=405)

    # grab params directly to implement defaults as
    # opposed to panicy django forms behavior.
    query = params.get('q', '')
    try:
        start = int(params.get('start', '0'))
    except Exception:
        start = 0

    try:
        limit = min(int(params.get('limit', DEFAULT_MAPS_SEARCH_BATCH_SIZE)),
                    MAX_MAPS_SEARCH_BATCH_SIZE)
    except Exception:
        limit = DEFAULT_MAPS_SEARCH_BATCH_SIZE


    sort_field = params.get('sort', u'')
    sort_field = unicodedata.normalize('NFKD', sort_field).encode('ascii','ignore')
    sort_dir = params.get('dir', 'ASC')
    result = _maps_search(query, start, limit, sort_field, sort_dir)

    result['success'] = True
    return HttpResponse(json.dumps(result), mimetype="application/json")


def _maps_search(query, start, limit, sort_field, sort_dir):

    keywords = _split_query(query)

    map_query = Map.objects
    for keyword in keywords:
        map_query = map_query.filter(
              Q(title__icontains=keyword)
            | Q(abstract__icontains=keyword))

    if sort_field:
        order_by = ("" if sort_dir == "ASC" else "-") + sort_field
        map_query = map_query.order_by(order_by)

    maps_list = []

    for m in map_query.all()[start:start+limit]:
        try:
            owner_name = Profile.objects.get(user=m.owner).name
        except Exception:
            owner_name = m.owner.first_name + " " + m.owner.last_name

        mapdict = {
            'id' : m.id,
            'title' : m.title,
            'abstract' : m.abstract,
            'detail' : reverse('map_detail', args=(m.id,)),
            'owner' : owner_name,
            'owner_detail' : reverse('profile_detail', args=(m.owner.username,)),
            'last_modified' : m.last_modified.isoformat()
            }
        maps_list.append(mapdict)

    result = {'rows': maps_list,
              'total': map_query.count()}

    result['query_info'] = {
        'start': start,
        'limit': limit,
        'q': query
    }
    if start > 0:
        prev = max(start - limit, 0)
        params = urlencode({'q': query, 'start': prev, 'limit': limit})
        result['prev'] = reverse('maps_search') + '?' + params

    next_page = start + limit + 1
    if next_page < map_query.count():
        params = urlencode({'q': query, 'start': next - 1, 'limit': limit})
        result['next'] = reverse('maps_search') + '?' + params

    return result


def maplayer_attributes(request, layername):
    #Return custom layer attribute labels/order in JSON format
    layer = Layer.objects.get(typename=layername)
    return HttpResponse(json.dumps(layer.attribute_config()), mimetype="application/json")
