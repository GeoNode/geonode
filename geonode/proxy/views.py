# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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
from django.views.decorators.csrf import requires_csrf_token
from django.middleware.csrf import get_token


@requires_csrf_token
def proxy(request, url=None, response_callback=None, sec_chk_hosts=True, sec_chk_rules=True, **kwargs):
    # Security rules and settings
    PROXY_ALLOWED_HOSTS = getattr(settings, 'PROXY_ALLOWED_HOSTS', ())

    # Sanity url checks
    if 'url' not in request.GET and not url:
        return HttpResponse("The proxy service requires a URL-encoded URL as a parameter.",
                            status=400,
                            content_type="text/plain"
                            )

    raw_url = url or request.GET['url']
    url = urlsplit(raw_url)
    locator = str(url.path)
    if url.query != "":
        locator += '?' + url.query
    if url.fragment != "":
        locator += '#' + url.fragment

    access_token = None
    if 'access_token' in request.session:
        access_token = request.session['access_token']

    # White-Black Listing Hosts
    if sec_chk_hosts and not settings.DEBUG:
        if 'geonode.geoserver' in settings.INSTALLED_APPS:
            from geonode.geoserver.helpers import ogc_server_settings
            hostname = (ogc_server_settings.hostname,) if ogc_server_settings else ()
            if hostname not in PROXY_ALLOWED_HOSTS:
                PROXY_ALLOWED_HOSTS += hostname

        if not validate_host(url.hostname, PROXY_ALLOWED_HOSTS):
            return HttpResponse("DEBUG is set to False but the host of the path provided to the proxy service"
                                " is not in the PROXY_ALLOWED_HOSTS setting.",
                                status=403,
                                content_type="text/plain"
                                )

    # Security checks based on rules; allow only specific requests
    if sec_chk_rules:
        # TODO: Not yet implemented
        pass

    # Collecting headers and cookies
    headers = {}
    cookies = None
    csrftoken = None

    if settings.SESSION_COOKIE_NAME in request.COOKIES and is_safe_url(url=raw_url, host=url.hostname):
        cookies = request.META["HTTP_COOKIE"]

    for cook in request.COOKIES:
        name = str(cook)
        value = request.COOKIES.get(name)
        if name == 'csrftoken':
            csrftoken = value
        cook = "%s=%s" % (name, value)
        cookies = cook if not cookies else (cookies + '; ' + cook)

    csrftoken = get_token(request) if not csrftoken else csrftoken

    if csrftoken:
        headers['X-Requested-With'] = "XMLHttpRequest"
        headers['X-CSRFToken'] = csrftoken
        cook = "%s=%s" % ('csrftoken', csrftoken)
        cookies = cook if not cookies else (cookies + '; ' + cook)

    if cookies:
        if 'JSESSIONID' in request.session and request.session['JSESSIONID']:
            cookies = cookies + '; JSESSIONID=' + \
                request.session['JSESSIONID']
        headers['Cookie'] = cookies

    if request.method in ("POST", "PUT") and "CONTENT_TYPE" in request.META:
        headers["Content-Type"] = request.META["CONTENT_TYPE"]

    access_token = None
    if 'access_token' in request.session:
        access_token = request.session['access_token']    #

    if access_token:
        # TODO: Bearer is currently cutted of by Djano / GeoServer
        if request.method in ("POST", "PUT"):
            headers['Authorization'] = 'Bearer %s' % access_token
        if access_token and 'access_token' not in locator:
            query_separator = '&' if '?' in locator else '?'
            locator = ('%s%saccess_token=%s' % (locator, query_separator, access_token))
    elif 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META.get('HTTP_AUTHORIZATION', request.META.get('HTTP_AUTHORIZATION2'))
        if auth:
            headers['Authorization'] = auth

    site_url = urlsplit(settings.SITEURL)

    pragma = "no-cache"
    referer = request.META[
        "HTTP_REFERER"] if "HTTP_REFERER" in request.META else \
        "{scheme}://{netloc}/".format(scheme=site_url.scheme, netloc=site_url.netloc)
    encoding = request.META["HTTP_ACCEPT_ENCODING"] if "HTTP_ACCEPT_ENCODING" in request.META else "gzip"

    headers.update({"Pragma": pragma,
                    "Referer": referer,
                    "Accept-encoding": encoding, })

    if url.scheme == 'https':
        conn = HTTPSConnection(url.hostname, url.port)
    else:
        conn = HTTPConnection(url.hostname, url.port)
    conn.request(request.method, locator, request.body, headers)
    response = conn.getresponse()
    content = response.read()
    status = response.status
    content_type = response.getheader("Content-Type", "text/plain")

    # decompress GZipped responses if not enabled
    if content and response.getheader('Content-Encoding') == 'gzip':
        from StringIO import StringIO
        import gzip
        buf = StringIO(content)
        f = gzip.GzipFile(fileobj=buf)
        content = f.read()

    if response_callback:
        kwargs = {} if not kwargs else kwargs
        kwargs.update({
            'response': response,
            'content': content,
            'status': status,
            'content_type': content_type
        })
        return response_callback(**kwargs)
    else:
        # If we get a redirect, let's add a useful message.
        if status in (301, 302, 303, 307):
            _response = HttpResponse(('This proxy does not support redirects. The server in "%s" '
                                     'asked for a redirect to "%s"' % (url, response.getheader('Location'))),
                                     status=status,
                                     content_type=content_type
                                    )
            _response['Location'] = response.getheader('Location')
            return _response
        else:
            return HttpResponse(
                content=content,
                status=status,
                content_type=content_type)
