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

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
import json
import os
import io
import gisdata
import zipfile

try:
    from unittest.mock import MagicMock
except ImportError:
    from mock import MagicMock

from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from geonode import geoserver
from geonode.base.models import Link
from geonode.layers.models import Layer
from geonode.layers.utils import file_upload
from geonode.decorators import on_ogc_backend
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.populate_test_data import create_models

TEST_DOMAIN = '.github.com'
TEST_URL = f'https://help{TEST_DOMAIN}/'


class ProxyTest(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        self.maxDiff = None
        self.admin = get_user_model().objects.get(username='admin')

        # FIXME(Ariel): These tests do not work when the computer is offline.
        self.proxy_url = '/proxy/'
        self.url = TEST_URL

    @override_settings(DEBUG=True, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is True, all hosts pass the proxy."""
        response = self.client.get(f'{self.proxy_url}?url={self.url}')
        # 404 - NOT FOUND
        if response.status_code != 404:
            self.assertTrue(response.status_code in (200, 301))

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_not_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        response = self.client.get(f'{self.proxy_url}?url={self.url}')
        # 404 - NOT FOUND
        if response.status_code != 404:
            self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=('.google.com',))
    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=(TEST_DOMAIN,))
    def test_proxy_allowed_host(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        response = self.client.get(f'{self.proxy_url}?url={self.url}')
        # 404 - NOT FOUND
        if response.status_code != 404:
            self.assertTrue(response.status_code in (200, 301))

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=())
    def test_validate_remote_services_hosts(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 200
        for Remote Services hosts."""
        from geonode.services.models import Service
        from geonode.services.enumerations import WMS, INDEXED
        Service.objects.get_or_create(
            type=WMS,
            name='Bogus',
            title='Pocus',
            owner=self.admin,
            method=INDEXED,
            base_url='http://bogus.pocus.com/ows')
        response = self.client.get(
            f'{self.proxy_url}?url=http://bogus.pocus.com/ows/wms?request=GetCapabilities')
        # 200 - FOUND
        self.assertTrue(response.status_code in (200, 301))

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=('.example.org',))
    def test_relative_urls(self):
        """Proxying to a URL with a relative path element should normalise the path into
        an absolute path before calling the remote URL."""
        import geonode.proxy.views

        class Response:
            status_code = 200
            content = 'Hello World'
            headers = {'Content-Type': 'text/html'}

        request_mock = MagicMock()
        request_mock.return_value = (Response(), None)

        geonode.proxy.views.http_client.request = request_mock
        url = "http://example.org/test/test/../../index.html"

        self.client.get(f'{self.proxy_url}?url={url}')
        assert request_mock.call_args[0][0] == 'http://example.org/index.html'

    def test_proxy_preserve_headers(self):
        """The GeoNode Proxy should preserve the original request headers."""
        import geonode.proxy.views

        _test_headers = {
            'Access-Control-Allow-Credentials': False,
            'Access-Control-Allow-Headers': 'Content-Type, Accept, Authorization, Origin, User-Agent',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, OPTIONS',
            'Cache-Control': 'public, must-revalidate, max-age = 30',
            'Connection': 'keep-alive',
            'Content-Language': 'en',
            'Content-Length': 116559,
            'Content-Type': 'image/tiff',
            'Content-Disposition': 'attachment; filename="filename.tif"',
            'Date': 'Fri, 05 Nov 2021 17: 19: 11 GMT',
            'Server': 'nginx/1.17.2',
            'Set-Cookie': 'sessionid = bogus-pocus; HttpOnly; Path=/; SameSite=Lax',
            'Strict-Transport-Security': 'max-age=3600; includeSubDomains',
            'Vary': 'Authorization, Accept-Language, Cookie, Origin',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block'
        }

        class Response:
            status_code = 200
            content = 'Hello World'
            headers = _test_headers

        request_mock = MagicMock()
        request_mock.return_value = (Response(), None)

        geonode.proxy.views.http_client.request = request_mock
        url = "http://example.org/test/test/../../image.tiff"

        response = self.client.get(f'{self.proxy_url}?url={url}')
        if hasattr(response, 'headers'):
            response_headers = response.headers
        else:
            response_headers = response._headers
        self.assertDictContainsSubset(
            dict(response_headers.copy()),
            {
                'content-type': ('Content-Type', 'text/plain'),
                'vary': ('Vary', 'Authorization, Accept-Language, Cookie, Origin'),
                'x-content-type-options': ('X-Content-Type-Options', 'nosniff'),
                'x-xss-protection': ('X-XSS-Protection', '1; mode=block'),
                'x-frame-options': ('X-Frame-Options', 'SAMEORIGIN'),
                'content-language': ('Content-Language', 'en'),
                'content-length': ('Content-Length', '119')
            }
        )


class DownloadResourceTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        create_models(type='layer')

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_download_url(self):
        layer = Layer.objects.all().first()
        self.client.login(username='admin', password='admin')
        # ... all should be good
        response = self.client.get(reverse('download', args=(layer.id,)))
        # Espected 404 since there are no files available for this layer
        self.assertEqual(response.status_code, 404)
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        data = content
        self.assertTrue(
            "No files have been found for this resource. Please, contact a system administrator." in data)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_download_files(self):
        admin = get_user_model().objects.get(username="admin")
        # upload a shapefile
        shp_file = os.path.join(
            gisdata.VECTOR_DATA,
            'san_andres_y_providencia_poi.shp')
        layer = file_upload(
            shp_file,
            name="san_andres_y_providencia_poi",
            user=admin,
            overwrite=True,
        )
        self.client.login(username='admin', password='admin')

        response = self.client.get(reverse('download', args=(layer.id,)))
        # headers and status assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('content-type'), "application/zip")
        self.assertEqual(response.get('content-disposition'), 'attachment; filename="san_andres_y_providencia_poi.zip"')
        # Inspect content
        zip_content = io.BytesIO(b"".join(response.streaming_content))
        zip = zipfile.ZipFile(zip_content)
        zip_files = zip.namelist()
        self.assertEqual(len(zip_files), 11)
        self.assertIn(".metadata/", "".join(zip_files))
        self.assertIn(".shp", "".join(zip_files))
        self.assertIn(".dbf", "".join(zip_files))
        self.assertIn(".shx", "".join(zip_files))
        self.assertIn(".prj", "".join(zip_files))


class OWSApiTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        create_models(type='layer')
        # prepare some WMS endpoints
        q = Link.objects.all()
        for lyr in q[:3]:
            lyr.link_type = 'OGC:WMS'
            lyr.save()

    def test_ows_api(self):
        url = '/api/ows_endpoints/'
        q = Link.objects.filter(link_type__startswith="OGC:")
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        content = resp.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        data = json.loads(content)
        self.assertTrue(len(data['data']), q.count())
