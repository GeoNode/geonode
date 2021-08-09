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

import json
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from django.urls import reverse


class CommandViewTests(APITestCase):

    def setUp(self):
        self.url = "geonode.commands:jobs"
        self.standard_user = get_user_model().objects.create(
            username="standard_user", email="test@test.com"
        )
        self.staff_user, _ = get_user_model().objects.get_or_create(
            username="staff_user", is_staff=True
        )
        self.super_user, _ = get_user_model().objects.get_or_create(
            username="superuser", is_staff=True, is_superuser=True
        )

        self.payload = {
        "cmd": "test_command",
        "args": ["delta"],
        "kwargs": {
                "cpair": [10, 40],
                "ppair": ["a", "b"]
            }
        }

    def test_permissions_on_GET_endpoint(self):
        cases = (
            {"user": None, "status": status.HTTP_401_UNAUTHORIZED},
            {"user": self.standard_user, "status": status.HTTP_403_FORBIDDEN},
            {"user": self.staff_user, "status": status.HTTP_403_FORBIDDEN},
            {"user": self.super_user, "status": status.HTTP_200_OK},
        )

        for case in cases:
            with self.subTest(case=case):
                if case.get("user"):
                    self.client.force_authenticate(user=case["user"])
                response = self.client.get(reverse(self.url))
                self.assertEqual(case["status"], response.status_code)

    def test_permissions_on_POST_endpoint(self):
        cases = (
            {"user": None, "status": status.HTTP_401_UNAUTHORIZED},
            {"user": self.standard_user, "status": status.HTTP_403_FORBIDDEN},
            {"user": self.staff_user, "status": status.HTTP_403_FORBIDDEN},
            {"user": self.super_user, "status": status.HTTP_200_OK},
        )

        for case in cases:
            with self.subTest(case=case):
                if case.get("user"):
                    self.client.force_authenticate(user=case["user"])
                response = self.client.post(reverse(self.url), json.dumps(self.payload), content_type="application/json")
                self.assertEqual(case["status"], response.status_code)

    def test_POST_api_response(self):
        self.client.force_authenticate(user=self.super_user)
        response = self.client.post(reverse(self.url), json.dumps(self.payload), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("job_id", response.data)
        self.assertIn("task_id", response.data)
        self.assertEqual(self.super_user.id, response.data["user_id"])
