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

"""
This file demonstrates two different styles of tests (one doctest and one
unittest). These will both pass when you run "manage.py test".

Replace these with more appropriate tests for your application.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test.utils import override_settings


TEST_DOMAIN = '.github.com'
TEST_URL = 'https://help%s/' % TEST_DOMAIN


class ProxyTest(TestCase):

    def setUp(self):
        self.admin, created = get_user_model().objects.get_or_create(username='admin',
                                                                     password='admin',
                                                                     is_superuser=True)

        # FIXME(Ariel): These tests do not work when the computer is offline.
        self.url = TEST_URL

    @override_settings(DEBUG=True, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is True, all hosts pass the proxy."""
        response = self.client.get('/proxy?url=%s' % self.url, follow=True)
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_not_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        response = self.client.get('/proxy?url=%s' % self.url, follow=True)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=('.google.com',))
    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=(TEST_DOMAIN,))
    def test_proxy_allowed_host(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        response = self.client.get('/proxy?url=%s' % self.url, follow=True)
        self.assertEqual(response.status_code, 200)
