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
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from django.test.utils import override_settings, str_prefix
from geonode.proxy.views import validate_host
from geonode.utils import ogc_server_settings

class ProxyTest(TestCase):

    def setUp(self):
        self.admin, created = User.objects.get_or_create(username='admin', password='admin', is_superuser=True)

    @override_settings(DEBUG=True, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is True, all hosts pass the proxy."""
        c = Client()
        response = c.get('/proxy?url=http://www.google.com', follow=True)
        self.assertEqual(response.status_code, 200)

    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=())
    def test_validate_host_disabled_not_in_debug(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        c = Client()
        response = c.get('/proxy?url=http://www.google.com', follow=True)
        self.assertEqual(response.status_code, 403)


    @override_settings(DEBUG=False, PROXY_ALLOWED_HOSTS=('.google.com',))
    def test_proxy_allowed_host(self):
        """If PROXY_ALLOWED_HOSTS is empty and DEBUG is False requests should return 403."""
        c = Client()
        response = c.get('/proxy?url=http://www.google.com', follow=True)
        self.assertEqual(response.status_code, 200)




