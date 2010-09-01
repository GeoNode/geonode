from django.http import HttpResponse
from httplib import HTTPConnection
from urlparse import urlsplit
import httplib2
import urllib
import simplejson 
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def proxy(request):
    if 'url' not in request.GET:
        return HttpResponse('The proxy service requires a URL-encoded URL as a parameter.', status=400, content_type="text/plain")

    url = urlsplit(request.GET['url'])
    locator = url.path
    if url.query != "":
        locator += '?' + url.query
    if url.fragment != "":
        locator += '#' + url.fragment

    conn = HTTPConnection(url.hostname, url.port)
    conn.request(request.method, locator, request.raw_post_data)
    result = conn.getresponse()
    response = HttpResponse(result.read(), status=result.status, content_type=result.getheader("Content-Type", "text/plain"))
    return response


@csrf_exempt
def geoserver(request):
    if not request.user.is_authenticated():
        return HttpResponse(
            "You must be logged in to access GeoServer",
            mimetype="text/plain",
            status=401
        )
    path = request.get_full_path()[11:] # strip "/geoserver/" from path
    url = "{geoserver}{path}".format(geoserver=settings.GEOSERVER_BASE_URL,path=path)
    h = httplib2.Http()    
    h.add_credentials(*settings.GEOSERVER_CREDENTIALS)
    headers = dict()

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]
    resp, content = h.request(
            url,
            request.method,
            body=request.raw_post_data or None,
            headers=headers
        )
    if resp.status != 404:
        if "content-type" in resp.keys():
            return HttpResponse(content=content,status=resp.status,mimetype=resp["content-type"])
        else: 
            return HttpResponse(content=content,status=resp.status)
    else: 
        return HttpResponse(content="Something went wrong",status=404)
