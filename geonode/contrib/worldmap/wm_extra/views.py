import ast
import json
import math
import re
import urlparse

from guardian.shortcuts import get_perms

from django.conf import settings
from django.db.models import F
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import render, get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

from geonode.base.models import TopicCategory
from geonode.documents.models import get_related_documents
from geonode.geoserver.helpers import ogc_server_settings
from geonode.layers.models import Layer
from geonode.maps.models import Map, MapLayer, MapSnapshot
from geonode.utils import forward_mercator, default_map_config
from geonode.utils import llbbox_to_mercator
from geonode.layers.views import _resolve_layer
from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW, clean_config
# from geonode.maps.views import snapshot_config
from geonode.utils import DEFAULT_TITLE
from geonode.utils import DEFAULT_ABSTRACT
from geonode.utils import build_social_links
from geonode.security.views import _perms_info_json

from .models import LayerStats, ExtLayerAttribute
from .forms import EndpointForm
from .encode import despam, XssCleaner


_PERMISSION_MSG_LOGIN = _("You must be logged in to save this map")
_PERMISSION_MSG_SAVE = _("You are not permitted to save or edit this map.")
ows_sub = re.compile(r"[&\?]+SERVICE=WMS|[&\?]+REQUEST=GetCapabilities", re.IGNORECASE)


def ajax_snapshot_history(request, mapid):
    map_obj = Map.objects.get(pk=mapid)
    history = [snapshot.json() for snapshot in map_obj.snapshots]
    return HttpResponse(json.dumps(history), content_type="text/plain")


def ajax_layer_edit_check(request, layername):
    """
    Check if the the layer style is editable.
    """

    layer = get_object_or_404(Layer, typename=layername)
    can_edit_data = request.user.has_perm('change_layer_data', layer)

    return HttpResponse(
        str(can_edit_data),
        status=200 if can_edit_data else 403
    )


def ajax_layer_edit_style_check(request, layername):
    """
    Check if the the layer style is editable.
    """

    layer = get_object_or_404(Layer, typename=layername)
    can_edit_style = request.user.has_perm('change_layer_style', layer)

    return HttpResponse(
        str(can_edit_style),
        status=200 if can_edit_style else 403
    )


def ajax_layer_download_check(request, layername):
    """
    Check if the the layer is downloadable.
    """

    can_download = False
    layer = get_object_or_404(Layer, typename=layername)

    if request.user.is_authenticated():
        if layer.owner == request.user:
            can_download = True
        else:
            can_download = request.user.has_perm('download_resourcebase', layer.resourcebase_ptr)

    return HttpResponse(
        str(can_download).lower()
    )


@login_required
def ajax_layer_update(request, layername):
    """
    Used to update layer bounds and gazetteer after an edit transaction.
    """
    # TODO implement this!
    return HttpResponse('')


@login_required
def create_pg_layer(request):
    # TODO implement this!
    # return redirect('layer_upload')
    return HttpResponse('')


@login_required
def upload_layer(request):
    # TODO implement this!
    return HttpResponse('')


