from geonode.maps.models import Map, Layer, MapLayer
from geonode.maps.context_processors import resource_urls
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django.template import RequestContext
from django.utils.html import escape
import urllib2

try:
    import json
except ImportError:
    print "using simplejson instead of json"
    import simplejson as json

DEFAULT_MAP_CONFIG = {
    "alignToGrid": True,
    "proxy": "/proxy/?url=",
    "about": {
        "title": "GeoNode Default Map",
        "abstract": "This is a demonstration of GeoNode, an application for assembling and publishing web based maps.  After adding layers to the map, use the Save Map button above to contribute your map to the GeoNode community.",
        "contact": "For more information, contact OpenGeo at http://opengeo.org/"
    },
    "wms": {
        "capra": "%swms" % settings.GEOSERVER_BASE_URL
    },
    "map": {
        "layers": [ {
            "name": settings.DEFAULT_MAP_BASE_LAYER,
            "wms": "capra"
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
            map = read_json_map(request.raw_post_data)
            response = HttpResponse('', status=201)
            response['Location'] = map.id
            return response
        except:
            return HttpResponse(
                "The server could not understand your request.",
                status=400, 
                mimetype="text/plain"
            )

def read_json_map(json_text):
    conf = json.loads(json_text)
    title = conf['about']['title']
    abstract = conf['about']['abstract']
    contact = conf['about']['contact']
    zoom = conf['map']['zoom']
    center_lon = conf['map']['center'][0]
    center_lat = conf['map']['center'][1]

    featured = conf['about'].get('featured', False)

    map = Map.objects.create(
        title=title, 
        abstract=abstract, 
        contact=contact, 
        zoom=zoom, 
        center_lon=center_lon, 
        center_lat=center_lat, 
        featured=featured
    )

    if 'wms' in conf and 'layers' in conf['map']:
        services = conf['wms']
        layers = conf['map']['layers']
        ordering = 0
        for l in layers:
            if 'wms' in l and l['wms'] in services:
                name = l['name']
                group = l.get('group', '')
                ows = services[l['wms']]
                map.layer_set.create(name=name, group=group, ows_url=ows, stack_order=ordering)
                ordering = ordering + 1

    return map


def newmap(request):
    return render_to_response('maps/view.html', 
                { 'config': json.dumps(DEFAULT_MAP_CONFIG), 'bg': json.dumps(settings.MAP_BASELAYERS),
				  'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY
				},
            )

def mapdetail(request,mapid): 
    '''
    The view that show details of each map
    '''
    map = get_object_or_404(Map,pk=mapid) 
    layers = MapLayer.objects.filter(map=map.id) 
    return render_to_response("maps/mapinfo.html", 
            
                { 'config': json.dumps(DEFAULT_MAP_CONFIG), 
                  'bg': json.dumps(settings.MAP_BASELAYERS),
                  'map': map, 
                  'layers': layers,})

def getLayers(layers): 
    tmp = "/tmp"
    def slug(string): 
        string = string.replace(":","")
        string = string.replace("-","")
        return string
    def buildURL(name): 
        url = "%swfs?request=getfeature&service=wfs&version=1.1.0&typename=%s&outputFormat=SHAPE-ZIP" % (setttings.GEOSERVER_URL,name)
        return url 
    for layer in layers:
        try:
            url = urllib2.urlopen(buildURL(str(layer.name)))
            shapefile = url.read()
            file = open("%s/%s.zip" % (tmp,slug(str(layer.name))),'wb') 
            file.write(shapefile)
            file.close
        except IOError: 
            print "something went wrong" 
     
def download(request,mapid):
    '''
    The view that downloads all of the files associated with each map 
    '''
    map = get_object_or_404(Map,pk=mapid)
    layers = MapLayer.objects.filter(map=map)
    getLayers(layers)
    return HttpResponse("%s \n" % layers)

def view(request, mapid):
    """  
    The view that returns the map composer opened to
    the map with the given map ID.
    """
    map = Map.objects.get(pk=mapid)
    config = build_map_config(map)
    return render_to_response('maps/view.html',
                    { 'config': json.dumps(config), 'bg': json.dumps(settings.MAP_BASELAYERS),
					  'GOOGLE_API_KEY' : settings.GOOGLE_API_KEY
					}
                )


def embed(request, mapid=None):
    if mapid is None:
        config = DEFAULT_MAP_CONFIG
    else:
        map = Map.objects.get(pk=mapid)
        config = build_map_config(map)
    return render_to_response('maps/embed.html', 
            { 'config': json.dumps(config), 'bg': json.dumps(settings.MAP_BASELAYERS)}
    )


def data(request):
    return render_to_response('data.html', {'GEOSERVER_BASE_URL':settings.GEOSERVER_BASE_URL})


def build_map_config(map):
    layers = map.layer_set.all()
    servers = list(set(l.ows_url for l in layers))
    server_mapping = {}

    for i in range(len(servers)):
        server_mapping[servers[i]] = str(i)

    config = {
        'id': map.id,
        'about': {
            'title':    escape(map.title),
            'contact':  escape(map.contact),
            'abstract': escape(map.abstract),
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

def layer_detail(request, layername):
    layer = get_object_or_404(Layer, typename=layername)
    print layer
    return render_to_response(
        'maps/layer.html', 
        {"layer": layer}
    )
