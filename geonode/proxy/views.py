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
import gzip
import io
import json
import logging
import re
import traceback
from distutils.version import StrictVersion
from urllib.parse import urljoin, urlparse, urlsplit

import zipstream
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.forms.models import model_to_dict
from django.http import HttpResponse, StreamingHttpResponse
from django.http.request import validate_host
from django.template import loader
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import requires_csrf_token
from django.views.generic import View
from hyperlink import URL
from slugify import slugify

from geonode import geoserver  # noqa
from geonode.base import register_event
from geonode.base.enumerations import LINK_TYPES as _LT
from geonode.base.models import Link
from geonode.layers.models import Layer, LayerFile
from geonode.utils import (
    check_ogc_backend,
    get_headers,
    http_client,
    json_response,
    json_serializer_producer,
    resolve_object,
)

BUFFER_CHUNK_SIZE = 64 * 1024

TIMEOUT = 30

LINK_TYPES = [L for L in _LT if L.startswith("OGC:")]

logger = logging.getLogger(__name__)

storage = FileSystemStorage()

ows_regexp = re.compile(
    r"^(?i)(version)=(\d\.\d\.\d)(?i)&(?i)request=(?i)(GetCapabilities)&(?i)service=(?i)(\w\w\w)$")


@requires_csrf_token
def proxy(request, url=None, response_callback=None,
          sec_chk_hosts=True, sec_chk_rules=True, timeout=None,
          allowed_hosts=[], **kwargs):
    # Request default timeout
    from geonode.geoserver.helpers import ogc_server_settings
    if not timeout:
        timeout = getattr(ogc_server_settings, "TIMEOUT", TIMEOUT)

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
    scheme = str(url.scheme)
    locator = str(url.path)
    if url.query != "":
        locator += f"?{url.query}"
    if url.fragment != "":
        locator += f"#{url.fragment}"

    # White-Black Listing Hosts
    site_url = urlsplit(settings.SITEURL)
    if sec_chk_hosts and not settings.DEBUG:

        # Attach current SITEURL
        if site_url.hostname not in PROXY_ALLOWED_HOSTS:
            PROXY_ALLOWED_HOSTS += (site_url.hostname, )

        # Attach current hostname
        hostname = (
            ogc_server_settings.hostname,
        ) if ogc_server_settings else ()
        if hostname not in PROXY_ALLOWED_HOSTS:
            PROXY_ALLOWED_HOSTS += hostname

        # Check OWS regexp
        if url.query and ows_regexp.match(url.query):
            ows_tokens = ows_regexp.match(url.query).groups()
            if len(ows_tokens) == 4 and 'version' == ows_tokens[0] and StrictVersion(
                    ows_tokens[1]) >= StrictVersion("1.0.0") and StrictVersion(
                        ows_tokens[1]) <= StrictVersion("3.0.0") and ows_tokens[2].lower() in (
                            'getcapabilities') and ows_tokens[3].upper() in ('OWS', 'WCS', 'WFS', 'WMS', 'WPS', 'CSW'):
                if url.hostname not in PROXY_ALLOWED_HOSTS:
                    PROXY_ALLOWED_HOSTS += (url.hostname, )

        # Check Remote Services base_urls
        from geonode.services.models import Service
        for _s in Service.objects.all():
            _remote_host = urlsplit(_s.base_url).hostname
            PROXY_ALLOWED_HOSTS += (_remote_host, )

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
    if parsed.netloc == site_url.netloc and scheme != site_url.scheme:
        parsed = parsed._replace(scheme=site_url.scheme)

    _url = parsed.geturl()

    # Some clients / JS libraries generate URLs with relative URL paths, e.g.
    # "http://host/path/path/../file.css", which the requests library cannot
    # currently handle (https://github.com/kennethreitz/requests/issues/2982).
    # We parse and normalise such URLs into absolute paths before attempting
    # to proxy the request.
    _url = URL.from_text(_url).normalize().to_text()

    if request.method == "GET" and access_token and 'access_token' not in _url:
        query_separator = '&' if '?' in _url else '?'
        _url = f'{_url}{query_separator}access_token={access_token}'

    _data = request.body.decode('utf-8')

    # Avoid translating local geoserver calls into external ones
    if check_ogc_backend(geoserver.BACKEND_PACKAGE):
        from geonode.geoserver.helpers import ogc_server_settings
        _url = _url.replace(
            f'{settings.SITEURL}geoserver',
            ogc_server_settings.LOCATION.rstrip('/'))
        _data = _data.replace(
            f'{settings.SITEURL}geoserver',
            ogc_server_settings.LOCATION.rstrip('/'))

    response, content = http_client.request(
        _url,
        method=request.method,
        data=_data.encode('utf-8'),
        headers=headers,
        timeout=timeout,
        user=request.user)
    if response is None:
        return HttpResponse(
            content=content,
            reason=content,
            status=500)
    content = response.content or response.reason
    status = response.status_code
    response_headers = response.headers
    content_type = response.headers.get('Content-Type')

    if status >= 400:
        _response = HttpResponse(
            content=content,
            reason=content,
            status=status,
            content_type=content_type)
        return fetch_response_headers(_response, response_headers)

    # decompress GZipped responses if not enabled
    # if content and response and response.getheader('Content-Encoding') == 'gzip':
    if content and content_type and content_type == 'gzip':
        buf = io.BytesIO(content)
        with gzip.GzipFile(fileobj=buf) as f:
            content = f.read()
        buf.close()

    PLAIN_CONTENT_TYPES = [
        'text',
        'plain',
        'html',
        'json',
        'xml',
        'gml'
    ]
    for _ct in PLAIN_CONTENT_TYPES:
        if content_type and _ct in content_type and not isinstance(content, str):
            try:
                content = content.decode()
                break
            except Exception:
                pass

    if response and response_callback:
        kwargs = {} if not kwargs else kwargs
        kwargs.update({
            'response': response,
            'content': content,
            'status': status,
            'response_headers': response_headers,
            'content_type': content_type
        })
        return response_callback(**kwargs)
    else:
        # If we get a redirect, let's add a useful message.
        if status and status in (301, 302, 303, 307):
            _response = HttpResponse((f"This proxy does not support redirects. The server in '{url}' "
                                      f"asked for a redirect to '{response.getheader('Location')}'"),
                                     status=status,
                                     content_type=content_type
                                     )
            _response['Location'] = response.getheader('Location')
            return fetch_response_headers(_response, response_headers)
        else:
            def _get_message(text):
                _s = text
                if isinstance(text, bytes):
                    _s = text.decode("utf-8", "replace")
                try:
                    found = re.search('<b>Message</b>(.+?)</p>', _s).group(1).strip()
                except Exception:
                    found = _s
                return found

            _response = HttpResponse(
                content=content,
                reason=_get_message(content) if status not in (200, 201) else None,
                status=status,
                content_type=content_type)
            return fetch_response_headers(_response, response_headers)


