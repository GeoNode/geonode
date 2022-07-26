#########################################################################
#
# Copyright (C) 2022 OSGeo
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
from django.urls import reverse
from geonode.resource.models import ExecutionRequest
from geonode.tests.base import GeoNodeBaseTestSupport


class ExecutionRequestApi(GeoNodeBaseTestSupport):
    #  loading test thesausuri and initial data
    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json',
        "test_thesaurus.json"
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.superuser, _ = get_user_model().objects.get_or_create(
            username='superuser',
            password="secret",
            is_active=True,
            is_superuser=True
        )
        cls.emmett_brown, _ = get_user_model().objects.get_or_create(
            username='emmett_brown',
            password="secret",
            is_active=True,
        )

        cls.superuser_request_delete = ExecutionRequest.objects.create(
            user=cls.superuser,
            func_name='foo',
            action="delete",
            input_params={},
            name="ReadableName"
        )

        cls.superuser_request_copy = ExecutionRequest.objects.create(
            user=cls.superuser,
            func_name='foo',
            action="copy",
            input_params={},
            name="ReadableName"
        )

        cls.emmett_brown_request = ExecutionRequest.objects.create(
            user=cls.emmett_brown,
            func_name='bar',
            action="copy",
            input_params={},
            name="ReadableName"
        )
        cls.url = reverse('executionrequest-list')
        cls.filtered_url = f"{reverse('executionrequest-list')}?filter{{action}}=delete"

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.superuser_request_delete.delete()
        cls.superuser_request_copy.delete()
        cls.emmett_brown_request.delete()
        cls.superuser.delete()
        cls.emmett_brown.delete()

    def test_endpoint_needs_login(self):
        response = self.client.get(self.url)
        self.assertEqual(403, response.status_code)

    def test_endpoint_will_accept_get(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)
        self.assertEqual(200, response.status_code)

    def test_endpoint_will_not_accept_post(self):
        self.client.force_login(self.superuser)
        response = self.client.post(self.url)
        self.assertEqual(405, response.status_code)

    def test_endpoint_will_not_accept_put(self):
        self.client.force_login(self.superuser)
        response = self.client.put(self.url)
        self.assertEqual(405, response.status_code)

    def test_endpoint_will_not_accept_patch(self):
        self.client.force_login(self.superuser)
        response = self.client.patch(self.url)
        self.assertEqual(405, response.status_code)

    def test_endpoint_will_return_the_user_data_emmett_brown(self):
        self.client.force_login(self.emmett_brown)
        response = self.client.get(self.url)

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.json().get("total", 0))

    def test_endpoint_will_return_the_user_data_superuser(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.url)

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.json().get("total", 0))

    def test_endpoint_will_return_the_user_data_superuser_with_filters(self):
        self.client.force_login(self.superuser)
        response = self.client.get(self.filtered_url)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.json().get("total", 0))
