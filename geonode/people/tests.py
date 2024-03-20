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
import django
from django.test.utils import override_settings
from mock import MagicMock, PropertyMock, patch
from geonode.base.models import ResourceBase
from geonode.groups.models import GroupMember, GroupProfile
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
from django.db.models import Q


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
        self.permission_type = ("view", "download", "edit")
        self.groups = Group.objects.all()[:3]
        self.group_ids = ",".join(str(element.pk) for element in self.groups)
        self.bar = GroupProfile.objects.get(slug="bar")
        self.group_profiles = [GroupProfile.objects.create(title=f"group_{c}", slug=f"slug_{c}") for c in range(5)]

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

    @patch("geonode.base.views.UserAndGroupPermissionsForm.is_valid")
    @patch("geonode.base.views.UserAndGroupPermissionsForm.errors", new_callable=PropertyMock)
    def test_invalid_form_return_the_expected_message(self, form_error, form_valid):
        """
        The form should retrun a pre-defined message if the dataset
        is not part of the choices
        """
        error_obj = MagicMock(data=[MagicMock(code="invalid_choice")])
        form_valid.return_value = False
        form_error.return_value = {"layers": error_obj}
        self.client.login(username="admin", password="admin")
        response = self.client.post(
            path=reverse("set_user_dataset_permissions"),
            data={"ids": [99999], "permission_type": "view", "mode": "set"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        message = list(response.context.get("messages"))[0]
        self.assertEqual(message.tags, "error")
        self.assertTrue("The following dataset ID selected are not part of the available choices" in message.message)

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

    def test_new_user_is_assigned_automatically_to_contributors(self):
        """
        By default the contributors group is assigned to each new user
        """
        new_user = get_user_model().objects.create(username="random_username")
        self.assertTrue("contributors" in [x.name for x in new_user.groups.iterator()])

    @override_settings(AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS=False)
    def test_new_user_is_no_assigned_automatically_to_contributors_if_disabled(self):
        """
        If AUTO_ASSIGN_REGISTERED_MEMBERS_TO_CONTRIBUTORS is false, each new user is not automatically
        assinged to the contributors group
        """
        new_user = get_user_model().objects.create(username="random_username")
        self.assertFalse("contributors" in [x.name for x in new_user.groups.iterator()])

    def test_users_api_valid_post(self):
        data = {
            "username": "usernam3e",
            "first_name": "Registered",
            "password": "@!2XJSL_S&V^0nt",
            "last_name": "Test",
            "avatar": "https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240",
            "perms": ["add_resource"],
            "is_superuser": False,
            "is_staff": False,
            "email": "fpglf@poc.com",
        }

        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse("users-list"), data=data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

    def test_users_api_post_not_admin(self):
        data = {
            "username": "usernam3e",
            "first_name": "Registered",
            "password": "@!2XJSL_S&V^0nt",
            "last_name": "Test",
            "avatar": "https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240",
            "perms": ["add_resource"],
            "is_superuser": True,
            "is_staff": True,
            "email": "fpglf@poc.com",
        }
        bobby = get_user_model().objects.get(username="bobby")
        self.client.login(username="bobby", password="bob")
        # assert that bobby is not a super user or staff
        self.assertFalse(bobby.is_superuser)
        self.assertFalse(bobby.is_staff)
        response = self.client.post(reverse("users-list"), data=data, content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_users_api_patch_self(self):

        bobby = get_user_model().objects.get(username="bobby")
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # bobby wants to edit his own data
        data = {"first_name": "Robert"}
        # before change
        self.assertNotEqual(bobby.first_name, "Robert")

        # and can acess even if he's not admin or staff
        self.assertFalse(bobby.is_superuser)
        self.assertFalse(bobby.is_staff)

        url = f"{reverse('users-list')}/{bobby.pk}"
        response = self.client.patch(url, data=data, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["user"]["first_name"], "Robert")

    def test_users_api_patch_self_as_superuser(self):

        bobby = get_user_model().objects.get(username="bobby")
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # bobby wants to edit his own data
        data = {
            "first_name": "Robert",
            "is_superuser": True,
            "is_staff": True,
        }
        # before change
        self.assertNotEqual(bobby.first_name, "Robert")

        # and can acess even if he's not admin or staff
        self.assertFalse(bobby.is_superuser)
        self.assertFalse(bobby.is_staff)

        url = f"{reverse('users-list')}/{bobby.pk}"
        response = self.client.patch(url, data=data, content_type="application/json")
        response_json = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response_json["user"]["first_name"], "Robert")

        self.assertFalse(response_json["user"]["is_superuser"])
        self.assertFalse(response_json["user"]["is_staff"])
        # check db side too
        bobby = get_user_model().objects.get(username="bobby")
        self.assertFalse(bobby.is_superuser)
        self.assertFalse(bobby.is_staff)

    def test_users_api_patch_others_from_non_admin(self):

        bobby = get_user_model().objects.get(username="bobby")
        profile = get_user_model().objects.get(username="user1")

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # bobby wants to edit his user's data
        data = {"first_name": "Norman Sky", "password": "@!2XJSL_S&V^0nt", "email": "bob@bob.com"}

        # Bobby is not superuser or staff
        self.assertFalse(bobby.is_superuser)
        self.assertFalse(bobby.is_staff)

        url = f"{reverse('users-list')}/{profile.pk}"
        response = self.client.patch(url, data=data, content_type="application/json")

        # bobby is not permitted to update user data
        self.assertEqual(response.status_code, 403)

    def test_users_api_patch_others_from_admin(self):

        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="admin", password="admin"))
        self.assertTrue(admin.is_authenticated)
        # admin wants to edit his bobby's data
        data = {"first_name": "Robert Baratheon", "password": "@!2XJSL_S&V^0nt000", "email": "bob@bob.com"}

        # Admin is superuser or staff
        self.assertTrue(admin.is_superuser or admin.is_staff)

        url = f"{reverse('users-list')}/{bobby.pk}"
        response = self.client.patch(url, data=data, content_type="application/json")

        # admin is  permitted to update bobby's data
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json()["user"]["first_name"], "Robert Baratheon")

    @override_settings(ACCOUNT_EMAIL_REQUIRED=True)
    def test_users_api_empty_email(self):
        """
        If the environment variable ACCOUNT_EMAIL_REQUIRED is set to True,
        the email will be mandatory in the payload.
        """
        data = {
            "username": "usernam3e",
            "first_name": "Registered",
            "password": "@!2XJSL_S&V^0nt",
            "last_name": "Test",
            "avatar": "https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240",
            "perms": ["add_resource"],
            "is_superuser": False,
            "is_staff": False,
        }
        # ensure there is no email in payload
        data.pop("email", None)

        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse("users-list"), data=data, content_type="application/json")

        # endpoint throws Exception on missing email
        self.assertEqual(response.status_code, 400)
        self.assertTrue("email missing from payload" in response.json()["errors"])

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
    def test_users_api_invalid_password(self):
        """
        If a password validator is set via AUTH_PASSWORD_VALIDATORS,
        the API will return an error if the validation fails
        """
        error_codes = [
            "This password is too short. It must contain at least 14 characters.",
            "The password must contain at least1 digit(s), 0-9.",
        ]
        data = {
            "username": "usernam3e",
            "first_name": "Registered",
            "password": "whitetext",
            "last_name": "Test",
            "avatar": "https://www.gravatar.com/avatar/7a68c67c8d409ff07e42aa5d5ab7b765/?s=240",
            "perms": ["add_resource"],
            "is_superuser": False,
            "is_staff": False,
            "email": "fpglf@poc.com",
        }

        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse("users-list"), data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)

        for error in error_codes:
            self.assertTrue(error in response.json()["errors"][0])

    @override_settings(
        ACCOUNT_EMAIL_VERIFICATION="mandatory",
        EMAIL_HOST="localhost",
        EMAIL_HOST_USER="",
        EMAIL_HOST_PASSWORD="",
        EMAIL_PORT="25",
    )
    def test_users_register_email_verification(self):
        """
        If the email confirmation requirement is configured,
        a verification email will be sent to the user before allowing them to log in.
        """
        data = {
            "username": "usernam3e",
            "email": "user@exampl2e.com",
            "password1": "@!2XJSL_S&V^0nt",
            "password2": "@!2XJSL_S&V^0nt",
        }

        response = self.client.post(reverse("account_signup"), data=data, format="json")
        # response should be a redirect to the confirmation email
        self.assertEqual(response.status_code, 302)

        # check that user was created
        get_user_model().objects.get(email=data["email"])

        email_box = django.core.mail.outbox
        # assert that an email was sent to the email provided in the payload
        self.assertEqual(len(email_box), 1)
        self.assertTrue(data["email"] in email_box[0].to)

    def test_users_api_patch_password_from_admin(self):
        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="admin", password="admin"))
        self.assertTrue(admin.is_authenticated)

        # admin wants to edit his bobby's data
        data = {"password": "@!2XJSL_S&V^0nt000"}
        # Admin is superuser or staff
        self.assertTrue(admin.is_superuser or admin.is_staff)
        old_pass = bobby.password

        url = f"{reverse('users-list')}/{bobby.pk}"
        response = self.client.patch(url, data=data, content_type="application/json")

        # admin is  permitted to update bobby's data
        self.assertEqual(response.status_code, 200)
        # bobbys password has changed
        bobby.refresh_from_db()
        # asserting not equal from the password salt
        self.assertNotEqual(bobby.password, old_pass)

    def test_users_api_add_existing_email(self):
        data = {"username": "teddy", "password": "@!2XJSL_S&V^0nt", "email": "teddy@teddy.com"}
        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse("users-list"), data=data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        # try to readd the same email
        data = {"username": "teddy1", "password": "@!2XJSL_S&V^0nt", "email": "teddy@teddy.com"}
        response = self.client.post(reverse("users-list"), data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue("A user is already registered with that email" in response.json()["errors"])

    def test_users_api_add_existing_username(self):
        bobby = get_user_model().objects.get(username="bobby")

        data = {"username": bobby.get_username(), "password": "@!2XJSL_S&V^0nt", "email": "bobby@bobby.com"}
        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse("users-list"), data=data, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue("A user with that username already exists." in response.json()["errors"])

    def test_users_api_patch_username(self):

        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="admin", password="admin"))
        # admin wants to edit his bobby's data
        data = {
            "first_name": "Robert Baratheon",
            "username": "bob",
            "password": "@!2XJSL_S&V^0nt000",
            "email": "bob@bob.com",
        }

        # Admin is superuser or staff
        self.assertTrue(admin.is_superuser or admin.is_staff)

        url = f"{reverse('users-list')}/{bobby.pk}"
        response = self.client.patch(url, data=data, content_type="application/json")

        # username cannot be updated
        self.assertEqual(response.status_code, 400)
        self.assertTrue("username cannot be updated" in response.json()["errors"])

    @override_settings(
        USER_DELETION_RULES=["geonode.people.utils.user_has_resources", "geonode.people.utils.user_is_manager"]
    )
    def test_valid_delete(self):
        # create a new user
        tim = get_user_model().objects.create(username="tim")

        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="admin", password="admin"))

        # admin wants to delete tim
        # Admin is superuser or staff
        self.assertTrue(admin.is_superuser or admin.is_staff)
        # check that tim is not manager
        # nor has any resources
        self.assertFalse(ResourceBase.objects.filter(owner_id=tim.pk).exists())
        self.assertFalse(GroupMember.objects.filter(user_id=tim.pk, role="manager").exists())

        url = f"{reverse('users-list')}/{tim.pk}"
        response = self.client.delete(url, content_type="application/json")

        # admin is  permitted to delete
        self.assertEqual(response.status_code, 200)
        # tim has been deleted
        self.assertEqual(get_user_model().objects.filter(username="tim").first(), None)

    @override_settings(USER_DELETION_RULES=[])
    @patch("geonode.people.utils.user_deletion_modules", [])
    def test_delete_without_validators(self):

        norman = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="admin", password="admin"))

        # admin wants to delete norman but norman is already promoted
        # Admin is superuser or staff
        self.assertTrue(admin.is_superuser or admin.is_staff)

        # Make sure norman is not a member
        self.assertFalse(self.bar.user_is_member(norman))

        # Add norman to the self.bar group
        self.bar.join(norman)

        # Ensure norman is now a member
        self.assertTrue(self.bar.user_is_member(norman))

        # promote norman to a manager
        self.bar.promote(norman)
        # Ensure norman is in the managers queryset
        self.assertTrue(norman in self.bar.get_managers())

        url = f"{reverse('users-list')}/{norman.pk}"
        response = self.client.delete(url, content_type="application/json")

        # norman can be deleted because validator rules are not applied
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.filter(username="norman").first(), None)

    @override_settings(
        USER_DELETION_RULES=["geonode.people.utils.user_has_resources", "geonode.people.utils.user_is_manager"]
    )
    def test_delete_a_manger(self):
        norman = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="admin", password="admin"))

        # admin wants to delete norman but norman is already promoted
        # Admin is superuser or staff
        self.assertTrue(admin.is_superuser or admin.is_staff)

        # Make sure norman is not a member
        self.assertFalse(self.bar.user_is_member(norman))

        # Add norman to the self.bar group
        self.bar.join(norman)

        # Ensure norman is now a member
        self.assertTrue(self.bar.user_is_member(norman))

        # promote norman to a manager
        self.bar.promote(norman)
        # Ensure norman is in the managers queryset
        self.assertTrue(norman in self.bar.get_managers())

        url = f"{reverse('users-list')}/{norman.pk}"
        response = self.client.delete(url, content_type="application/json")

        # norman cant be deleted
        self.assertEqual(response.status_code, 403)
        self.assertNotEqual(get_user_model().objects.filter(username="norman").first(), None)
        #
        self.assertTrue("user_is_manager" in response.json()["errors"][0])

    @override_settings(USER_DELETION_RULES=["geonode.people.utils.user_has_resources"])
    def test_delete_a_user_with_resource(self):
        # create a new user
        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="admin", password="admin"))

        # admin wants to delete bobby
        # Admin is superuser or staff
        self.assertTrue(admin.is_superuser or admin.is_staff)
        # check that bobby is not manager
        # but he has resources already assigned
        self.assertTrue(ResourceBase.objects.filter(owner_id=bobby.pk).exists())
        self.assertFalse(GroupMember.objects.filter(user_id=bobby.pk, role="manager").exists())

        url = f"{reverse('users-list')}/{bobby.pk}"
        response = self.client.delete(url, content_type="application/json")

        # admin is  permitted to delete
        self.assertEqual(response.status_code, 403)
        # bobby cant be deleted
        self.assertNotEqual(get_user_model().objects.filter(username="bobby").first(), None)
        self.assertTrue("user_has_resources" in response.json()["errors"][0])

    def test_remove_self_from_group_manager_all(self):
        """
        user is manager of some groups
        and is quitting all
        """
        bobby = get_user_model().objects.get(username="bobby")
        for group in self.group_profiles:
            group.join(bobby)
            group.promote(bobby)

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # assert that bobby is manager of these groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # call the api that removes him from all assigned groups as manager
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/remove_from_group_manager",
            data={"groups": "ALL"},
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 200)
        # check that bobby is manager no more
        for group in self.group_profiles:
            self.assertFalse(bobby in group.get_managers())
            self.assertTrue(group.title in response.json()["success"])

    def test_remove_self_as_group_manager_list(self):
        """
        user is manager of some groups
        and is quitting some of them
        """
        bobby = get_user_model().objects.get(username="bobby")

        for group in self.group_profiles:
            group.join(bobby)
            group.promote(bobby)

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # assert that bobby is manager of these groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # call the api that removes him from all assigned groups as manager
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/remove_from_group_manager",
            data={"groups": [group.group_id for group in self.group_profiles[:3]]},
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 200)
        # check that bobby is  no more manager in the first groups
        for group in self.group_profiles[:3]:
            self.assertFalse(bobby in group.get_managers())
            self.assertTrue(group.title in response.json()["success"])
        # but still manager in the others
        for group in self.group_profiles[4:]:
            self.assertTrue(bobby in group.get_managers())

    def test_remove_user_as_group_manager_empty(self):
        """
        user is manager of some groups
        and is sending empty payload
        """
        bobby = get_user_model().objects.get(username="bobby")

        for group in self.group_profiles:
            group.join(bobby)
            group.promote(bobby)

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # assert that bobby is manager of these groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # call the api that removes him from all assigned groups as manager
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/remove_from_group_manager",
            data={"groups": ""},
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 400)
        self.assertTrue("No groups IDs were provided" in response.json()["error"])
        # check that bobby is still manager at all groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())

    def test_remove_user_as_group_manager_of_invalid_groups(self):
        """
        user is manager of some groups
        and is trying to remove himself as a manger of a group hes not part of
        """
        bobby = get_user_model().objects.get(username="bobby")
        for group in self.group_profiles:
            group.join(bobby)
            group.promote(bobby)
        newgroup = GroupProfile.objects.create(title="newgroup")
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # assert that bobby is manager of these groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # and not for the new group
        self.assertFalse(bobby in newgroup.get_managers())
        # call the api that removes him from all assigned groups as manager"
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/remove_from_group_manager",
            data={"groups": [newgroup.group_id]},
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 400)
        # check that bobby is still manager at all groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # assert the invalid group is in the payload
        self.assertTrue("User is not manager of the following groups" in response.json()["error"])
        self.assertTrue(f"{newgroup.group_id}" in response.json()["error"])

    def test_non_admin_remove_user_as_group_manager(self):
        """
        a non admin user tries to remove another user as the group manager
        """
        bobby = get_user_model().objects.get(username="bobby")
        norman = get_user_model().objects.get(username="norman")
        for group in self.group_profiles:
            group.join(bobby)
            group.promote(bobby)

        # assert that bobby is manager of these groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # login as norman
        self.client.force_login(norman)
        self.assertTrue(norman.is_authenticated)
        # assert that norman is neither a super user or staff
        self.assertFalse(norman.is_superuser)
        self.assertFalse(norman.is_staff)

        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/remove_from_group_manager",
            data={"groups": "ALL"},
            content_type="application/json",
        )
        self.assertTrue(response.status_code == 403)
        # check that bobby is still manager at all groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # assert that norman has no permission for this action
        self.assertEqual("permission_denied", response.json()["code"])

    def test_admin_remove_user_as_group_manager(self):
        """
        an admin user tries to remove another user as the group manager
        """
        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")
        for group in self.group_profiles:
            group.join(bobby)
            group.promote(bobby)

        # assert that bobby is manager of these groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # login as admin
        self.client.force_login(admin)
        self.assertTrue(admin.is_authenticated)
        # assert that admin is  a super user , staff
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/remove_from_group_manager",
            data={"groups": "ALL"},
            content_type="application/json",
        )
        # assert that admin has permission for this action
        self.assertTrue(response.status_code == 200)
        # check that bobby is not manager in all his groups
        for group in self.group_profiles:
            self.assertFalse(bobby in group.get_managers())
        self.assertTrue("User removed as a group manager" in response.json()["success"])
        for group in self.group_profiles:
            self.assertTrue(f"{group.title}" in response.json()["success"])

    def test_staff_remove_user_as_group_manager(self):
        """
        an staff user tries to remove another user as the group manager
        """
        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")
        admin.is_superuser = False
        admin.save()
        for group in self.group_profiles:
            group.join(bobby)
            group.promote(bobby)

        # assert that bobby is manager of these groups
        for group in self.group_profiles:
            self.assertTrue(bobby in group.get_managers())
        # login as admin
        self.client.force_login(admin)
        self.assertTrue(admin.is_authenticated)
        # assert that admin is only a staff user
        self.assertFalse(admin.is_superuser)
        self.assertTrue(admin.is_staff)

        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/remove_from_group_manager",
            data={"groups": "ALL"},
            content_type="application/json",
        )
        # assert that admin has permission for this action
        self.assertTrue(response.status_code == 200)
        # check that bobby is not manager in all his groups
        for group in self.group_profiles:
            self.assertFalse(bobby in group.get_managers())
        self.assertTrue("User removed as a group manager" in response.json()["success"])
        for group in self.group_profiles:
            self.assertTrue(f"{group.title}" in response.json()["success"])

    def test_transfer_resources_all(self):
        """
        user wants to transfer resources to target
        """
        bobby = get_user_model().objects.get(username="bobby")
        norman = get_user_model().objects.get(username="norman")
        # group = GroupProfile.objects.get(slug="bar")

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # check bobbys resources
        bobby_resources = ResourceBase.objects.filter(owner=bobby)
        prior_bobby_resources = bobby_resources.all()
        self.assertTrue(bobby_resources.exists())
        # call api
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/transfer_resources", data={"owner": norman.id}
        )
        # check that bobby owns the resources no more
        self.assertFalse(bobby_resources.exists())
        self.assertEqual(response.status_code, 200)
        # check that the resources have been transvered to norman
        norman_resources = ResourceBase.objects.filter(owner=norman).all()
        self.assertTrue(set(prior_bobby_resources).issubset(set(norman_resources)))

    def test_transfer_resources_invalid_user(self):
        """
        user wants to transfer resources to target
        """
        bobby = get_user_model().objects.get(username="bobby")
        invalid_user_id = get_user_model().objects.last().id + 1

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # check bobbys resources
        bobby_resources = ResourceBase.objects.filter(owner=bobby)
        prior_bobby_resources = bobby_resources.all()
        self.assertTrue(bobby_resources.exists())
        # call api
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby}/transfer_resources", data={"owner": invalid_user_id}
        )
        # response should be 404
        self.assertEqual(response.status_code, 404)
        # check that bobby still owns the resources
        later_bobby_resources = bobby_resources.all()
        self.assertTrue(bobby_resources.exists())
        # and no change has happened to them
        self.assertTrue(set(prior_bobby_resources) == set(later_bobby_resources))

    def test_transfer_resources_default(self):
        """
        user wants to transfer resources to target
        """
        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)

        # check bobbys resources
        bobby_resources = ResourceBase.objects.filter(owner=bobby)
        prior_bobby_resources = bobby_resources.all()
        self.assertTrue(bobby_resources.exists())
        # call api
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/transfer_resources", data={"owner": "DEFAULT"}
        )
        self.assertTrue(response.status_code == 200)
        # check that bobby owns the resources no more
        self.assertFalse(bobby_resources.exists())
        # check that the resources have been transfered to admin
        admin_resources = ResourceBase.objects.filter(owner=admin).all()
        self.assertTrue(set(prior_bobby_resources).issubset(set(admin_resources)))

    def test_transfer_resources_to_missing_default(self):
        """
        user wants to transfer resources to principal,
        but a principal account is missing
        """
        bobby = get_user_model().objects.get(username="bobby")
        admin = get_user_model().objects.get(username="admin")

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.client.force_login(bobby)
        self.assertTrue(bobby.is_authenticated)
        # removal of admin accounts
        admin.is_superuser = False
        admin.is_staff = False
        admin.save()
        self.assertFalse(get_user_model().objects.filter(Q(is_superuser=True) | Q(is_staff=True)).exists())

        # check bobbys resources
        bobby_resources = ResourceBase.objects.filter(owner=bobby)
        prior_bobby_resources = bobby_resources.all()
        self.assertTrue(bobby_resources.exists())
        # call api
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/transfer_resources", data={"owner": "DEFAULT"}
        )
        self.assertTrue(response.status_code == 500)
        self.assertEqual(response.data, "Principal User not found")
        # check that bobby still owns the resources
        later_bobby_resources = bobby_resources.all()
        # check that the resources havent changed
        self.assertTrue(set(prior_bobby_resources) == set(later_bobby_resources))

    def test_transfer_resources_to_self(self):
        """
        user wants to transfer resources to self but should be unable to
        """
        bobby = get_user_model().objects.get(username="bobby")

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)

        # check bobbys resources
        bobby_resources = ResourceBase.objects.filter(owner=bobby)
        prior_bobby_resources = bobby_resources.all()
        self.assertTrue(bobby_resources.exists())

        # call api
        response = self.client.post(
            path=f"{reverse('users-list')}/{bobby.pk}/transfer_resources", data={"owner": bobby.pk}
        )
        self.assertTrue(response.status_code == 400)
        self.assertEqual(response.data, "Cannot reassign to self")
        # check that bobby still owns the resources
        later_bobby_resources = ResourceBase.objects.filter(owner=bobby).all()
        # check that the resources havent changed
        self.assertTrue(set(prior_bobby_resources) == set(later_bobby_resources))

    def test_transfer_resources_nopayload(self):
        """
        user wants to transfer resources to target
        """
        bobby = get_user_model().objects.get(username="bobby")
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        self.assertTrue(bobby.is_authenticated)
        # check bobbys resources
        bobby_resources = ResourceBase.objects.filter(owner=bobby)
        prior_bobby_resources = bobby_resources.all()
        self.assertTrue(bobby_resources.exists())

        # call api
        response = self.client.post(path=f"{reverse('users-list')}/{bobby.pk}/transfer_resources", data={})
        # response should be 404
        self.assertEqual(response.status_code, 404)
        # check that bobby still owns the resources
        self.assertTrue(bobby_resources.exists())
        later_bobby_resources = ResourceBase.objects.filter(owner=bobby).all()
        self.assertTrue(set(prior_bobby_resources) == set(later_bobby_resources))
