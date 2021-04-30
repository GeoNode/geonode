# -*- coding: utf-8 -*-
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

from geonode.tests.base import GeoNodeBaseTestSupport

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from django.contrib.sites.models import Site

from geonode.people import profileextractors
from geonode.layers.models import Layer
from django.contrib.auth.models import Group


class TestSetUnsetUserLayerPermissions(GeoNodeBaseTestSupport):
    def setUp(self):
        super(TestSetUnsetUserLayerPermissions, self).setUp()
        self.layers = Layer.objects.all()[:3]
        self.layer_ids = [layer.pk for layer in self.layers]
        self.user_ids = ','.join([str(element.pk) for element in get_user_model().objects.all()[:3]])
        self.permission_type = ('r', 'w', 'd')
        self.groups = Group.objects.all()[:3]
        self.group_ids = ','.join([str(element.pk) for element in self.groups])

    def test_redirect_on_get_request(self):
        """
        Test that an immediate redirect occurs back to the admin
        page of origin when no IDS are supplied
        """
        self.client.login(username="admin", password="admin")
        response = self.client.get(reverse('set_user_layer_permissions'))
        self.assertEqual(response.status_code, 302)

    def test_admin_only_access(self):
        """
        Test that only admin users can access the routes
        """
        self.client.login(username="bobby", password="bob")
        response = self.client.get(reverse('set_user_layer_permissions'))
        self.assertEqual(response.status_code, 401)

    def test_set_unset_user_layer_permissions(self):
        """
        Test that user permissions are set for layers
        """
        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse('set_user_layer_permissions'), data={
            'ids': self.user_ids, 'layers': self.layer_ids,
            'permission_type': self.permission_type, 'mode': 'set'
        })
        self.assertEqual(response.status_code, 302)
        for layer in self.layers:
            perm_spec = layer.get_all_level_info()
            self.assertTrue(get_user_model().objects.all()[0] in perm_spec["users"])

    def test_set_unset_group_layer_permissions(self):
        """
        Test that group permissions are set for layers
        """
        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse('set_group_layer_permissions'), data={
            'ids': self.group_ids, 'layers': self.layer_ids,
            'permission_type': self.permission_type, 'mode': 'set'
        })
        self.assertEqual(response.status_code, 302)
        for layer in self.layers:
            perm_spec = layer.get_all_level_info()
            self.assertTrue(self.groups[0] in perm_spec["groups"])

    def test_unset_group_layer_perms(self):
        """
        Test that group permissions are unset for layers
        """
        user = get_user_model().objects.all()[0]
        for layer in self.layers:
            layer.set_permissions({'users': {user.username: [
                                  'change_layer_data', 'view_resourcebase',
                                  'download_resourcebase', 'change_resourcebase_metadata']}})

        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse('set_user_layer_permissions'), data={
            'ids': self.user_ids, 'layers': self.layer_ids,
            'permission_type': self.permission_type, 'mode': 'unset'
        })

        self.assertEqual(response.status_code, 302)
        for layer in self.layers:
            perm_spec = layer.get_all_level_info()
            self.assertTrue(user not in perm_spec["users"])


