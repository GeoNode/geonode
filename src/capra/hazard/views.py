from django.conf import settings
from django.shortcuts import render_to_response
from django.template import RequestContext
from geonode.maps.context_processors import resource_urls
from httplib2 import Http
import json 

def index(request): 
    return render_to_response("index.html",
        context_instance=RequestContext(request, {}, [resource_urls])
    )

def report(request): 
    params = extract_params(request)
    result = request_rest_process("hazard", params)

    return render_to_response("report.html",
        context_instance=RequestContext(request, {"result": result}, [resource_urls])
    )

def extract_params(request):
    """
    Examine a report request and extract the parameters that should be 
    included in the corresponding WPS request.
    """
    if (request.method == "POST"):
        try:
            params = json.loads(request.raw_post_data)
            params["radius"] = radius_for(params["scale"])
            del params["scale"]
            return params
        except:
            pass
    return {}

def radius_for(scale): 
    """
    Given a scale denominator for the viewport, produce the proper buffer radius
    for the report process. 
    """
    return 12

def request_rest_process(process, params): 
    """
    Make a REST request for the WPS process named, with the provided parameters.
    """
    url = "%srest/process/%s" % (settings.GEOSERVER_BASE_URL, process)
    user, pw = settings.GEOSERVER_CREDENTIALS
    http = Http()
    http.add_credentials(user, pw)
    response, content = http.request(url, "POST", json.dumps(params))
    if (response.status is not 200):
        raise Exception
    return json.loads(content)

