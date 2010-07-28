from django.conf import settings
from geonode.maps.models import Map
from django.shortcuts import render_to_response
from django.template import RequestContext

def index(request): 
    return render_to_response('index.html', RequestContext(request))

def static(request, page):
    return render_to_response(page + '.html', RequestContext(request, {
        "GEOSERVER_BASE_URL": settings.GEOSERVER_BASE_URL
    }))

def community(request):
    return render_to_response('community.html', RequestContext(request))

def lang(request): 
    return render_to_response('lang.js', mimetype="text/javascript")
