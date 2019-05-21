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
