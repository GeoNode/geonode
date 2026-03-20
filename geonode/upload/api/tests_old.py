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
import os
import logging

from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase

from geonode.geoserver.helpers import ogc_server_settings
from geonode.upload.models import UploadSizeLimit, UploadParallelismLimit

LIVE_SERVER_URL = "http://localhost:8001/"
GEOSERVER_URL = ogc_server_settings.LOCATION
GEOSERVER_USER, GEOSERVER_PASSWD = ogc_server_settings.credentials

CURRENT_LOCATION = os.path.abspath(os.path.dirname(__file__))

logger = logging.getLogger("importer")


class UploadSizeLimitTests(APITestCase):
    fixtures = [
        "group_test_data.json",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = get_user_model().objects.get(username="admin")
        UploadSizeLimit.objects.create(
            slug="some-size-limit",
            description="some description",
            max_size=104857600,  # 100 MB
        )
        UploadSizeLimit.objects.create(
            slug="some-other-size-limit",
            description="some other description",
            max_size=52428800,  # 50 MB
        )

    def test_list_size_limits_admin_user(self):
        url = reverse("upload-size-limits-list")

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limits = [
            (size_limit["slug"], size_limit["max_size"], size_limit["max_size_label"])
            for size_limit in response.json()["upload-size-limits"]
        ]
        expected_size_limits = [
            ("some-size-limit", 104857600, "100.0\xa0MB"),
            ("some-other-size-limit", 52428800, "50.0\xa0MB"),
        ]
        for size_limit in expected_size_limits:
            self.assertIn(size_limit, size_limits)

    def test_list_size_limits_anonymous_user(self):
        url = reverse("upload-size-limits-list")

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        # Response Content
        size_limits = [
            (size_limit["slug"], size_limit["max_size"], size_limit["max_size_label"])
            for size_limit in response.json()["upload-size-limits"]
        ]
        expected_size_limits = [
            ("some-size-limit", 104857600, "100.0\xa0MB"),
            ("some-other-size-limit", 52428800, "50.0\xa0MB"),
        ]
        for size_limit in expected_size_limits:
            self.assertIn(size_limit, size_limits)

    def test_retrieve_size_limit_admin_user(self):
        url = reverse("upload-size-limits-detail", args=("some-size-limit",))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limit = response.json()["upload-size-limit"]
        self.assertEqual(size_limit["slug"], "some-size-limit")
        self.assertEqual(size_limit["max_size"], 104857600)
        self.assertEqual(size_limit["max_size_label"], "100.0\xa0MB")

    def test_retrieve_size_limit_anonymous_user(self):
        url = reverse("upload-size-limits-detail", args=("some-size-limit",))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        # Response Content
        size_limit = response.json()["upload-size-limit"]
        self.assertEqual(size_limit["slug"], "some-size-limit")
        self.assertEqual(size_limit["max_size"], 104857600)
        self.assertEqual(size_limit["max_size_label"], "100.0\xa0MB")

    def test_patch_size_limit_admin_user(self):
        url = reverse("upload-size-limits-detail", args=("some-size-limit",))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(url, data={"max_size": 5242880})

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_patch_size_limit_anonymous_user(self):
        url = reverse("upload-size-limits-detail", args=("some-size-limit",))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.patch(url, data={"max_size": 2621440})

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_put_size_limit_admin_user(self):
        url = reverse("upload-size-limits-detail", args=("some-size-limit",))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(url, data={"slug": "some-size-limit", "max_size": 5242880})

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_put_size_limit_anonymous_user(self):
        url = reverse("upload-size-limits-detail", args=("some-size-limit",))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.put(url, data={"slug": "some-size-limit", "max_size": 2621440})

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_post_size_limit_admin_user(self):
        url = reverse("upload-size-limits-list")

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data={"slug": "some-new-slug", "max_size": 5242880})

        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        size_limit = response.json()["upload-size-limit"]
        self.assertEqual(size_limit["slug"], "some-new-slug")
        self.assertEqual(size_limit["max_size"], 5242880)
        self.assertEqual(size_limit["max_size_label"], "5.0\xa0MB")

    def test_post_size_limit_anonymous_user(self):
        url = reverse("upload-size-limits-list")

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.post(url, data={"slug": "other-new-slug", "max_size": 2621440})

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_delete_size_limit_admin_user(self):
        url = reverse("upload-size-limits-detail", args=("some-size-limit",))

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_delete_size_limit_anonymous_user(self):
        url = reverse("upload-size-limits-detail", args=("some-other-size-limit",))

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)


