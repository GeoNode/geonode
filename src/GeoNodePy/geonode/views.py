from django.conf import settings
from geonode.maps.models import Map
from django.shortcuts import render_to_response
from django.template import RequestContext
from geonode.maps.views import build_map_config, DEFAULT_MAP_CONFIG
from geonode.maps.context_processors import resource_urls
import random

def index(request): 
    featured = Map.objects.filter(featured=True)
    count = featured.count()
    if count == 0:
        map = DEFAULT_MAP_CONFIG
    else:         
        map = build_map_config(featured[random.randint(0, count - 1)])
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
