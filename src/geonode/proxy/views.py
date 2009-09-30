from django.template import Context, loader
from django.http import HttpResponse
from django.shortcuts import render_to_response

from httplib import HTTPConnection
from urlparse import urlsplit

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


