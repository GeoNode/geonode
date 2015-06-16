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
from httplib import HTTPConnection, HTTPSConnection
from urlparse import urlsplit
from django.conf import settings
from django.utils.http import is_safe_url
from django.http.request import validate_host


def proxy(request):
    PROXY_ALLOWED_HOSTS = getattr(settings, 'PROXY_ALLOWED_HOSTS', ())

    host = None

    if 'geonode.geoserver' in settings.INSTALLED_APPS:
        from geonode.geoserver.helpers import ogc_server_settings
        hostname = (ogc_server_settings.hostname,) if ogc_server_settings else ()
        PROXY_ALLOWED_HOSTS += hostname
        host = ogc_server_settings.netloc

    if 'url' not in request.GET:
        return HttpResponse("The proxy service requires a URL-encoded URL as a parameter.",
                            status=400,
                            content_type="text/plain"
                            )

    raw_url = request.GET['url']
    url = urlsplit(raw_url)
    locator = str(url.path)
    if url.query != "":
        locator += '?' + url.query
    if url.fragment != "":
        locator += '#' + url.fragment

    if not settings.DEBUG:
        if not validate_host(url.hostname, PROXY_ALLOWED_HOSTS):
            return HttpResponse("DEBUG is set to False but the host of the path provided to the proxy service"
                                " is not in the PROXY_ALLOWED_HOSTS setting.",
                                status=403,
                                content_type="text/plain"
                                )
    headers = {}

    if settings.SESSION_COOKIE_NAME in request.COOKIES and is_safe_url(url=raw_url, host=host):
        headers["Cookie"] = request.META["HTTP_COOKIE"]

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    if url.scheme == 'https':
        conn = HTTPSConnection(url.hostname, url.port)
    else:
        conn = HTTPConnection(url.hostname, url.port)
    conn.request(request.method, locator, request.body, headers)

    result = conn.getresponse()

    # If we get a redirect, let's add a useful message.
    if result.status in (301, 302, 303, 307):
        response = HttpResponse(('This proxy does not support redirects. The server in "%s" '
                                 'asked for a redirect to "%s"' % (url, result.getheader('Location'))),
                                status=result.status,
                                content_type=result.getheader("Content-Type", "text/plain")
                                )

        response['Location'] = result.getheader('Location')
    else:
        response = HttpResponse(
            result.read(),
            status=result.status,
            content_type=result.getheader("Content-Type", "text/plain"))

    return response