class UploadParallelismLimitTests(APITestCase):
    fixtures = [
        "group_test_data.json",
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = get_user_model().objects.get(username="admin")
        cls.norman_user = get_user_model().objects.get(username="norman")
        cls.test_user = get_user_model().objects.get(username="test_user")
        try:
            cls.default_parallelism_limit = UploadParallelismLimit.objects.get(slug="default_max_parallel_uploads")
        except UploadParallelismLimit.DoesNotExist:
            cls.default_parallelism_limit = UploadParallelismLimit.objects.create_default_limit()

    def test_list_parallelism_limits_admin_user(self):
        url = reverse("upload-parallelism-limits-list")

        # List as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        parallelism_limits = [
            (parallelism_limit["slug"], parallelism_limit["max_number"])
            for parallelism_limit in response.json()["upload-parallelism-limits"]
        ]
        expected_parallelism_limits = [
            (self.default_parallelism_limit.slug, self.default_parallelism_limit.max_number),
        ]
        for parallelism_limit in expected_parallelism_limits:
            self.assertIn(parallelism_limit, parallelism_limits)

    def test_list_parallelism_limits_anonymous_user(self):
        url = reverse("upload-parallelism-limits-list")

        # List as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
        # Response Content
        parallelism_limits = [
            (parallelism_limit["slug"], parallelism_limit["max_number"])
            for parallelism_limit in response.json()["upload-parallelism-limits"]
        ]
        expected_parallelism_limits = [
            (self.default_parallelism_limit.slug, self.default_parallelism_limit.max_number),
        ]
        for parallelism_limit in expected_parallelism_limits:
            self.assertIn(parallelism_limit, parallelism_limits)

    def test_retrieve_parallelism_limit_admin_user(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Retrieve as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        parallelism_limit = response.json()["upload-parallelism-limit"]
        self.assertEqual(parallelism_limit["slug"], self.default_parallelism_limit.slug)
        self.assertEqual(parallelism_limit["max_number"], self.default_parallelism_limit.max_number)

    def test_retrieve_parallelism_limit_norman_user(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Retrieve as a norman user
        self.client.force_authenticate(user=self.norman_user)
        response = self.client.get(url)

        # Assertions
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.norman_user)
        # Response Content
        parallelism_limit = response.json()["upload-parallelism-limit"]
        self.assertEqual(parallelism_limit["slug"], self.default_parallelism_limit.slug)
        self.assertEqual(parallelism_limit["max_number"], self.default_parallelism_limit.max_number)

    def test_patch_parallelism_limit_admin_user(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Patch as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.patch(url, data={"max_number": 3})

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_patch_parallelism_limit_norman_user(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Patch as a norman user
        self.client.force_authenticate(user=None)
        response = self.client.patch(url, data={"max_number": 4})

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_patch_parallelism_limit_anonymous_user(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Patch as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.patch(url, data={"max_number": 6})

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_put_parallelism_limit_admin_user(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Put as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.put(url, data={"slug": self.default_parallelism_limit.slug, "max_number": 7})

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_put_parallelism_limit_anonymous_user(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Put as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.put(url, data={"slug": self.default_parallelism_limit.slug, "max_number": 8})

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_post_parallelism_limit_admin_user(self):
        url = reverse("upload-parallelism-limits-list")

        # Post as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.post(url, data={"slug": "some-parallelism-limit", "max_number": 9})

        # Assertions
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.wsgi_request.user, self.admin)
        # Response Content
        parallelism_limit = response.json()["upload-parallelism-limit"]
        self.assertEqual(parallelism_limit["slug"], "some-parallelism-limit")
        self.assertEqual(parallelism_limit["max_number"], 9)

    def test_post_parallelism_limit_anonymous_user(self):
        url = reverse("upload-parallelism-limits-list")

        # Post as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.post(url, data={"slug": "some-parallelism-limit", "max_number": 8})

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)

    def test_delete_parallelism_limit_admin_user(self):
        UploadParallelismLimit.objects.create(
            slug="test-parallelism-limit",
            max_number=123,
        )
        url = reverse("upload-parallelism-limits-detail", args=("test-parallelism-limit",))

        # Delete as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_delete_parallelism_limit_admin_user_protected(self):
        url = reverse("upload-parallelism-limits-detail", args=(self.default_parallelism_limit.slug,))

        # Delete as an admin user
        self.client.force_authenticate(user=self.admin)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.wsgi_request.user, self.admin)

    def test_delete_parallelism_limit_anonymous_user(self):
        UploadParallelismLimit.objects.create(
            slug="test-parallelism-limit",
            max_number=123,
        )
        url = reverse("upload-parallelism-limits-detail", args=("test-parallelism-limit",))

        # Delete as an Anonymous user
        self.client.force_authenticate(user=None)
        response = self.client.delete(url)

        # Assertions
        self.assertEqual(response.status_code, 401)
        self.assertTrue(response.wsgi_request.user.is_anonymous)