def download(request, resourceid, sender=Layer):

    _not_authorized = _("You are not authorized to download this resource.")
    _not_permitted = _("You are not permitted to save or edit this resource.")
    _no_files_found = _("No files have been found for this resource. Please, contact a system administrator.")

    instance = resolve_object(request,
                              sender,
                              {'pk': resourceid},
                              permission='base.download_resourcebase',
                              permission_msg=_not_permitted)

    if isinstance(instance, Layer):
        layer_files = []
        file_list = []  # Store file info to be returned
        try:
            upload_session = instance.get_upload_session()
            if upload_session:
                layer_files = [
                    item for idx, item in enumerate(LayerFile.objects.filter(upload_session=upload_session))]
                if layer_files:
                    # Copy all Layer related files into a temporary folder
                    for lyr in layer_files:
                        if storage.exists(str(lyr.file)):
                            geonode_layer_path = storage.path(str(lyr.file))
                            file_list.append({
                                "zip_folder": "",
                                "name": lyr.file.name.split('/')[-1],
                                "data_src_file": geonode_layer_path,
                            })
                        else:
                            return HttpResponse(
                                loader.render_to_string(
                                    '401.html',
                                    context={
                                        'error_title': _("No files found."),
                                        'error_message': _no_files_found
                                    },
                                    request=request), status=404)

            # Check we can access the original files
            if not layer_files:
                return HttpResponse(
                    loader.render_to_string(
                        '401.html',
                        context={
                            'error_title': _("No files found."),
                            'error_message': _no_files_found
                        },
                        request=request), status=404)

            # Let's check for associated SLD files (if any)
            try:
                for s in instance.styles.all():
                    sld_file_name = "".join([s.name, ".sld"])
                    file_list.append({
                        "zip_folder": "",
                        "name": sld_file_name,
                        "data_str": s.sld_body.strip(),
                    })
                    try:
                        # Collecting headers and cookies
                        headers, access_token = get_headers(request, urlsplit(s.sld_url), s.sld_url)

                        response, content = http_client.get(
                            s.sld_url,
                            headers=headers,
                            timeout=TIMEOUT,
                            user=request.user)
                        sld_remote_content = response.text
                        remote_sld_file_name = "".join([s.name, "_remote.sld"])
                        file_list.append({
                            "zip_folder": "",
                            "name": remote_sld_file_name,
                            "data_str": sld_remote_content,
                        })
                    except Exception:
                        traceback.print_exc()
                        tb = traceback.format_exc()
                        logger.debug(tb)
            except Exception:
                traceback.print_exc()
                tb = traceback.format_exc()
                logger.debug(tb)

            # Let's dump metadata
            try:
                dump_file_name = "".join([instance.name, ".dump"])
                serialized_obj = json_serializer_producer(model_to_dict(instance))
                file_list.append({
                    "zip_folder": ".metadata/",
                    "name": dump_file_name,
                    "data_str": json.dumps(serialized_obj),
                })
                links = Link.objects.filter(resource=instance.resourcebase_ptr)
                for link in links:
                    link_name = slugify(link.name)
                    link_file_name = "".join([link_name, f".{link.extension}"])
                    link_file_obj = None

                    if link.link_type in ('data'):
                        # Skipping 'data' download links
                        continue
                    elif link.link_type in ('metadata', 'image'):
                        # Dumping metadata files and images
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
                            if raw and raw is not None:
                                link_file_obj = {
                                    "zip_folder": ".metadata/",
                                    "name": link_file_name,
                                    "data_iter": raw,
                                }
                        except Exception:
                            traceback.print_exc()
                            tb = traceback.format_exc()
                            logger.debug(tb)
                    elif link.link_type.startswith('OGC'):
                        # Dumping OGC/OWS links
                        link_file_obj = {
                            "zip_folder": ".metadata/",
                            "name": link_file_name,
                            "data_str": link.url.strip(),
                        }
                    # Add file_info to the file list
                    if link_file_obj is not None:
                        file_list.append(link_file_obj)
            except Exception:
                traceback.print_exc()
                tb = traceback.format_exc()
                logger.debug(tb)

            # ZIP everything and return
            target_file_name = "".join([instance.name, ".zip"])

            target_zip = zipstream.ZipFile(mode='w', compression=zipstream.ZIP_DEFLATED, allowZip64=True)

            # Iterable: Needed when the file_info has it's data as a stream
            def _iterable(source_iter):
                while True:
                    buf = source_iter.read(BUFFER_CHUNK_SIZE)
                    if not buf:
                        break
                    yield buf

            # Add files to zip
            for file_info in file_list:
                zip_file_name = "".join([file_info['zip_folder'], file_info['name']])
                # The zip can be built from 3 data sources: str, iterable or a file path
                if 'data_str' in file_info and file_info['data_str'] is not None:
                    target_zip.writestr(arcname=zip_file_name, data=bytes(file_info['data_str'], 'utf-8'))
                elif 'data_iter' in file_info and file_info['data_iter'] is not None:
                    target_zip.write_iter(arcname=zip_file_name, iterable=_iterable(file_info['data_iter']))
                elif 'data_src_file' in file_info and file_info['data_src_file'] is not None:
                    target_zip.write(filename=file_info['data_src_file'], arcname=zip_file_name)

            register_event(request, 'download', instance)

            # Streaming content response
            response = StreamingHttpResponse(target_zip, content_type='application/zip')
            response['Content-Disposition'] = f'attachment; filename="{target_file_name}"'
            return response
        except NotImplementedError:
            traceback.print_exc()
            tb = traceback.format_exc()
            logger.debug(tb)
            return HttpResponse(
                loader.render_to_string(
                    '401.html',
                    context={
                        'error_title': _("No files found."),
                        'error_message': _no_files_found
                    },
                    request=request), status=404)
    return HttpResponse(
        loader.render_to_string(
            '401.html',
            context={
                'error_title': _("Not Authorized"),
                'error_message': _not_authorized
            },
            request=request), status=403)


