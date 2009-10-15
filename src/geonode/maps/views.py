from geonode.maps.models import Map
from geonode.maps.context_processors import resource_urls
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext

try:
    import json
except ImportError:
    import simplejson as json

DEFAULT_MAP_CONFIG = {
    "alignToGrid": True,
    "proxy": "/proxy/?url=",

    "about": {
        "title": "GeoNode Default Map",
        "abstract": "This is a demonstration of GeoNode, an application for assembling and publishing web based maps.  After adding layers to the map, use the 'Save Map' button above to contribute your map to the GeoNode community.",
        "contact": "For more information, contact <a href='http://opengeo.org'>OpenGeo</a>."
    },
    "wms": {
        "capra": "%swms" % settings.GEOSERVER_BASE_URL
    },
    "map": {
        "layers": [ {
            "name": settings.DEFAULT_MAP_BASE_LAYER,
            "wms": "capra",
            "group": "background"
        } ],
        "center": settings.DEFAULT_MAP_CENTER,
        "zoom": settings.DEFAULT_MAP_ZOOM
    }
}


def maps(request, mapid=None):
    if request.method == 'GET' and mapid is None:
        map_configs = [{"id": map.pk, "config": build_map_config(map)} for map in Map.objects.all()]
        return HttpResponse(json.dumps({"maps": map_configs}), mimetype="application/json")
    elif request.method == 'GET' and mapid is not None:
        map = Map.objects.get(pk=mapid)
        config = build_map_config(map)
        return HttpResponse(json.dumps(config))
    elif request.method == 'POST':
        try:
            conf = json.loads(request.raw_post_data)
            title = conf['about']['title']
            abstract = conf['about']['abstract']
            contact = conf['about']['contact']
            zoom = conf['map']['zoom']
            center_lon = conf['map']['center'][0]
            center_lat = conf['map']['center'][1]
        except (KeyError, ValueError):
            return HttpResponse("The server could not understand your request.", status=400, mimetype="text/plain")

        featured = False
        if 'featured' in conf['about']:
            featured = conf['about']['featured']

        map = Map.objects.create(title=title, abstract=abstract, contact=contact, zoom=zoom, center_lon=center_lon, center_lat=center_lat, featured=featured)
        map.save()

        if 'wms' in conf and 'layers' in conf['map']:
            services = conf['wms']
            layers = conf['map']['layers']
            ordering = 0
            for l in layers:
                if 'wms' in l and l['wms'] in services:
                    name = l['name']
                    group = l['group']
                    ows = services[l['wms']]
                    map.layer_set.create(name=name, group=group, ows_url=ows, stack_order=ordering)
                    ordering = ordering + 1

        response = HttpResponse('', status=201)
        response['Location'] = map.id
        return response

def newmap(request):
    return render_to_response('maps/view.html', 
            context_instance = RequestContext(request, 
                { 'config': json.dumps(DEFAULT_MAP_CONFIG) },
                [resource_urls]
            ))

def view(request, mapid):
    """  
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    map = Map.objects.get(pk=mapid)
    config = build_map_config(map)
    return render_to_response('maps/view.html',
                context_instance = RequestContext(request, 
                    { 'config': json.dumps(config) },
                    [resource_urls]
                ))

def embed(request, mapid=None):
    if mapid is None:
        config = DEFAULT_MAP_CONFIG
    else:
        map = Map.objects.get(pk=mapid)
        config = build_map_config(map)
    return render_to_response('maps/embed.html', 
        context_instance = RequestContext(request, 
            { 'config': json.dumps(config) },
            [resource_urls]
    ))



def data(request):
    context = RequestContext(request,[resource_urls])
    return render_to_response('data.html', context_instance=context)


def build_map_config(map):
    layers = map.layer_set.all()
    servers = list(set(l.ows_url for l in layers))
    server_mapping = {}

    for i in range(len(servers)):
        server_mapping[servers[i]] = str(i)

    config = {
        'about': {
            'title': map.title,
            'contact': map.contact,
            'abstract': map.abstract,
            'endorsed': map.endorsed
            },
        'map': { 
            'layers': [],
            'center': [map.center_lon, map.center_lat],
            'zoom': map.zoom
        }
    }

    config['wms'] = dict(zip(server_mapping.values(), server_mapping.keys()))

    for l in layers:
        config['map']['layers'].append({
            'name': l.name,
            'wms': server_mapping[l.ows_url],
            'group': l.group
        })

    return config

def view_js(request, mapid):
    map = Map.objects.get(pk=mapid)
    config = build_map_config(map)
    return HttpResponse(json.dumps(config), mimetype="application/javascript")
   

