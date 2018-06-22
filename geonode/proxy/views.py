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

import os
import re
import json
import shutil
import logging
import requests
import tempfile
import traceback

from slugify import Slugify
from httplib import HTTPConnection, HTTPSConnection
from urlparse import urlsplit, urljoin
from django.conf import settings
from django.http import HttpResponse
from django.utils.http import is_safe_url
from django.http.request import validate_host
from django.views.decorators.csrf import requires_csrf_token
from django.middleware.csrf import get_token
from distutils.version import StrictVersion
from django.utils.translation import ugettext as _
from django.core.files.storage import default_storage as storage
from geonode.base.models import Link
from geonode.layers.models import Layer, LayerFile
from geonode.utils import (resolve_object,
                           check_ogc_backend,
                           get_dir_time_suffix,
                           zip_dir)
from geonode import geoserver, qgis_server  # noqa

TIMEOUT = 30

logger = logging.getLogger(__name__)

custom_slugify = Slugify(separator='_')

ows_regexp = re.compile(
    "^(?i)(version)=(\d\.\d\.\d)(?i)&(?i)request=(?i)(GetCapabilities)&(?i)service=(?i)(\w\w\w)$")


@requires_csrf_token
def proxy(request, url=None, response_callback=None,
          sec_chk_hosts=True, sec_chk_rules=True, **kwargs):
    # Security rules and settings
    PROXY_ALLOWED_HOSTS = getattr(settings, 'PROXY_ALLOWED_HOSTS', ())

    # Sanity url checks
    if 'url' not in request.GET and not url:
        return HttpResponse("The proxy service requires a URL-encoded URL as a parameter.",
                            status=400,
                            content_type="text/plain"
                            )

    raw_url = url or request.GET['url']
    raw_url = urljoin(
        settings.SITEURL,
        raw_url) if raw_url.startswith("/") else raw_url
    url = urlsplit(raw_url)
    locator = str(url.path)
    if url.query != "":
        locator += '?' + url.query
    if url.fragment != "":
        locator += '#' + url.fragment

    access_token = None
    if request and 'access_token' in request.session:
        access_token = request.session['access_token']

    # White-Black Listing Hosts
    if sec_chk_hosts and not settings.DEBUG:
        site_url = urlsplit(settings.SITEURL)
        if site_url.hostname not in PROXY_ALLOWED_HOSTS:
            PROXY_ALLOWED_HOSTS += (site_url.hostname, )

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            from geonode.geoserver.helpers import ogc_server_settings
            hostname = (
                ogc_server_settings.hostname,
            ) if ogc_server_settings else ()
            if hostname not in PROXY_ALLOWED_HOSTS:
                PROXY_ALLOWED_HOSTS += hostname

        if url.query and ows_regexp.match(url.query):
            ows_tokens = ows_regexp.match(url.query).groups()
            if len(ows_tokens) == 4 and 'version' == ows_tokens[0] and StrictVersion(
                    ows_tokens[1]) >= StrictVersion("1.0.0") and StrictVersion(
                        ows_tokens[1]) <= StrictVersion("3.0.0") and ows_tokens[2].lower() in (
                            'getcapabilities') and ows_tokens[3].upper() in ('OWS', 'WCS', 'WFS', 'WMS', 'WPS', 'CSW'):
                if url.hostname not in PROXY_ALLOWED_HOSTS:
                    PROXY_ALLOWED_HOSTS += (url.hostname, )

        if not validate_host(
                url.hostname, PROXY_ALLOWED_HOSTS):
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

    if settings.SESSION_COOKIE_NAME in request.COOKIES and is_safe_url(
            url=raw_url, host=url.hostname):
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
    if request and 'access_token' in request.session:
        access_token = request.session['access_token']

    if access_token:
        # TODO: Bearer is currently cutted of by Djano / GeoServer
        if request.method in ("POST", "PUT"):
            headers['Authorization'] = 'Bearer %s' % access_token
        if access_token and 'access_token' not in locator:
            query_separator = '&' if '?' in locator else '?'
            locator = ('%s%saccess_token=%s' %
                       (locator, query_separator, access_token))
    elif 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META.get(
            'HTTP_AUTHORIZATION',
            request.META.get('HTTP_AUTHORIZATION2'))
        if auth:
            headers['Authorization'] = auth

    site_url = urlsplit(settings.SITEURL)

    pragma = "no-cache"
    referer = request.META[
        "HTTP_REFERER"] if "HTTP_REFERER" in request.META else \
        "{scheme}://{netloc}/".format(scheme=site_url.scheme,
                                      netloc=site_url.netloc)
    encoding = request.META["HTTP_ACCEPT_ENCODING"] if "HTTP_ACCEPT_ENCODING" in request.META else "gzip"

    headers.update({"Pragma": pragma,
                    "Referer": referer,
                    "Accept-encoding": encoding, })

    if url.scheme == 'https':
        conn = HTTPSConnection(url.hostname, url.port)
    else:
        conn = HTTPConnection(url.hostname, url.port)
    conn.request(request.method, locator.encode('utf8'), request.body, headers)
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


