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
from django.test.utils import override_settings
from geonode.tests.base import GeoNodeBaseTestSupport

from django.core import mail
from django.urls import reverse
from django.db import transaction
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site
from allauth.account.forms import SignupForm

from geonode.layers import utils
from geonode.layers.models import Dataset
from geonode.people import profileextractors

from geonode.base.populate_test_data import all_public, create_models, remove_models


class PeopleAndProfileTests(GeoNodeBaseTestSupport):

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()
        self.layers = Dataset.objects.all()[:3]
        self.dataset_ids = [layer.pk for layer in self.layers]
        self.user_ids = ",".join(str(element.pk) for element in get_user_model().objects.all()[:3])
        self.permission_type = ("r", "w", "d")
        self.groups = Group.objects.all()[:3]
        self.group_ids = ",".join(str(element.pk) for element in self.groups)

    def test_redirect_on_get_request(self):
        """
        Test that an immediate redirect occurs back to the admin
        page of origin when no IDS are supplied
        """
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse("set_user_dataset_permissions"))
        self.assertEqual(response.status_code, 302)

    def test_admin_only_access(self):
        """
        Test that only admin users can access the routes
        """
        self.client.logout()
        response = self.client.get(reverse("set_user_dataset_permissions"))
        self.assertEqual(response.status_code, 302)

    @override_settings(ASYNC_SIGNALS=False)
    def test_set_unset_user_dataset_permissions(self):
        """
        Test that user permissions are set for layers
        """
        self.client.login(username="admin", password="admin")
        response = self.client.post(
            reverse("set_user_dataset_permissions"),
            data={
                "ids": self.user_ids,
                "layers": self.dataset_ids,
                "permission_type": self.permission_type,
                "mode": "set",
            },
        )
        self.assertEqual(response.status_code, 302)
        with transaction.atomic():
            for permissions_name in self.permission_type:
                utils.set_datasets_permissions(
                    permissions_name,
                    [
                        resource.name
                        for resource in Dataset.objects.filter(id__in=[int(_id) for _id in self.dataset_ids])
                    ],
                    [user.username for user in get_user_model().objects.filter(id__in=self.user_ids.split(","))],
                    [],
                    False,
                    verbose=True,
                )
        for layer in self.layers:
            user = get_user_model().objects.first()
            perm_spec = layer.get_all_level_info()
            self.assertFalse(user in perm_spec["users"], f"{layer} - {user}")

    @override_settings(ASYNC_SIGNALS=False)
    def test_set_unset_group_dataset_permissions(self):
        """
        Test that group permissions are set for layers
        """
        self.client.login(username="admin", password="admin")
        response = self.client.post(
            reverse("set_group_dataset_permissions"),
            data={
                "ids": self.group_ids,
                "layers": self.dataset_ids,
                "permission_type": self.permission_type,
                "mode": "set",
            },
        )
        self.assertEqual(response.status_code, 302)
        with transaction.atomic():
            for permissions_name in self.permission_type:
                utils.set_datasets_permissions(
                    permissions_name,
                    [
                        resource.name
                        for resource in Dataset.objects.filter(id__in=[int(_id) for _id in self.dataset_ids])
                    ],
                    [],
                    [group.name for group in Group.objects.filter(id__in=self.group_ids.split(","))],
                    False,
                    verbose=True,
                )
        for layer in self.layers:
            perm_spec = layer.get_all_level_info()
            self.assertTrue(self.groups[0] in perm_spec["groups"])

    @override_settings(ASYNC_SIGNALS=False)
    def test_unset_group_dataset_perms(self):
        """
        Test that group permissions are unset for layers
        """
        user = get_user_model().objects.first()
        for layer in self.layers:
            layer.set_permissions(
                {
                    "users": {
                        user.username: [
                            "change_dataset_data",
                            "view_resourcebase",
                            "download_resourcebase",
                            "change_resourcebase_metadata",
                        ]
                    }
                }
            )

        self.client.login(username="admin", password="admin")
        response = self.client.post(
            reverse("set_user_dataset_permissions"),
            data={
                "ids": self.user_ids,
                "layers": self.dataset_ids,
                "permission_type": self.permission_type,
                "mode": "unset",
            },
        )
        self.assertEqual(response.status_code, 302)
        with transaction.atomic():
            for permissions_name in self.permission_type:
                utils.set_datasets_permissions(
                    permissions_name,
                    [
                        resource.name
                        for resource in Dataset.objects.filter(id__in=[int(_id) for _id in self.dataset_ids])
                    ],
                    [user.username for user in get_user_model().objects.filter(id__in=self.user_ids.split(","))],
                    [],
                    True,
                    verbose=True,
                )
        for layer in self.layers:
            perm_spec = layer.get_all_level_info()
            self.assertTrue(user not in perm_spec["users"])

    def test_forgot_username(self):
        url = reverse("forgot_username")

        # page renders
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # and responds for a bad email
        response = self.client.post(url, data={"email": "foobar@doesnotexist.com"})
        self.assertContains(response, "No user could be found with that email address.")

        norman = get_user_model().objects.get(username="norman")
        norman.email = "contact@admin.admin"
        norman.save()
        response = self.client.post(url, data={"email": norman.email})
        # and sends a mail for a good one
        self.assertEqual(len(mail.outbox), 1)

        site = Site.objects.get_current()

        # Verify that the subject of the first message is correct.
        self.assertEqual(mail.outbox[0].subject, f"Your username for {site.name}")

    def test_get_profile(self):
        admin = get_user_model().objects.get(username="admin")
        norman = get_user_model().objects.get(username="norman")
        bobby = get_user_model().objects.get(username="bobby")
        bobby.voice = "+245-897-7889"
        bobby.save()
        url = reverse("profile_detail", args=["bobby"])

        # Get user's profile as anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Get user's profile by another authenticated user
        self.assertTrue(self.client.login(username="norman", password="norman"))
        self.assertTrue(norman.is_authenticated)
        response = self.client.get(url, user=norman)
        self.assertEqual(response.status_code, 200)
        # Returns limitted info about a user
        content = response.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        self.assertIn("Profile of bobby", content)
        self.assertNotIn(bobby.voice, content)

        # Get user's profile as owner
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Returns all profile info
        content = response.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        self.assertIn("Profile of bobby", content)
        self.assertIn(bobby.voice, content)

        # Get user's profile as admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        self.assertTrue(admin.is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Returns all profile info
        content = response.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        self.assertIn("Profile of bobby", content)
        self.assertIn(bobby.voice, content)

    def _facebook_extractor_init(self):
        data = {
            "email": "phony_mail",
            "first_name": "phony_first_name",
            "last_name": "phony_last_name",
            "cover": "phony_cover",
        }
        extractor = profileextractors.FacebookExtractor()
        return extractor, data

    def test_extract_area(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_area(data)

    def test_extract_city(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_city(data)

    def test_extract_country(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_country(data)

    def test_extract_delivery(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_delivery(data)

    def test_fb_extract_email(self):
        extractor, data = self._facebook_extractor_init()

        result = extractor.extract_email(data)
        self.assertEqual(result, data["email"])

    def test_extract_fax(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_fax(data)

    def test_fb_extract_first_name(self):
        extractor, data = self._facebook_extractor_init()

        result = extractor.extract_first_name(data)
        self.assertEqual(result, data["first_name"])

    def test_fb_extract_last_name(self):
        extractor, data = self._facebook_extractor_init()

        result = extractor.extract_last_name(data)
        self.assertEqual(result, data["last_name"])

    def test_extract_organization(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_organization(data)

    def test_extract_position(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_position(data)

    def test_extract_profile(self):
        extractor, data = self._facebook_extractor_init()

        result = extractor.extract_profile(data)
        self.assertEqual(result, data["cover"])

    def test_extract_voice(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_voice(data)

    def test_extract_zipcode(self):
        extractor, data = self._facebook_extractor_init()

        with self.assertRaises(NotImplementedError):
            extractor.extract_zipcode(data)

    def _linkedin_extractor_init(self):
        data = {
            "id": "REDACTED",
            "firstName": {"localized": {"en_US": "Tina"}, "preferredLocale": {"country": "US", "language": "en"}},
            "lastName": {"localized": {"en_US": "Belcher"}, "preferredLocale": {"country": "US", "language": "en"}},
            "profilePicture": {"displayImage": "urn:li:digitalmediaAsset:B54328XZFfe2134zTyq"},
            "elements": [
                {"handle": "urn:li:emailAddress:3775708763", "handle~": {"emailAddress": "hsimpson@linkedin.com"}}
            ],
        }
        extractor = profileextractors.LinkedInExtractor()
        return extractor, data

    def test_ln_extract_email(self):
        extractor, data = self._linkedin_extractor_init()

        result = extractor.extract_email(data)
        self.assertEqual(result, data["elements"][0]["handle~"]["emailAddress"])

    def test_ln_extract_first_name(self):
        extractor, data = self._linkedin_extractor_init()

        result = extractor.extract_first_name(data)
        self.assertEqual(result, data["firstName"]["localized"]["en_US"])

    def test_ln_extract_last_name(self):
        extractor, data = self._linkedin_extractor_init()

        result = extractor.extract_last_name(data)
        self.assertEqual(result, data["lastName"]["localized"]["en_US"])

    @override_settings(
        AUTH_PASSWORD_VALIDATORS=[
            {
                "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
            },
            {
                "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
                "OPTIONS": {
                    "min_length": 14,
                },
            },
            {
                "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
            },
            {
                "NAME": "geonode.people.password_validators.UppercaseValidator",
            },
            {
                "NAME": "geonode.people.password_validators.NumberValidator",
                "OPTIONS": {
                    "min_digits": 1,
                },
            },
            {
                "NAME": "geonode.people.password_validators.LowercaseValidator",
            },
            {
                "NAME": "geonode.people.password_validators.SpecialCharsValidator",
            },
        ]
    )
    def test_password_validators(self):
        data = {"username": "username", "email": "user@example.com", "password1": "qwerty", "password2": "qwerty"}
        error_codes = [
            "password_too_short",
            "password_too_common",
            "password_no_upper",
            "password_no_number",
            "password_no_upper",
        ]
        form = SignupForm(data, email_required=True)
        self.assertFalse(form.is_valid())
        for errors in form.errors.values():
            for error in errors.data:
                self.assertTrue(error.code in error_codes)

        data = {
            "username": "username",
            "email": "user@example.com",
            "password1": "@!2XJSL_S&V^0nt",
            "password2": "@!2XJSL_S&V^0nt",
        }
        form = SignupForm(data, email_required=True)
        self.assertTrue(form.is_valid())
