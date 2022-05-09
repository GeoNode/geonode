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
from datetime import datetime
from django.conf import settings
from django.contrib.auth import get_user_model
from unittest.mock import patch
from geonode.management_commands_http.models import ManagementCommandJob
from geonode.management_commands_http.utils.job_runner import (
    run_management_command
)


class ManagementCommandsTestCase(APITestCase):
    def setUp(self):
        self.resource_list_url = "/api/v2/management/commands/"
        self.resource_details_url = "/api/v2/management/commands/{}/"
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
            "data": list(settings.MANAGEMENT_COMMANDS_EXPOSED_OVER_HTTP),
        }
        response = self.client.get(self.resource_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), expected_payload)

    def test_management_commands_list_forbidden(self):
        self.client.force_authenticate(self.non_admin_user)
        response = self.client.get(self.resource_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_management_commands_detail(self):
        cmd_name = "ping_mngmt_commands_http"
        response = self.client.get(self.resource_details_url.format(cmd_name))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertTrue(response_json["success"])
        self.assertIn(cmd_name, response_json["data"])

    def test_management_commands_detail_not_found(self):
        cmd_name = "some_unavaliable_command"
        response = self.client.get(self.resource_details_url.format(cmd_name))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("geonode.management_commands_http.utils.jobs.run_management_command_async")
    def test_management_commands_create(self, mocked_async_task):
        cmd_name = "ping_mngmt_commands_http"
        response = self.client.post(self.resource_details_url.format(cmd_name))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        self.assertTrue(response_json["success"])
        self.assertEqual(response_json["data"]["command"], cmd_name)
        self.assertEqual(
            response_json["data"]["status"], ManagementCommandJob.QUEUED
        )
        job_id = response_json["data"]["id"]
        mocked_async_task.delay.assert_called_once()
        mocked_async_task.delay.assert_called_with(job_id=job_id)

    @patch("geonode.management_commands_http.utils.jobs.run_management_command_async")
    def test_management_commands_create_autostart_off(self, mocked_async_task):
        cmd_name = "ping_mngmt_commands_http"
        response = self.client.post(
            self.resource_details_url.format(cmd_name),
            data={"autostart": False},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json()["data"]["status"], ManagementCommandJob.CREATED
        )
        mocked_async_task.delay.assert_not_called()

    def test_management_commands_create_without_command(self):
        response = self.client.post(self.resource_list_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("This field may not be null.", response.json()["errors"])

    def test_management_commands_create_not_found(self):
        cmd_name = "some_unavaliable_command"
        response = self.client.post(self.resource_details_url.format(cmd_name))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Command not found", response.content.decode())

    def test_management_commands_create_bad_request(self):
        cmd_name = "ping_mngmt_commands_http"
        response = self.client.post(
            self.resource_details_url.format(cmd_name),
            data={"args": ["--help"]},
            format="json",
        )
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


class ManagementCommandJobsTestCase(APITestCase):
    def setUp(self):
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

        self.job1 = ManagementCommandJob.objects.create(
            command="ping_mngmt_commands_http",
            app_name="management_commands_http",
            user=self.admin,
            args='["--sleep","1"]',
        )
        self.job2 = ManagementCommandJob.objects.create(
            command="ping_mngmt_commands_http",
            app_name="management_commands_http",
            user=self.admin,
        )
        self.job3 = ManagementCommandJob.objects.create(
            command="sync_geonode_layers",
            app_name="geoserver",
            user=self.admin,
        )

        self.resource_list_url = "/api/v2/management/jobs/"
        self.resource_list_by_cmd_url = "/api/v2/management/commands/{}/jobs/"

    def test_management_command_jobs_list(self):
        response = self.client.get(self.resource_list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        response_jobs = [job["id"] for job in response_json["data"]]
        self.assertEqual(response_json["total"], 3)
        self.assertIn(self.job1.id, response_jobs)
        self.assertIn(self.job2.id, response_jobs)
        self.assertIn(self.job3.id, response_jobs)

    def test_management_command_jobs_list_by_command(self):
        cmd_name = "ping_mngmt_commands_http"
        response = self.client.get(self.resource_list_by_cmd_url.format(cmd_name))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        response_jobs = [job["id"] for job in response_json["data"]]
        self.assertEqual(response_json["total"], 2)
        self.assertIn(self.job1.id, response_jobs)
        self.assertIn(self.job2.id, response_jobs)
        self.assertNotIn(self.job3.id, response_jobs)

    def test_management_command_jobs_list_forbidden(self):
        self.client.force_authenticate(self.non_admin_user)
        response = self.client.get(self.resource_list_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_management_command_job_detail(self):
        resource_url = f"/api/v2/management/jobs/{self.job1.id}/"
        response = self.client.get(resource_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(response_json["id"], self.job1.id)
        self.assertEqual(response_json["command"], self.job1.command)

    @patch("geonode.management_commands_http.views.get_celery_task_meta")
    def test_management_command_job_status(self, mocked_celery_task_meta):
        mocked_celery_task_meta.return_value = {
            "status": "some_value",
            "worker": "some_worker",
            "traceback": None,
            "result": ...,
            "date_done": datetime.now(),
        }
        cmd_name = "ping_mngmt_commands_http"
        resource_url = f"/api/v2/management/commands/{cmd_name}/jobs/{self.job1.id}/status/"
        response = self.client.get(resource_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(response_json["celery_task_meta"]["status"], "some_value")
        self.assertEqual(response_json["celery_task_meta"]["worker"], "some_worker")
        self.assertNotIn("result", response_json["celery_task_meta"])
        mocked_celery_task_meta.assert_called_once()
        mocked_celery_task_meta.assert_called_with(self.job1)

    @patch("geonode.management_commands_http.utils.jobs.run_management_command_async")
    def test_management_command_job_start(self, mocked_async_task):
        cmd_name = "ping_mngmt_commands_http"
        resource_url = f"/api/v2/management/commands/{cmd_name}/jobs/{self.job1.id}/start/"
        response = self.client.patch(resource_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_json = response.json()
        self.assertEqual(
            response_json["data"]["status"], ManagementCommandJob.QUEUED
        )
        mocked_async_task.delay.assert_called_once()
        mocked_async_task.delay.assert_called_with(job_id=self.job1.id)

    @patch("geonode.management_commands_http.utils.jobs.celery_app")
    def test_management_command_job_stop(self, mocked_celery_app):
        self.job2.celery_result_id = "73a412f6-70f7-4b6f-a8ae-152651e6a2f7"
        self.job2.save()
        cmd_name = "ping_mngmt_commands_http"
        resource_url = f"/api/v2/management/commands/{cmd_name}/jobs/{self.job2.id}/stop/"
        response = self.client.patch(resource_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mocked_celery_app.control.terminate.assert_called_once()
        mocked_celery_app.control.terminate.assert_called_with(self.job2.celery_result_id)

    @patch("geonode.management_commands_http.utils.jobs.run_management_command_async")
    def test_management_command_job_create(self, mocked_async_task):
        cmd_name = "ping_mngmt_commands_http"
        response = self.client.post(
            self.resource_list_url,
            data={"command": cmd_name},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response_json = response.json()
        self.assertTrue(response_json["success"])
        self.assertEqual(response_json["data"]["command"], "ping_mngmt_commands_http")
        self.assertEqual(
            response_json["data"]["status"], ManagementCommandJob.QUEUED
        )
        job_id = response_json["data"]["id"]
        mocked_async_task.delay.assert_called_once()
        mocked_async_task.delay.assert_called_with(job_id=job_id)
