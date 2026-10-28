#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from geonode.security.auth_handlers import BasicAuthHandler
from geonode.sources.tests.utils import create_connection


class SourcesViewsTests(TestCase):
    """The pages are a thin client of the API: only the access to them is tested here, the flows in test_api"""

    # GeoNode drops sessions without an OAuth token, created on login from these apps
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    def setUp(self):
        self.staff = get_user_model().objects.create_user(username="sources_staff", password="password", is_staff=True)
        self.user = get_user_model().objects.create_user(username="sources_user", password="password")
        self.connection = create_connection()
        self.urls = (
            reverse("sources_connection_list"),
            reverse("sources_connection_create", args=["postgresql"]),
            reverse("sources_connection_detail", args=[self.connection.pk]),
        )

    def test_anonymous_should_be_sent_to_the_login_page(self):
        for _url in self.urls:
            with self.subTest(url=_url):
                self.assertEqual(302, self.client.get(_url).status_code)

    def test_user_should_be_denied_access(self):
        """A logged in user without staff rights gets a 403, not a redirect"""
        self.client.force_login(self.user)
        for _url in self.urls:
            with self.subTest(url=_url):
                self.assertEqual(403, self.client.get(_url).status_code)

    def test_staff_can_open_every_page(self):
        self.client.force_login(self.staff)
        for _url in self.urls:
            with self.subTest(url=_url):
                self.assertEqual(200, self.client.get(_url).status_code)

    def test_create_page_should_404_for_an_unknown_provider(self):
        self.client.force_login(self.staff)
        self.assertEqual(404, self.client.get(reverse("sources_connection_create", args=["unknown"])).status_code)

    def test_detail_page_should_404_for_an_auth_config_that_is_not_a_connection(self):
        """Only the AuthConfig of a source provider is a connection"""
        _other = BasicAuthHandler.create_auth_config({"username": "service", "password": "secret"})
        self.client.force_login(self.staff)
        self.assertEqual(404, self.client.get(reverse("sources_connection_detail", args=[_other.pk])).status_code)