def ajax_increment_layer_stats(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed('Only POST is supported')

    if request.POST['layername'] != '':
        layer_match = Layer.objects.filter(typename=request.POST['layername'])[:1]
        for l in layer_match:
            layerStats, created = LayerStats.objects.get_or_create(layer=l)
            layerStats.visits += 1
            first_visit = True
            if request.session.get('visitlayer' + str(l.id), False):
                first_visit = False
            else:
                request.session['visitlayer' + str(l.id)] = True
            if first_visit or created:
                layerStats.uniques += 1
            layerStats.save()

    return HttpResponse(
        status=200
    )


def add_layer_wm(request):
    """
    The view that returns the map composer opened to
    a given map and adds a layer on top of it.
    """
    map_id = request.GET.get('map_id')
    layer_name = request.GET.get('layer_name')

    map_obj = _resolve_map(
        request,
        map_id,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    return map_view_wm(request, str(map_obj.id), layer_name=layer_name)


def map_view_wm(request, mapid, snapshot=None, layer_name=None, template='wm_extra/maps/map_view.html'):
    """
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    map_obj = _resolve_map(
        request,
        mapid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    if snapshot is None:
        config = map_obj.viewer_json(request)
    else:
        config = snapshot_config(snapshot, map_obj, request)
    if layer_name:
        config = add_layers_to_map_config(request, map_obj, (layer_name, ), False)

    config = gxp2wm(config, map_obj)

    return render(request, template, {
        'config': json.dumps(config),
        'map': map_obj,
        'preview': getattr(
            settings,
            'LAYER_PREVIEW_LIBRARY',
            '')
    })


def map_view_wm_mobile(request, mapid=None, snapshot=None):
    """
    The view that returns the map composer opened to
    the mobile version for the map with the given map ID.
    """
    map_obj = _resolve_map(
        request,
        mapid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    # TODO check if it is a new map
    # if mapid is None:
    #    return newmap(request);

    # TODO check if it is a mapid or suffix
    # if mapid.isdigit():
    #    map_obj = Map.objects.get(pk=mapid)
    # else:
    #    map_obj = Map.objects.get(urlsuffix=mapid)

    if snapshot is None:
        config = map_obj.viewer_json(request)
    else:
        config = snapshot_config(snapshot, map_obj, request)

    config = gxp2wm(config, map_obj)

    first_visit_mobile = True
    if request.session.get('visit_mobile' + str(map_obj.id), False):
        first_visit_mobile = False
    else:
        request.session['visit_mobile' + str(map_obj.id)] = True
    config['first_visit_mobile'] = first_visit_mobile

    template = 'wm_extra/maps/mobilemap.html'

    return render(request, template, {
        'config': json.dumps(config),
        # 'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY,
        # 'GEONETWORK_BASE_URL' : settings.GEONETWORK_BASE_URL,
        # 'GEOSERVER_BASE_URL' : settings.GEOSERVER_BASE_URL,
        # 'DB_DATASTORE' : settings.DB_DATASTORE,
        'maptitle': map_obj.title,
        # 'urlsuffix': get_suffix_if_custom(map_obj),
    })


def map_view_js(request, mapid):
    map_obj = _resolve_map(
        request,
        mapid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)

    config = map_obj.viewer_json(request)
    return HttpResponse(
        json.dumps(config),
        content_type="application/javascript")


def update_ext_map(request, map_obj):
    conf = json.loads(request.body)
    map_obj.urlsuffix = conf['about']['urlsuffix']
    x = XssCleaner()
    map_obj.extmap.content_map = despam(x.strip(conf['about']['introtext']))
    if 'groups' in conf['map']:
        map_obj.extmap.group_params = json.dumps(conf['map']['groups'])
    map_obj.extmap.save()
    map_obj.save()


def map_json_wm(request, mapid, snapshot=None):
    if request.method == 'GET':
        map_obj = _resolve_map(
            request,
            mapid,
            'base.view_resourcebase',
            _PERMISSION_MSG_VIEW)

        return HttpResponse(
            json.dumps(
                map_obj.viewer_json(request)))
    elif request.method == 'PUT':
        if not request.user.is_authenticated():
            return HttpResponse(
                _PERMISSION_MSG_LOGIN,
                status=401,
                content_type="text/plain"
            )

        map_obj = Map.objects.get(id=mapid)
        if not request.user.has_perm(
            'change_resourcebase',
                map_obj.get_self_resource()):
            return HttpResponse(
                _PERMISSION_MSG_SAVE,
                status=401,
                content_type="text/plain"
            )
        try:
            map_obj.update_from_viewer(request.body, context={'request': request, 'mapId': mapid, 'map': map_obj})
            update_ext_map(request, map_obj)
            MapSnapshot.objects.create(
                config=clean_config(
                    request.body),
                map=map_obj,
                user=request.user)

            return HttpResponse(
                json.dumps(
                    map_obj.viewer_json(request)))
        except ValueError as e:
            return HttpResponse(
                "The server could not understand the request." + str(e),
                content_type="text/plain",
                status=400
            )


def new_map_wm(request, template='wm_extra/maps/map_new.html'):
    config = new_map_config(request)
    config = gxp2wm(config)
    context_dict = {
        'config': config,
        'USE_GAZETTEER': settings.USE_GAZETTEER
    }
    context_dict["preview"] = getattr(
        settings,
        'LAYER_PREVIEW_LIBRARY',
        '')
    if isinstance(config, HttpResponse):
        return config
    else:
        return render(request, template, context_dict)


@csrf_exempt
def new_map_json_wm(request):
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
                content_type="text/plain",
                status=401
            )
        map_obj = Map(owner=request.user, zoom=0,
                      center_x=0, center_y=0)
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
            map_obj.update_from_viewer(body, context={'request': request, 'mapId': map_obj.id, 'map': map_obj})

            update_ext_map(request, map_obj)
            MapSnapshot.objects.create(
                config=clean_config(body),
                map=map_obj,
                user=request.user)
        except ValueError as e:
            return HttpResponse(str(e), status=400)
        else:
            return HttpResponse(
                json.dumps({'id': map_obj.id}),
                status=200,
                content_type='application/json'
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
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)

    if request.method == 'GET' and 'copy' in request.GET:
        mapid = request.GET['copy']
        map_obj = _resolve_map(request, mapid, 'base.view_resourcebase')

        map_obj.abstract = DEFAULT_ABSTRACT
        map_obj.title = DEFAULT_TITLE
        if request.user.is_authenticated():
            map_obj.owner = request.user

        config = map_obj.viewer_json(request)
        del config['id']
    else:
        if request.method == 'GET':
            params = request.GET
        elif request.method == 'POST':
            params = request.POST
        else:
            return HttpResponse(status=405)

        if 'layer' in params:
            map_obj = Map(projection=getattr(settings, 'DEFAULT_MAP_CRS',
                                             'EPSG:900913'))
            config = add_layers_to_map_config(request, map_obj, params.getlist('layer'))
        else:
            config = DEFAULT_MAP_CONFIG
    return json.dumps(config)


def add_layers_to_map_config(request, map_obj, layer_names, add_base_layers=True):
    DEFAULT_MAP_CONFIG, DEFAULT_BASE_LAYERS = default_map_config(request)
    bbox = None
    layers = []
    for layer_name in layer_names:
        try:
            layer = _resolve_layer(request, layer_name)
        except ObjectDoesNotExist:
            # bad layer, skip
            continue

        if not layer.is_published:
            # invisible layer, skip inclusion
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
            bbox[1] = max(bbox[1], layer_bbox[1])
            bbox[2] = min(bbox[2], layer_bbox[2])
            bbox[3] = max(bbox[3], layer_bbox[3])

        config = layer.attribute_config()

        # Add required parameters for a WM layer
        title = 'No title'
        if layer.title:
            title = layer.title
        config["title"] = title
        config["queryable"] = True

        config["srs"] = getattr(
            settings, 'DEFAULT_MAP_CRS', 'EPSG:900913')

        config["bbox"] = bbox if config["srs"] != 'EPSG:900913' \
            else llbbox_to_mercator([float(coord) for coord in bbox])

        access_token = request.session['access_token'] if request and 'access_token' in request.session else None
        if layer.storeType == "remoteStore":
            service = layer.service
            # Probably not a good idea to send the access token to every remote service.
            # This should never match, so no access token should be
            # sent to remote services.
            ogc_server_url = urlparse.urlsplit(
                ogc_server_settings.PUBLIC_LOCATION).netloc
            service_url = urlparse.urlsplit(service.base_url).netloc

            if access_token and ogc_server_url == service_url and 'access_token' not in service.base_url:
                url = '%s?access_token=%s' % (service.base_url, access_token)
            else:
                url = service.base_url
            maplayer = MapLayer(map=map_obj,
                                name=layer.alternate,
                                ows_url=layer.ows_url,
                                layer_params=json.dumps(config),
                                visibility=True,
                                source_params=json.dumps({
                                    "ptype": service.ptype,
                                    "remote": True,
                                    "url": url,
                                    "name": service.name}))
        else:
            ogc_server_url = urlparse.urlsplit(
                ogc_server_settings.PUBLIC_LOCATION).netloc
            layer_url = urlparse.urlsplit(layer.ows_url).netloc

            if access_token and ogc_server_url == layer_url and 'access_token' not in layer.ows_url:
                url = '%s?access_token=%s' % (layer.ows_url, access_token)
            else:
                url = layer.ows_url
            maplayer = MapLayer(
                map=map_obj,
                name=layer.alternate,
                ows_url=url,
                # use DjangoJSONEncoder to handle Decimal values
                layer_params=json.dumps(config, cls=DjangoJSONEncoder),
                visibility=True
            )
        layers.append(maplayer)

    if bbox is not None:
        minx, maxx, miny, maxy = [float(coord) for coord in bbox]
        x = (minx + maxx) / 2
        y = (miny + maxy) / 2

        if getattr(
            settings,
            'DEFAULT_MAP_CRS',
                'EPSG:900913') == "EPSG:4326":
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

    if add_base_layers:
        layers_to_add = DEFAULT_BASE_LAYERS + layers
    else:
        layers_to_add = layers
    config = map_obj.viewer_json(request, *layers_to_add)

    config['fromLayer'] = True

    return config


def map_detail_wm(request, mapid, snapshot=None, template='wm_extra/maps/map_detail.html'):
    '''
    The view that show details of each map
    '''
    map_obj = _resolve_map(
        request,
        mapid,
        'base.view_resourcebase',
        _PERMISSION_MSG_VIEW)
    # Update count for popularity ranking,
    # but do not includes admins or resource owners
    if request.user != map_obj.owner and not request.user.is_superuser:
        Map.objects.filter(
            id=map_obj.id).update(
            popular_count=F('popular_count') + 1)

    if snapshot is None:
        config = map_obj.viewer_json(request)
    else:
        config = snapshot_config(snapshot, map_obj, request)

    config = json.dumps(config)
    layers = MapLayer.objects.filter(map=map_obj.id)
    links = map_obj.link_set.download()

    config = gxp2wm(config)

    context_dict = {
        'config': config,
        'resource': map_obj,
        'layers': layers,
        'perms_list': get_perms(request.user, map_obj.get_self_resource()),
        'permissions_json': _perms_info_json(map_obj),
        "documents": get_related_documents(map_obj),
        'links': links,
    }

    context_dict["preview"] = getattr(
        settings,
        'GEONODE_CLIENT_LAYER_PREVIEW_LIBRARY',
        'geoext')
    context_dict["crs"] = getattr(
        settings,
        'DEFAULT_MAP_CRS',
        'EPSG:900913')

    if settings.SOCIAL_ORIGINS:
        context_dict["social_links"] = build_social_links(request, map_obj)

    return render(request, template, context_dict)


def uniqifydict(seq, item):
    """
    get a list of unique dictionary elements based on a certain  item (ie 'group').
    """
    results = []
    items = []
    for x in seq:
        if x[item] not in items:
            items.append(x[item])
            results.append(x)
    return results


def gxp2wm(config, map_obj=None):
    """
    Convert a GeoNode map json or string config to the WorldMap client format.
    """
    config_is_string = False
    # let's first see if it is a string, in which case must be converted to json
    if isinstance(config, basestring):
        config = json.loads(config)
        config_is_string = True

    if map_obj:
        config['id'] = map_obj.id

    topics = TopicCategory.objects.all()
    topicArray = []
    for topic in topics:
        topicArray.append([topic.identifier, topic.gn_description])
    topicArray.append(['General', 'General'])
    groups = set()

    config['topic_categories'] = topicArray

    config['proxy'] = '/proxy/?url='

    # TODO check permissions here
    config['edit_map'] = True

    # 3 different layer types
    #
    # 1. background layer: group: background, ows_url: None
    #
    # 2. WM local layer:
    #    ows_url: http://localhost:8080/geoserver/wms,
    #    layer_params = {"selected": true, "title": "camer_hyd_basins_vm0_2007",
    #       "url": "http://localhost:8080/geoserver/wms",
    #       "tiled": true, "detail_url": "http://worldmap.harvard.edu/data/geonode:camer_hyd_basins_vm0_2007",
    #       "local": true,
    #       "llbbox": [-94.549682617, 9.553222656, -82.972412109, 18.762207031]}
    #
    # 3. WM remote layer (HH):
    #    ows_url:
    #    http://192.168.33.15:8002/registry/hypermap/layer/13ff2fea-d479-4fc7-87a6-3eab7d349def/map/wmts/market/default_grid/$%7Bz%7D/$%7Bx%7D/$%7By%7D.png
    #    layer_params = {"title": "market", "selected": true,
    #       "detail_url": "http://192.168.33.15:8002/registry/hypermap/layer/13ff2fea-d479-4fc7-87a6-3eab7d349def/",
    #       "local": false}

    # let's detect WM or HH layers and alter configuration as needed
    bbox = [-180, -90, 180, 90]
    valid_layers = []
    for layer_config in config['map']['layers']:
        is_valid = True
        is_wm = False
        is_hh = False
        if 'source' not in layer_config:
            is_valid = False
            print 'Skipping this layer as it is missing source... %s' % layer_config
        else:
            source_id = layer_config['source']
            source = config['sources'][source_id]
            if 'url' in source:
                source_url = source['url']
                if settings.GEOSERVER_PUBLIC_LOCATION in source_url:
                    config['sources'][source_id]['url'] = source_url
                    if 'name' in layer_config:
                        is_wm = True
                if 'registry/hypermap' in source_url:
                    is_hh = True
            group = 'General'
            layer_config['tiled'] = True
            if is_wm:
                source = layer_config['source']
                config['sources'][source]['ptype'] = 'gxp_gnsource'
                config['sources'][source]['url'] = config['sources'][source]['url'].replace('ows', 'wms')
                layer_config['local'] = True
                layer_config['queryable'] = True
                alternate = layer_config['name']
                layer = None
                try:
                    layer = Layer.objects.get(alternate=alternate)
                except Layer.DoesNotExist:
                    is_valid = False
                    print 'Skipping this layer as it is not existing in GeoNode... %s' % layer_config
                if layer:
                    layer_config['attributes'] = (get_layer_attributes(layer))
                    layer_config['url'] = layer.ows_url.replace('ows', 'wms')
                    if 'styles' not in layer_config:
                        if layer.default_style:
                            layer_config['styles'] = [layer.default_style.name, ]
                        else:
                            if layer.styles.all().count() > 0:
                                layer_config['styles'] = [layer.styles.all()[0].name, ]
                    else:
                        if isinstance(layer_config['styles'], unicode):
                            try:
                                layer_config['styles'] = ast.literal_eval(layer_config['styles'])
                            except:  # noqa
                                layer_config['styles'] = [layer_config['styles'], ]
                    if 'styles' not in layer_config:
                        is_valid = False
                        print 'Skipping this layer as it has not a style... %s' % layer_config
                    if layer.category:
                        group = layer.category.gn_description
                    layer_config["srs"] = getattr(
                        settings, 'DEFAULT_MAP_CRS', 'EPSG:900913')
                    bbox = layer.bbox[:-1]
                    # WorldMap GXP use a different bbox representation than GeoNode
                    bbox = [bbox[0], bbox[2], bbox[1], bbox[3]]
                    layer_config["bbox"] = [float(coord) for coord in bbox] if layer_config["srs"] != 'EPSG:900913' \
                        else llbbox_to_mercator([float(coord) for coord in bbox])
            if is_hh:
                layer_config['local'] = False
                layer_config['styles'] = ''
                hh_url = (
                    '%smap/wmts/%s/default_grid/${z}/${x}/${y}.png' %
                    (layer_config['detail_url'], layer_config['name'])
                )
                layer_config['url'] = hh_url
            if is_wm or is_hh:
                # bbox
                layer_config['llbbox'] = [float(coord) for coord in bbox]
                # group
                if 'group' not in layer_config:
                    layer_config['group'] = group
                else:
                    group = layer_config['group']
                if group not in groups:
                    groups.add(group)
                # let's make sure the group exists in topicArray (it could be a custom group create from user in GXP)
                is_in_topicarray = False
                for cat in topicArray:
                    if group == cat[1]:
                        is_in_topicarray = True
                if not is_in_topicarray:
                    topicArray.append([group, group])
        if is_valid:
            valid_layers.append(layer_config)

    config['map']['layers'] = valid_layers
    config['map']['groups'] = []

    # about and groups from existing map
    if map_obj:
        config['about']['introtext'] = map_obj.extmap.content_map
        config['about']['urlsuffix'] = map_obj.urlsuffix
        if map_obj.extmap.group_params:
            config["map"]["groups"] = uniqifydict(json.loads(map_obj.extmap.group_params), 'group')
    else:
        # TODO check if this works with different languages
        config['about']['introtext'] = unicode(settings.DEFAULT_MAP_ABSTRACT)

    if not [d for d in config['map']['groups'] if d['group'] == group]:
        for group in groups:
            config['map']['groups'].append({"expanded": "true", "group": group})

    if config_is_string:
        config = json.dumps(config)

    return config


def get_layer_attributes(layer):
    """
    Return a dictionary of attributes for a layer.
    """
    attribute_fields = []
    attributes = layer.attribute_set.order_by('display_order')
    for la in attributes:
        searchable = False
        if hasattr(la, 'extlayerattribute'):
            searchable = la.extlayerattribute.searchable
        attribute_fields.append({"id": la.attribute,
                                 "header": la.attribute,
                                 "searchable": searchable
                                 })
    return attribute_fields


def snapshot_config(snapshot, map_obj, request):
    """
    Get the snapshot map configuration - look up WMS parameters (bunding box)
    for local GeoNode layers
    """

    def source_config(maplayer):
        """
        Generate a dict that can be serialized to a GXP layer source
        configuration suitable for loading this layer.
        """
        try:
            cfg = json.loads(maplayer.source_params)
        except Exception:
            cfg = dict(ptype="gxp_gnsource", restUrl="/gs/rest")

        if maplayer.ows_url:
            cfg["url"] = ows_sub.sub('', maplayer.ows_url)
            if "ptype" not in cfg:
                cfg["ptype"] = "gxp_wmscsource"

        if "ptype" in cfg and cfg["ptype"] == "gxp_gnsource":
            cfg["restUrl"] = "/gs/rest"
        return cfg

    def layer_config(maplayer, user):
        """
        Generate a dict that can be serialized to a GXP layer configuration
        suitable for loading this layer.

        The "source" property will be left unset; the layer is not aware of the
        name assigned to its source plugin.  See
        :method:`geonode.maps.models.Map.viewer_json` for an example of
        generating a full map configuration.
        """

        try:
            cfg = json.loads(maplayer.layer_params)
        except Exception:
            cfg = dict()

        if maplayer.format:
            cfg['format'] = maplayer.format
        if maplayer.name:
            cfg["name"] = maplayer.name
        if maplayer.opacity:
            cfg['opacity'] = maplayer.opacity
        if maplayer.styles:
            cfg['styles'] = maplayer.styles
        if maplayer.transparent:
            cfg['transparent'] = True

        cfg["fixed"] = maplayer.fixed
        if 'url' not in cfg:
            cfg['url'] = maplayer.ows_url
        if cfg['url']:
            cfg['url'] = ows_sub.sub('', cfg['url'])
        if maplayer.group:
            cfg["group"] = maplayer.group
        cfg["visibility"] = maplayer.visibility

        if maplayer.name is not None and maplayer.source_params.find("gxp_gnsource") > -1:
            # Get parameters from GeoNode instead of WMS GetCapabilities
            try:
                gnLayer = Layer.objects.get(alternate=maplayer.name)
                if gnLayer.srid:
                    cfg['srs'] = gnLayer.srid
                if gnLayer.bbox:
                    cfg['bbox'] = json.loads(gnLayer.bbox)
                if gnLayer.llbbox:
                    cfg['llbbox'] = json.loads(gnLayer.llbbox)
                cfg['attributes'] = (get_layer_attributes(gnLayer))
                attribute_cfg = gnLayer.attribute_config()
                if "getFeatureInfo" in attribute_cfg:
                    cfg["getFeatureInfo"] = attribute_cfg["getFeatureInfo"]
                cfg['queryable'] = (gnLayer.storeType == 'dataStore'),
                cfg['disabled'] = user is not None and not user.has_perm('maps.view_layer', obj=gnLayer)
                # cfg["displayOutsideMaxExtent"] = user is not None and  user.has_perm('maps.change_layer', obj=gnLayer)
                cfg['visibility'] = cfg['visibility'] and not cfg['disabled']
                cfg['abstract'] = gnLayer.abstract
                cfg['styles'] = maplayer.styles
                cfg['local'] = True
            except Exception as e:
                # Give it some default values so it will still show up on the map, but disable it in the layer tree
                cfg['srs'] = 'EPSG:900913'
                cfg['llbbox'] = [-180, -90, 180, 90]
                cfg['attributes'] = []
                cfg['queryable'] = False,
                cfg['disabled'] = False
                cfg['visibility'] = cfg['visibility'] and not cfg['disabled']
                cfg['abstract'] = ''
                cfg['styles'] = ''
                print "Could not retrieve Layer with typename of %s : %s" % (maplayer.name, str(e))
        elif maplayer.source_params.find("gxp_hglsource") > -1:
            # call HGL ServiceStarter asynchronously to load the layer into HGL geoserver
            from geonode.queue.tasks import loadHGL
            loadHGL.delay(maplayer.name)

        return cfg

    # Match up the layer with it's source
    def snapsource_lookup(source, sources):
        for k, v in sources.iteritems():
            if v.get("id") == source.get("id"):
                return k
        return None

    # Set up the proper layer configuration
    # def snaplayer_config(layer, sources, user):
    def snaplayer_config(layer, sources, request):
        user = request.user if request else None
        cfg = layer_config(layer, user)
        src_cfg = source_config(layer)
        source = snapsource_lookup(src_cfg, sources)
        if source:
            cfg["source"] = source
        if src_cfg.get(
                "ptype",
                "gxp_wmscsource") == "gxp_wmscsource" or src_cfg.get(
                "ptype",
                "gxp_gnsource") == "gxp_gnsource":
            cfg["buffer"] = 0
        return cfg

    from geonode.utils import num_decode
    from geonode.utils import layer_from_viewer_config
    decodedid = num_decode(snapshot)
    snapshot = get_object_or_404(MapSnapshot, pk=decodedid)
    if snapshot.map == map_obj.map:
        config = json.loads(clean_config(snapshot.config))
        layers = [l for l in config["map"]["layers"]]
        sources = config["sources"]
        maplayers = []
        for ordering, layer in enumerate(layers):
            maplayers.append(
                layer_from_viewer_config(
                    map_obj.id,
                    MapLayer,
                    layer,
                    config["sources"][
                        layer["source"]],
                    ordering,
                    False))
#             map_obj.map.layer_set.from_viewer_config(
# map_obj, layer, config["sources"][layer["source"]], ordering))
        config['map']['layers'] = [
            snaplayer_config(
                l,
                sources,
                request) for l in maplayers]
    else:
        config = map_obj.viewer_json(request)
    return config


def printmap(request, mapid=None, snapshot=None):

    return render(request, 'wm_extra/maps/map_print.html', {})


@login_required
def add_endpoint(request):
    """
    Let the user to add an endpoint for a remote service.
    """
    if request.method == 'POST':
        endpoint_form = EndpointForm(request.POST)
        if endpoint_form.is_valid():
            endpoint = endpoint_form.save(commit=False)
            endpoint.owner = request.user
            endpoint.save()
            return render(
                request,
                'wm_extra/endpoint_added.html',
                {
                    "endpoint": endpoint,
                }
            )
        else:
            print 'Error posting an endpoint'
    else:
        endpoint_form = EndpointForm()

    return render(
        request,
        'wm_extra/endpoint_add.html',
        {
            "form": endpoint_form,
        }
    )


def official_site(request, site):
    """
    The view that returns the map composer opened to
    the map with the given urlsuffix  site url.
    """
    map_obj = get_object_or_404(Map, urlsuffix=site)
    return map_view_wm(request, str(map_obj.id))


@login_required
def layer_searchable_fields(
        request,
        layername):
    """
    Manage the layer in the gazetteer.
    """

    layer = _resolve_layer(
        request,
        layername,
        'base.change_resourcebase_metadata',
        'permissions message from searchable layers')

    status_message = None
    if request.method == 'POST':
        attributes_list = request.POST.getlist('attributes')
        status_message = ''
        for attribute in layer.attributes:
            ext_att, created = ExtLayerAttribute.objects.get_or_create(attribute=attribute)
            ext_att.searchable = False
            if attribute.attribute in attributes_list and attribute.attribute_type == 'xsd:string':
                ext_att.searchable = True
                status_message += ' %s' % attribute.attribute
            ext_att.save()

    searchable_attributes = []
    for attribute in layer.attributes:
        if attribute.attribute_type == 'xsd:string':
            if hasattr(attribute, 'extlayerattribute'):
                attribute.searchable = attribute.extlayerattribute.searchable
            else:
                attribute.searchable = False
            searchable_attributes.append(attribute)

    template = 'wm_extra/layers/edit_searchable_fields.html'

    return render(request, template, {
        "layer": layer,
        "searchable_attributes": searchable_attributes,
        "status_message": status_message,
    })
