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
import tempfile
import traceback

from slugify import slugify
from urlparse import urlparse, urlsplit, urljoin

from django.conf import settings
from django.http import HttpResponse
from django.utils.http import is_safe_url
from django.http.request import validate_host
from django.views.generic import View
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
                           zip_dir,
                           http_client,
                           json_response)
from geonode.base.auth import (extend_token,
                               get_or_create_token,
                               get_token_from_auth_header,
                               get_token_object_from_session)
from geonode.base.enumerations import LINK_TYPES as _LT

from geonode import geoserver, qgis_server  # noqa

TIMEOUT = 300

LINK_TYPES = [L for L in _LT if L.startswith("OGC:")]

logger = logging.getLogger(__name__)

ows_regexp = re.compile(
    r"^(?i)(version)=(\d\.\d\.\d)(?i)&(?i)request=(?i)(GetCapabilities)&(?i)service=(?i)(\w\w\w)$")


def get_headers(request, url, raw_url, allowed_hosts=[]):
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
    site_url = urlsplit(settings.SITEURL)
    allowed_hosts += [url.hostname]
    # We want to convert HTTP_AUTH into a Beraer Token only when hitting the local GeoServer
    if site_url.hostname in allowed_hosts:
        # we give precedence to obtained from Aithorization headers
        if 'HTTP_AUTHORIZATION' in request.META:
            auth_header = request.META.get(
                'HTTP_AUTHORIZATION',
                request.META.get('HTTP_AUTHORIZATION2'))
            if auth_header:
                headers['Authorization'] = auth_header
                access_token = get_token_from_auth_header(auth_header, create_if_not_exists=True)
        # otherwise we check if a session is active
        elif request and request.user.is_authenticated:
            access_token = get_token_object_from_session(request.session)

            # we extend the token in case the session is active but the token expired
            if access_token and access_token.is_expired():
                extend_token(access_token)
            else:
                access_token = get_or_create_token(request.user)

    if access_token:
        headers['Authorization'] = 'Bearer %s' % access_token

    pragma = "no-cache"
    referer = request.META[
        "HTTP_REFERER"] if "HTTP_REFERER" in request.META else \
        "{scheme}://{netloc}/".format(scheme=site_url.scheme,
                                      netloc=site_url.netloc)
    encoding = request.META["HTTP_ACCEPT_ENCODING"] if "HTTP_ACCEPT_ENCODING" in request.META else "gzip"
    headers.update({"Pragma": pragma,
                    "Referer": referer,
                    "Accept-encoding": encoding,
    })

    return (headers, access_token)


@requires_csrf_token
def proxy(request, url=None, response_callback=None,
          sec_chk_hosts=True, sec_chk_rules=True, timeout=None,
          allowed_hosts=[], **kwargs):
    # Request default timeout
    if not timeout:
        timeout = TIMEOUT

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
    headers, access_token = get_headers(request, url, raw_url, allowed_hosts=allowed_hosts)

    # Inject access_token if necessary
    parsed = urlparse(raw_url)
    parsed._replace(path=locator.encode('utf8'))

    _url = parsed.geturl()

    if request.method == "GET" and access_token and 'access_token' not in _url:
        query_separator = '&' if '?' in _url else '?'
        _url = ('%s%saccess_token=%s' %
                (_url, query_separator, access_token))

    response, content = http_client.request(_url,
                                            method=request.method,
                                            data=request.body,
                                            headers=headers,
                                            timeout=timeout,
                                            user=request.user)
    content = response.content or response.reason
    status = response.status_code
    content_type = response.headers.get('Content-Type')

    # decompress GZipped responses if not enabled
    # if content and response and response.getheader('Content-Encoding') == 'gzip':
    if content and content_type and content_type == 'gzip':
        from StringIO import StringIO
        import gzip
        buf = StringIO(content)
        f = gzip.GzipFile(fileobj=buf)
        content = f.read()

    if response and response_callback:
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
        if status and status in (301, 302, 303, 307):
            _response = HttpResponse(('This proxy does not support redirects. The server in "%s" '
                                      'asked for a redirect to "%s"' % (url, response.getheader('Location'))),
                                     status=status,
                                     content_type=content_type
                                     )
            _response['Location'] = response.getheader('Location')
            return _response
        else:
            def _get_message(text):
                _s = text.decode("utf-8", "replace")
                try:
                    found = re.search('<b>Message</b>(.+?)</p>', _s).group(1).strip()
                except BaseException:
                    found = _s
                return found

            return HttpResponse(
                content=content,
                reason=_get_message(content) if status not in (200, 201) else None,
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

                        # Collecting headers and cookies
                        headers, access_token = get_headers(request, urlsplit(s.sld_url), s.sld_url)

                        response, content = http_client.get(
                            s.sld_url,
                            headers=headers,
                            timeout=TIMEOUT,
                            user=request.user)
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
                    link_name = slugify(link.name)
                    link_file = os.path.join(target_md_folder, "".join([link_name, ".%s" % link.extension]))
                    if link.link_type in ('data'):
                        # Skipping 'data' download links
                        continue
                    elif link.link_type in ('metadata', 'image'):
                        # Dumping metadata files and images
                        link_file = open(link_file, "wb")
                        try:
                            # Collecting headers and cookies
                            headers, access_token = get_headers(request, urlsplit(link.url), link.url)

                            response, raw = http_client.get(
                                link.url,
                                stream=True,
                                headers=headers,
                                timeout=TIMEOUT,
                                user=request.user)
                            raw.decode_content = True
                            shutil.copyfileobj(raw, link_file)
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


class OWSListView(View):

    def get(self, request):
        from geonode.geoserver import ows
        out = {'success': True}
        data = []
        out['data'] = data
        # per-layer links
        # for link in Link.objects.filter(link_type__in=LINK_TYPES):  # .distinct('url'):
        #     data.append({'url': link.url, 'type': link.link_type})
        data.append({'url': ows._wcs_get_capabilities(), 'type': 'OGC:WCS'})
        data.append({'url': ows._wfs_get_capabilities(), 'type': 'OGC:WFS'})
        data.append({'url': ows._wms_get_capabilities(), 'type': 'OGC:WMS'})

        # catalogue from configuration
        for catname, catconf in settings.CATALOGUE.items():
            data.append({'url': catconf['URL'], 'type': 'OGC:CSW'})
        # main site url
        data.append({'url': settings.SITEURL, 'type': 'WWW:LINK'})
        return json_response(out)
