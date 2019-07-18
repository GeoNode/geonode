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

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
import json

from geonode.base.models import Link
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.populate_test_data import create_models

from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from mock import MagicMock


TEST_DOMAIN = '.github.com'
TEST_URL = 'https://help%s/' % TEST_DOMAIN


class ProxyTest(GeoNodeBaseTestSupport):

    def setUp(self):
        super(ProxyTest, self).setUp()
        self.admin = get_user_model().objects.get(username='admin')

        # FIXME(Ariel): These tests do not work when the computer is offline.
        self.proxy_url = '/proxy/'
        self.url = TEST_URL

    @override_settings(DEBUG=True, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is True, all hosts pass the proxy."""
        response = self.client.get('%s?url=%s' %
                                   (self.proxy_url, self.url))
        # 404 - NOT FOUND
        if response.status_code != 404:
            self.assertTrue(response.status_code in (200, 301))

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_not_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        response = self.client.get('%s?url=%s' %
                                   (self.proxy_url, self.url))
        # 404 - NOT FOUND
        if response.status_code != 404:
            self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=('.google.com',))
    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=(TEST_DOMAIN,))
    def test_proxy_allowed_host(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        response = self.client.get('%s?url=%s' %
                                   (self.proxy_url, self.url))
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
            '%s?url=%s' % (self.proxy_url, 'http://bogus.pocus.com/ows/wms?request=GetCapabilities'))
        # 200 - FOUND
        self.assertTrue(response.status_code in (200, 301))

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=('.example.org',))
    def test_relative_urls(self):
        """Proxying to a URL with a relative path element should normalise the path into
        an absolute path before calling the remote URL."""
        import geonode.proxy.views

        class Response(object):
            status_code = 200
            content = 'Hello World'
            headers = {'Content-Type': 'text/html'}

        request_mock = MagicMock()
        request_mock.return_value = (Response(), None)

        geonode.proxy.views.http_client.request = request_mock
        url = "http://example.org/test/test/../../index.html"

        self.client.get('%s?url=%s' % (self.proxy_url, url))
        assert request_mock.assert_called_once
        assert request_mock.call_args[0][0] == 'http://example.org/index.html'


class OWSApiTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(OWSApiTestCase, self).setUp()
        create_models(type='layer')
        # prepare some WMS endpoints
        q = Link.objects.all()
        for l in q[:3]:
            l.link_type = 'OGC:WMS'
            l.save()

    def test_ows_api(self):
        url = '/api/ows_endpoints/'
        q = Link.objects.filter(link_type__startswith="OGC:")
        self.assertEqual(q.count(), 3)
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertTrue(len(data['data']), q.count())
