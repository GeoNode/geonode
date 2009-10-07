from django.conf import settings
from geonode.maps.models import Map
from django.shortcuts import render_to_response
from django.template import RequestContext
from geonode.maps.views import build_map_config
from geonode.maps.context_processors import resource_urls

DEFAULT_MAP_CONFIG = {
    "alignToGrid": True,
    "proxy": "/proxy/?url=",

    "about": {
        "title": "GeoNode Demo Map",
        "abstract": "This is a demonstration of GeoNode, an application for assembling and publishing web based maps.  After adding layers to the map, use the 'Save Map' button above to contribute your map to the GeoNode community.",
        "contact": "For more information, contact <a href='http://opengeo.org'>OpenGeo</a>."
    },
    "wms": {
        "capra": "%swms" % settings.GEOSERVER_BASE_URL
    },
    "map": {
        "layers": [ {
            "name": "base:nicaragua_admin",
            "wms": "capra",
            "group": "background"
        } ],
        "center": [-84.7, 12.8],
        "zoom": 7
    }
}

def index(request): 
    featured = Map.objects.filter(featured=True)
    if featured.count() == 0:
        map = DEFAULT_MAP_CONFIG
    else: 
        map = build_map_config(featured[0])
    context = RequestContext(request, {'map': map}, [resource_urls])
    return render_to_response('index.html', context_instance=context);

def static(request, page):
    info = dict(GEOSERVER_BASE_URL=settings.GEOSERVER_BASE_URL)
    context = RequestContext(request, info, [resource_urls])
    return render_to_response(page + '.html', context_instance=context)

def community(request):
    maps = Map.objects.filter(featured=False)[:5]
    context = RequestContext(request, dict(maps=maps), [resource_urls])
    return render_to_response('community.html', context_instance=context)

def curated(request):
    maps = Map.objects.filter(featured=True)[:5]
    context = RequestContext(request, dict(maps=maps), [resource_urls])
    return render_to_response('curated.html', context_instance=context)

def lang(request): 
    return render_to_response('lang.js', mimetype="text/javascript")
