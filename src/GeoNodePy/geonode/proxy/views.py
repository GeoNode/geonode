from django.http import HttpResponse
from httplib import HTTPConnection
from urlparse import urlsplit
import httplib2
import urllib
import simplejson 
from django.conf import settings
from django.contrib.auth.decorators import login_required

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

# http://localhost:8001/mapserver/ ? geoserver/

@login_required
def geoserver(request,path):
    url = "{geoserver}{url}".format(geoserver=settings.GEOSERVER_BASE_URL,url=path)
    h = httplib2.Http()    
    h.add_credentials(*settings.GEOSERVER_CREDENTIALS)
    resp, content = h.request(url,request.method,body=request.raw_post_data)
    return HttpResponse(content=content,status=resp.status)