def download(request, resourceid, sender=Layer):

    instance = resolve_object(request,
                              sender,
                              {'pk': resourceid},
                              permission='base.download_resourcebase',
                              permission_msg=_("You are not permitted to save or edit this resource."))

    if isinstance(instance, Layer):
        try:
            upload_session = instance.get_upload_session()
            layer_files = [item for idx, item in enumerate(LayerFile.objects.filter(upload_session=upload_session))]

            # Create Target Folder
            dirpath = tempfile.mkdtemp()
            dir_time_suffix = get_dir_time_suffix()
            target_folder = os.path.join(dirpath, dir_time_suffix)
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)

            # Copy all Layer related files into a temporary folder
            for l in layer_files:
                if storage.exists(l.file):
                    geonode_layer_path = storage.path(l.file)
                    base_filename, original_ext = os.path.splitext(geonode_layer_path)
                    shutil.copy2(geonode_layer_path, target_folder)

            # Let's check for associated SLD files (if any)
            try:
                for s in instance.styles.all():
                    sld_file_path = os.path.join(target_folder, "".join([s.name, ".sld"]))
                    sld_file = open(sld_file_path, "w")
                    sld_file.write(s.sld_body.strip())
                    sld_file.close()

                    try:
                        sld_file = open(sld_file_path, "r")
                        response = requests.get(s.sld_url, timeout=TIMEOUT)
                        sld_remote_content = response.text
                        sld_file_path = os.path.join(target_folder, "".join([s.name, "_remote.sld"]))
                        sld_file = open(sld_file_path, "w")
                        sld_file.write(sld_remote_content.strip())
                        sld_file.close()
                    except BaseException:
                        traceback.print_exc()
                        tb = traceback.format_exc()
                        logger.debug(tb)

            except BaseException:
                traceback.print_exc()
                tb = traceback.format_exc()
                logger.debug(tb)

            # Let's dump metadata
            target_md_folder = os.path.join(target_folder, ".metadata")
            if not os.path.exists(target_md_folder):
                os.makedirs(target_md_folder)

            try:
                links = Link.objects.filter(resource=instance.resourcebase_ptr)
                for link in links:
                    link_name = custom_slugify(link.name)
                    link_file = os.path.join(target_md_folder, "".join([link_name, ".%s" % link.extension]))
                    if link.link_type in ('data'):
                        # Skipping 'data' download links
                        continue
                    elif link.link_type in ('metadata', 'image'):
                        # Dumping metadata files and images
                        link_file = open(link_file, "wb")
                        try:
                            response = requests.get(link.url, stream=True, timeout=TIMEOUT)
                            response.raw.decode_content = True
                            shutil.copyfileobj(response.raw, link_file)
                        except BaseException:
                            traceback.print_exc()
                            tb = traceback.format_exc()
                            logger.debug(tb)
                        finally:
                            link_file.close()
                    elif link.link_type.startswith('OGC'):
                        # Dumping OGC/OWS links
                        link_file = open(link_file, "w")
                        link_file.write(link.url.strip())
                        link_file.close()
            except BaseException:
                traceback.print_exc()
                tb = traceback.format_exc()
                logger.debug(tb)

            # ZIP everything and return
            target_file_name = "".join([instance.name, ".zip"])
            target_file = os.path.join(dirpath, target_file_name)
            zip_dir(target_folder, target_file)
            response = HttpResponse(
                content=open(target_file),
                status=200,
                content_type="application/zip")
            response['Content-Disposition'] = 'attachment; filename="%s"' % target_file_name
            return response
        except NotImplementedError:
            traceback.print_exc()
            tb = traceback.format_exc()
            logger.debug(tb)
            return HttpResponse(
                json.dumps({
                    'error': 'file_not_found'
                }),
                status=404,
                content_type="application/json"
            )

    return HttpResponse(
        json.dumps({
            'error': 'unauthorized_request'
        }),
        status=403,
        content_type="application/json"
    )