class OWSListView(View):

    def get(self, request):
        from geonode.geoserver import ows
        out = {'success': True}
        data = []
        out['data'] = data
        # WMS
        _raw_url = ows._wms_get_capabilities()
        _url = urlsplit(_raw_url)
        headers, access_token = get_headers(request, _url, _raw_url)
        if access_token:
            _j = '&' if _url.query else '?'
            _raw_url = _j.join([_raw_url, f'access_token={access_token}'])
        data.append({'url': _raw_url, 'type': 'OGC:WMS'})

        # WCS
        _raw_url = ows._wcs_get_capabilities()
        _url = urlsplit(_raw_url)
        headers, access_token = get_headers(request, _url, _raw_url)
        if access_token:
            _j = '&' if _url.query else '?'
            _raw_url = _j.join([_raw_url, f'access_token={access_token}'])
        data.append({'url': _raw_url, 'type': 'OGC:WCS'})

        # WFS
        _raw_url = ows._wfs_get_capabilities()
        _url = urlsplit(_raw_url)
        headers, access_token = get_headers(request, _url, _raw_url)
        if access_token:
            _j = '&' if _url.query else '?'
            _raw_url = _j.join([_raw_url, f'access_token={access_token}'])
        data.append({'url': _raw_url, 'type': 'OGC:WFS'})

        # catalogue from configuration
        for catname, catconf in settings.CATALOGUE.items():
            # CSW
            _raw_url = catconf['URL']
            _url = urlsplit(_raw_url)
            headers, access_token = get_headers(request, _url, _raw_url)
            if access_token:
                _j = '&' if _url.query else '?'
                _raw_url = _j.join([_raw_url, f'access_token={access_token}'])
            data.append({'url': _raw_url, 'type': 'OGC:CSW'})

        # main site url
        data.append({'url': settings.SITEURL, 'type': 'WWW:LINK'})
        return json_response(out)


_hoppish = {
    'connection', 'keep-alive', 'proxy-authenticate',
    'proxy-authorization', 'te', 'trailers', 'transfer-encoding',
    'upgrade', 'content-length', 'content-encoding'
}.__contains__


def is_hop_by_hop(header_name):
    """Return true if 'header_name' is an HTTP/1.1 "Hop-by-Hop" header"""
    return _hoppish(header_name.lower())


def fetch_response_headers(response, response_headers):
    if response_headers:
        for _header in response_headers:
            if not is_hop_by_hop(_header):
                if hasattr(response, 'headers') and _header.lower() not in [_k.lower() for _k in response.headers.keys()]:
                    response.headers[_header] = response_headers.get(_header)
                elif hasattr(response, '_headers') and _header.lower() not in [_k.lower() for _k in response._headers.keys()]:
                    response._headers[_header] = (_header, response_headers.get(_header))
    return response
