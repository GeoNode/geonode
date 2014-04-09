# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.http import HttpResponse
from httplib import HTTPConnection,HTTPSConnection
from urlparse import urlsplit
import httplib2
from django.conf import settings
from django.utils.http import is_safe_url
from django.http.request import validate_host
from geonode.utils import ogc_server_settings

def proxy(request):
    PROXY_ALLOWED_HOSTS = (ogc_server_settings.hostname,) + getattr(settings, 'PROXY_ALLOWED_HOSTS', ())

    if 'url' not in request.GET:
        return HttpResponse(
                "The proxy service requires a URL-encoded URL as a parameter.",
                status=400,
                content_type="text/plain"
                )

    raw_url = request.GET['url']
    url = urlsplit(raw_url)
    locator = url.path
    if url.query != "":
        locator += '?' + url.query
    if url.fragment != "":
        locator += '#' + url.fragment

    if not settings.DEBUG:
        if not validate_host(url.hostname, PROXY_ALLOWED_HOSTS):
            return HttpResponse(
                    "DEBUG is set to False but the host of the path provided to the proxy service is not in the"
                    " PROXY_ALLOWED_HOSTS setting.",
                    status=403,
                    content_type="text/plain"
                    )
    headers = {}

    if settings.SESSION_COOKIE_NAME in request.COOKIES and is_safe_url(url=raw_url, host=ogc_server_settings.netloc):
        headers["Cookie"] = request.META["HTTP_COOKIE"]

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    if url.scheme =='https':
        conn = HTTPSConnection(url.hostname, url.port)
    else:
        conn = HTTPConnection(url.hostname, url.port)
    conn.request(request.method, locator, request.raw_post_data, headers)

    result = conn.getresponse()

    # If we get a redirect, let's add a useful message.
    if result.status in (301, 302, 303, 307):
         response = HttpResponse(
            ('This proxy does not support redirects. The server in "%s" '
            'asked for a redirect to "%s"' % (url, result.getheader('Location'))),
            status=result.status,
            content_type=result.getheader("Content-Type", "text/plain")
            )

         response['Location']=result.getheader('Location')
    else:
        response = HttpResponse(
            result.read(),
            status=result.status,
            content_type=result.getheader("Content-Type", "text/plain")
            )

    return response

def geoserver_rest_proxy(request, proxy_path, downstream_path):
    if not request.user.is_authenticated():
        return HttpResponse(
            "You must be logged in to access GeoServer",
            mimetype="text/plain",
            status=401)

    def strip_prefix(path, prefix):
        assert path.startswith(prefix)
        return path[len(prefix):]

    path = strip_prefix(request.get_full_path(), proxy_path)
    url = "".join([ogc_server_settings.LOCATION, downstream_path, path])

    http = httplib2.Http()
    http.add_credentials(*(ogc_server_settings.credentials))
    headers = dict()

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    response, content = http.request(
        url, request.method,
        body=request.raw_post_data or None,
        headers=headers)
        
    # we need to sync django here
    # we should remove this geonode dependency calling layers.views straight
    # from GXP, bypassing the proxy
    if downstream_path == 'rest/styles' and len(request.raw_post_data)>0:
        # for some reason sometime gxp sends a put with empty request
        # need to figure out with Bart
        from geonode.layers import utils
        utils.style_update(request, url)

    return HttpResponse(
        content=content,
        status=response.status,
        mimetype=response.get("content-type", "text/plain"))