class PeopleTest(GeoNodeBaseTestSupport):

    def test_forgot_username(self):
        url = reverse('forgot_username')

        # page renders
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # and responds for a bad email
        response = self.client.post(url, data={
            'email': 'foobar@doesnotexist.com'
        })
        self.assertContains(response, "No user could be found with that email address.")

        norman = get_user_model().objects.get(username='norman')
        norman.email = "contact@admin.admin"
        norman.save()
        response = self.client.post(url, data={
            'email': norman.email
        })
        # and sends a mail for a good one
        self.assertEqual(len(mail.outbox), 1)

        site = Site.objects.get_current()

        # Verify that the subject of the first message is correct.
        self.assertEqual(
            mail.outbox[0].subject,
            f"Your username for {site.name}")

    def test_get_profile(self):
        admin = get_user_model().objects.get(username='admin')
        norman = get_user_model().objects.get(username='norman')
        bobby = get_user_model().objects.get(username='bobby')
        bobby.voice = '+245-897-7889'
        bobby.save()
        url = reverse('profile_detail', args=['bobby'])

        # Get user's profile as anonymous
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Returns limitted info about a user
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        self.assertIn('Profile of bobby', content)
        self.assertNotIn(bobby.voice, content)

        # Get user's profile by another authenticated user
        self.assertTrue(self.client.login(username='norman', password='norman'))
        self.assertTrue(norman.is_authenticated)
        response = self.client.get(url, user=norman)
        self.assertEqual(response.status_code, 200)
        # Returns limitted info about a user
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        self.assertIn('Profile of bobby', content)
        self.assertNotIn(bobby.voice, content)

        # Get user's profile as owner
        self.assertTrue(self.client.login(username='bobby', password='bob'))
        self.assertTrue(bobby.is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Returns all profile info
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        self.assertIn('Profile of bobby', content)
        self.assertIn(bobby.voice, content)

        # Get user's profile as admin
        self.assertTrue(self.client.login(username='admin', password='admin'))
        self.assertTrue(admin.is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Returns all profile info
        content = response.content
        if isinstance(content, bytes):
            content = content.decode('UTF-8')
        self.assertIn('Profile of bobby', content)
        self.assertIn(bobby.voice, content)


class FacebookExtractorTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(FacebookExtractorTestCase, self).setUp()
        self.data = {
            "email": "phony_mail",
            "first_name": "phony_first_name",
            "last_name": "phony_last_name",
            "cover": "phony_cover",
        }
        self.extractor = profileextractors.FacebookExtractor()

    def test_extract_area(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_area(self.data)

    def test_extract_city(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_city(self.data)

    def test_extract_country(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_country(self.data)

    def test_extract_delivery(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_delivery(self.data)

    def test_extract_email(self):
        result = self.extractor.extract_email(self.data)
        self.assertEqual(result, self.data["email"])

    def test_extract_fax(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_fax(self.data)

    def test_extract_first_name(self):
        result = self.extractor.extract_first_name(self.data)
        self.assertEqual(result, self.data["first_name"])

    def test_extract_last_name(self):
        result = self.extractor.extract_last_name(self.data)
        self.assertEqual(result, self.data["last_name"])

    def test_extract_organization(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_organization(self.data)

    def test_extract_position(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_position(self.data)

    def test_extract_profile(self):
        result = self.extractor.extract_profile(self.data)
        self.assertEqual(result, self.data["cover"])

    def test_extract_voice(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_voice(self.data)

    def test_extract_zipcode(self):
        with self.assertRaises(NotImplementedError):
            self.extractor.extract_zipcode(self.data)


class LinkedInExtractorTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super(LinkedInExtractorTestCase, self).setUp()
        self.data = {
            "id": "REDACTED",
            "firstName": {
                "localized": {
                    "en_US": "Tina"
                },
                "preferredLocale": {
                    "country": "US",
                    "language": "en"
                }
            },
            "lastName": {
                "localized": {
                    "en_US": "Belcher"
                },
                "preferredLocale": {
                    "country": "US",
                    "language": "en"
                }
            },
            "profilePicture": {
                "displayImage": "urn:li:digitalmediaAsset:B54328XZFfe2134zTyq"
            },
            "elements": [
                {
                    "handle": "urn:li:emailAddress:3775708763",
                    "handle~": {
                        "emailAddress": "hsimpson@linkedin.com"
                    }
                }
            ]
        }
        self.extractor = profileextractors.LinkedInExtractor()

    def test_extract_email(self):
        result = self.extractor.extract_email(self.data)
        self.assertEqual(
            result,
            self.data["elements"][0]["handle~"]["emailAddress"]
        )

    def test_extract_first_name(self):
        result = self.extractor.extract_first_name(self.data)
        self.assertEqual(
            result,
            self.data["firstName"]["localized"]["en_US"]
        )

    def test_extract_last_name(self):
        result = self.extractor.extract_last_name(self.data)
        self.assertEqual(
            result,
            self.data["lastName"]["localized"]["en_US"]
        )
