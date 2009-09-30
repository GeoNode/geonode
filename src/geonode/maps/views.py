from geonode.maps.models import Map
from django.http import HttpResponse
from django.shortcuts import render_to_response
try:
    import json
except ImportError:
    import simplejson as json

DEFAULT_MAP_CONFIG = {
    "alignToGrid": True,
    "proxy": "/proxy/?url=",

    "about": {
        "title": "GeoNode Demo Map",
        "abstract": "This is a demonstration of GeoNode, an application for assembling and publishing web based maps.  After adding layers to the map, use the 'Save Map' button above to contribute your map to the GeoNode community.",
        "contact": "For more information, contact <a href='http://opengeo.org'>OpenGeo</a>."
    },
    "wms": {
        "capra": "http://capra.opengeo.org/geoserver/wms/"
    },
    "map": {
        "layers": [ {
            "name": "risk:nicaragua_admin",
            "wms": "capra",
            "group": "background"
        } ],
        "center": [-84.7, 12.8],
        "zoom": 5
    }
}

def index(request): 
    if Map.objects.count() == 0:
        map = DEFAULT_MAP_CONFIG
    else: 
        map = build_map_config(Map.objects.all()[0])
    return render_to_response('maps/index.html', {'map': map});

def community(request):
        maps = Map.objects.filter(featured=False)[:5]
        return render_to_response('maps/community.html', {
            'maps': maps
        })

#@@ replace with piston
def maps(request):
    if request.method == 'GET':
        maps = Map.objects.filter(featured=True)[:5]
        return render_to_response('maps/maps.html', {
            'maps': maps
        })
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
    return render_to_response('maps/view.html', { 'config': json.dumps(DEFAULT_MAP_CONFIG) })

def view(request, mapid):
    map = Map.objects.get(pk=mapid)
    config = build_map_config(map)
    return render_to_response('maps/view.html', { 'config': json.dumps(config) })

def embed(request, mapid=None):
    if mapid is None:
        config = DEFAULT_MAP_CONFIG
    else:
        map = Map.objects.get(pk=mapid)
        config = build_map_config(map)
    return render_to_response('maps/embed.html', { 'config': json.dumps(config) })

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
            'abstract': map.abstract
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
   
def static(request, page):
    return render_to_response('maps/' + page + '.html')

def lang(request): 
    return render_to_response('maps/lang.js', mimetype="text/javascript")
