from django.conf import settings
from geonode.maps.models import Map
from django.shortcuts import render_to_response
from django.template import RequestContext
from geonode.maps.views import build_map_config, DEFAULT_MAP_CONFIG

def index(request): 
    return render_to_response('index.html'))

def static(request, page):
    return render_to_response(page + '.html', RequestContext(request, {
        "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL
    }))

def community(request):
    maps = Map.objects.filter(featured=False)[:5]
    return render_to_response('community.html', RequestContext(request, {
        "maps": maps
    }))

def lang(request): 
    return render_to_response('lang.js', mimetype="text/javascript")
