from django.shortcuts import render_to_response
from django.template import RequestContext
from geonode.maps.context_processors import resource_urls

def index(request): 
    return render_to_response("index.html",
        context_instance=RequestContext(request, {}, [resource_urls])
    )
