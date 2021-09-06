#########################################################################
#
# Copyright (C) 2021 OSGeo
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
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .models import ManagementCommandJob
from .utils import run_management_command


class ManagementCommandsTestCase(APITestCase):
    def setUp(self):
        self.resource_url = "/api/v2/management/"
        self.admin = get_user_model().objects.create_superuser(
            username="admin",
            password="admin",
            email="admin@geonode.org",
        )
        self.non_admin_user = get_user_model().objects.create_user(
            username="some_user",
            password="some_password",
            email="some_user@geonode.org",
        )
        self.client.force_authenticate(self.admin)

    def test_management_commands_list(self):
        expected_payload = {
            "success": True,
            "error": None,
            "data": ['ping_mngmt_commands_http'],
        }
        response = self.client.get(self.resource_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_payload)

    def test_management_commands_list_forbidden(self):
        self.client.force_authenticate(self.non_admin_user)
        response = self.client.get(self.resource_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_management_commands_detail(self):
        cmd_name = "ping_mngmt_commands_http"
        resource_url = f"/api/v2/management/{cmd_name}/"
        response = self.client.get(resource_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertTrue(response_json['success'])
        self.assertIn(cmd_name, response_json['data'])

    def test_management_commands_detail_not_found(self):
        cmd_name = "some_unavaliable_command"
        resource_url = f"/api/v2/management/{cmd_name}/"
        response = self.client.get(resource_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("geonode.mngmt_commands_http.tasks.run_management_command_async")
    def test_management_commands_create(self, mocked_async_task):
        cmd_name = "ping_mngmt_commands_http"
        resource_url = f"/api/v2/management/{cmd_name}/"
        response = self.client.post(resource_url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        self.assertTrue(response_json['success'])
        self.assertEqual(response_json['data']["command"], cmd_name)
        self.assertEqual(
            response_json['data']["status"], ManagementCommandJob.QUEUED
        )
        mocked_async_task.delay.assert_called_once()

    @patch("geonode.mngmt_commands_http.tasks.run_management_command_async")
    def test_management_commands_create_autostart_off(self, mocked_async_task):
        cmd_name = "ping_mngmt_commands_http"
        resource_url = f"/api/v2/management/{cmd_name}/"
        response = self.client.post(resource_url, data={"autostart": "false"})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json()['data']["status"], ManagementCommandJob.CREATED
        )
        mocked_async_task.delay.assert_not_called()

    def test_management_commands_create_not_allowed(self):
        resource_url = "/api/v2/management/"
        response = self.client.post(resource_url)
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def test_management_commands_create_not_found(self):
        cmd_name = "some_unavaliable_command"
        resource_url = f"/api/v2/management/{cmd_name}/"
        response = self.client.post(resource_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_management_commands_create_bad_request(self):
        cmd_name = "ping_mngmt_commands_http"
        resource_url = f"/api/v2/management/{cmd_name}/"
        response = self.client.post(resource_url, data={"args": ["--help"]})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class JobRunnerTestCase(APITestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="admin",
            password="admin",
            email="admin@geonode.org",
        )
        self.job = ManagementCommandJob.objects.create(
            command="ping_mngmt_commands_http",
            app_name="mngmt_commands_http",
            user=self.admin,
            status=ManagementCommandJob.CREATED,
        )

    def test_run_management_command(self):
        run_management_command(self.job.id)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, ManagementCommandJob.FINISHED)
        self.assertIn("pong", self.job.output_message)
