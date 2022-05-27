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

from unittest import TestCase
from geonode.base.populate_test_data import create_single_dataset
from geonode.resource.utils import metadata_storers
from geonode.tests.base import GeoNodeBaseTestSupport

import os
import math
from django.conf import settings
from django.test import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from user_messages.models import Message

from geonode import geoserver
from geonode.decorators import on_ogc_backend
from geonode.base.auth import get_or_create_token

from geonode.utils import forward_mercator, inverse_mercator


class GeoNodeSmokeTests(GeoNodeBaseTestSupport):

    GEOSERVER = False

    def setUp(self):
        super().setUp()

        # If Geoserver is not running
        # avoid running tests that call those views.
        if "GEOSERVER" in os.environ.keys():
            self.GEOSERVER = True

    def tearDown(self):
        pass

    # Basic Pages #

    def test_home_page(self):
        '''Test if the homepage renders.'''
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_help_page(self):
        '''Test help page renders.'''

        response = self.client.get(reverse('help'))
        self.assertEqual(response.status_code, 200)

    def test_developer_page(self):
        '''Test help page renders.'''

        response = self.client.get(reverse('help'))
        self.assertEqual(response.status_code, 200)

    # Dataset Pages #

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_dataset_acls(self):
        'Test if the data/acls endpoint renders.'
        response = self.client.get(reverse('dataset_acls'))
        self.assertEqual(response.status_code, 401)

    # People Pages #

    def test_profile_list(self):
        '''Test the profiles page renders.'''

        response = self.client.get(reverse('profile_browse'))
        self.assertEqual(response.status_code, 200)

    @override_settings(USE_GEOSERVER=False)
    def test_profiles(self):
        '''Test that user profile pages render.'''
        self.client.login(username='admin', password='admin')
        response = self.client.get(reverse('profile_detail', args=['admin']))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('profile_detail', args=['norman']))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse(
                'profile_detail',
                args=['a.fancy.username.123']))
        self.assertEqual(response.status_code, 404)

    def test_csw_endpoint(self):
        '''Test that the CSW endpoint is correctly configured.'''
        response = self.client.get(reverse('csw_global_dispatch'))
        self.assertEqual(response.status_code, 200)

    def test_opensearch_description(self):
        '''Test that the local OpenSearch endpoint is correctly configured.'''
        response = self.client.get(reverse('opensearch_dispatch'))
        self.assertEqual(response.status_code, 200)

    # Settings Tests #

    def test_settings_geoserver_location(self):
        '''Ensure GEOSERVER_LOCATION variable ends with /'''
        self.assertTrue(settings.GEOSERVER_LOCATION.endswith('/'))


class GeoNodeUtilsTests(GeoNodeBaseTestSupport):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    # Some other Stuff

    def test_forward_mercator(self):
        arctic = forward_mercator((0, 85))
        antarctic = forward_mercator((0, -85))
        hawaii = forward_mercator((-180, 0))
        phillipines = forward_mercator((180, 0))
        ne = forward_mercator((180, 90))
        sw = forward_mercator((-180, -90))

        inf_test = forward_mercator(
            (-8.988465674311579e+307, -8.988465674311579e+307)
        )

        self.assertEqual(inf_test[0], float('-inf'))
        self.assertEqual(inf_test[1], float('-inf'))

        self.assertEqual(round(arctic[0]), 0, "Arctic longitude is correct")
        self.assertEqual(
            round(
                arctic[1]),
            19971869,
            "Arctic latitude is correct")

        self.assertEqual(
            round(
                antarctic[0]),
            0,
            "Antarctic longitude is correct")
        self.assertEqual(
            round(
                antarctic[1]), -19971869, "Antarctic latitude is correct")

        self.assertEqual(
            round(
                hawaii[0]), -20037508, "Hawaiian lon is correct")
        self.assertEqual(round(hawaii[1]), 0, "Hawaiian lat is correct")

        self.assertEqual(
            round(
                phillipines[0]),
            20037508,
            "Phillipines lon is correct")
        self.assertEqual(
            round(
                phillipines[1]),
            0,
            "Phillipines lat is correct")

        self.assertEqual(round(ne[0]), 20037508, "NE lon is correct")
        self.assertTrue(ne[1] > 50000000, "NE lat is correct")

        self.assertEqual(round(sw[0]), -20037508, "SW lon is correct")
        self.assertTrue(math.isinf(sw[1]), "SW lat is correct")

        # verify behavior for invalid y values
        self.assertEqual(float('-inf'), forward_mercator((0, 135))[1])
        self.assertEqual(float('-inf'), forward_mercator((0, -135))[1])

    def test_inverse_mercator(self):
        arctic = inverse_mercator(forward_mercator((0, 85)))
        antarctic = inverse_mercator(forward_mercator((0, -85)))
        hawaii = inverse_mercator(forward_mercator((-180, 0)))
        phillipines = inverse_mercator(forward_mercator((180, 0)))
        ne = inverse_mercator(forward_mercator((180, 90)))
        sw = inverse_mercator(forward_mercator((-180, -90)))

        self.assertAlmostEqual(
            arctic[0],
            0.0,
            places=3,
            msg="Arctic longitude is correct")
        self.assertAlmostEqual(
            arctic[1],
            85.0,
            places=3,
            msg="Arctic latitude is correct")

        self.assertAlmostEqual(
            antarctic[0],
            0.0,
            places=3,
            msg="Antarctic longitude is correct")
        self.assertAlmostEqual(
            antarctic[1], -85.0, places=3, msg="Antarctic latitude is correct")

        self.assertAlmostEqual(
            hawaii[0], -180.0, msg="Hawaiian lon is correct")
        self.assertAlmostEqual(hawaii[1], 0.0, places=3, msg="Hawaiian lat is correct")

        self.assertAlmostEqual(
            phillipines[0],
            180.0,
            places=3,
            msg="Phillipines lon is correct")
        self.assertAlmostEqual(
            phillipines[1],
            0.0,
            places=3,
            msg="Phillipines lat is correct")

        self.assertAlmostEqual(ne[0], 180.0, places=3, msg="NE lon is correct")
        self.assertAlmostEqual(ne[1], 90.0, places=3, msg="NE lat is correct")

        self.assertAlmostEqual(sw[0], -180.0, places=3, msg="SW lon is correct")
        self.assertAlmostEqual(sw[1], -90.0, places=3, msg="SW lat is correct")

    def test_split_query(self):
        query = 'alpha "beta gamma"   delta  '
        from geonode.utils import _split_query
        keywords = _split_query(query)
        self.assertEqual(keywords[0], "alpha")
        self.assertEqual(keywords[1], "beta gamma")
        self.assertEqual(keywords[2], "delta")


class PermissionViewTests(GeoNodeBaseTestSupport):

    def setUp(self):
        pass

    def tearDown(self):
        pass


class UserMessagesTestCase(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()

        self.user_password = "somepass"
        self.first_user = get_user_model().objects.create_user(
            "someuser",
            "someuser@fakemail.com",
            self.user_password,
            is_active=True)
        self.second_user = get_user_model().objects.create_user(
            "otheruser",
            "otheruser@fakemail.com",
            self.user_password,
            is_active=True)
        first_message = Message.objects.new_message(
            from_user=self.first_user,
            subject="testing message",
            content="some content",
            to_users=[self.second_user]
        )
        self.thread = first_message.thread

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_inbox_renders(self):
        logged_in = self.client.login(
            username=self.first_user.username, password=self.user_password)
        self.assertTrue(logged_in)
        session = self.client.session
        session['access_token'] = get_or_create_token(self.first_user)
        session.save()
        response = self.client.get(reverse("messages_inbox"))
        self.assertTemplateUsed(response, "user_messages/inbox.html")
        self.assertEqual(response.status_code, 200)

    def test_inbox_redirects_when_not_logged_in(self):
        target_url = reverse("messages_inbox")
        response = self.client.get(target_url)
        account_login_url = reverse("account_login")
        self.assertRedirects(
            response,
            f"{settings.SITEURL[:-1]}{account_login_url}?next=http%3A//testserver{target_url}"
        )

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_new_message_renders(self):
        logged_in = self.client.login(
            username=self.first_user.username, password=self.user_password)
        self.assertTrue(logged_in)
        session = self.client.session
        session['access_token'] = get_or_create_token(self.first_user)
        session.save()
        response = self.client.get(
            reverse("message_create", args=(self.first_user.id,)))
        self.assertTemplateUsed(response, "user_messages/message_create.html")
        self.assertEqual(response.status_code, 200)

    def test_new_message_redirects_when_not_logged_in(self):
        target_url = reverse("message_create", args=(self.first_user.id,))
        response = self.client.get(target_url)
        account_login_url = reverse("account_login")
        self.assertRedirects(
            response,
            f"{settings.SITEURL[:-1]}{account_login_url}?next=http%3A//testserver{target_url}"
        )

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_thread_detail_renders(self):
        logged_in = self.client.login(
            username=self.first_user.username, password=self.user_password)
        self.assertTrue(logged_in)
        session = self.client.session
        session['access_token'] = get_or_create_token(self.first_user)
        session.save()
        response = self.client.get(
            reverse("messages_thread_detail", args=(self.thread.id,)))
        self.assertTemplateUsed(response, "user_messages/thread_detail.html")
        self.assertEqual(response.status_code, 200)

    def test_thread_detail_redirects_when_not_logged_in(self):
        target_url = reverse("messages_thread_detail", args=(self.thread.id,))
        response = self.client.get(target_url)
        account_login_url = reverse("account_login")
        self.assertRedirects(
            response,
            f"{settings.SITEURL[:-1]}{account_login_url}?next=http%3A//testserver{target_url}"
        )


'''
Smoke test to explain how the new function for multiple storer will work
Is required to define a fuction that takes 2 parametersand return 2 parameters.
            Parameters:
                    dataset: (Dataset): Dataset instance
                    custom (dict): Custom dict generated by the parser

            Returns:
                    None
'''


class TestMetadataStorers(TestCase):
    def setUp(self):
        self.dataset = create_single_dataset('metadata-storer')
        self.uuid = self.dataset.uuid
        self.abstract = self.dataset.abstract
        self.custom = {
            "processes": {"uuid": "abc123cfde", "abstract": "updated abstract"},
            "second-stage": {"title": "Updated Title", "abstract": "another update"},
        }

    @override_settings(METADATA_STORERS=['geonode.tests.smoke.dummy_metadata_storer'])
    def test_will_use_single_storers_defined(self):
        metadata_storers(self.dataset, self.custom)
        self.assertEqual('abc123cfde', self.dataset.uuid)
        self.assertEqual("updated abstract", self.dataset.abstract)

    @override_settings(
        METADATA_STORERS=[
            "geonode.tests.smoke.dummy_metadata_storer",
            "geonode.tests.smoke.dummy_metadata_storer2",
        ]
    )
    def test_will_use_multiple_storers_defined(self):
        dataset = metadata_storers(self.dataset, self.custom)
        self.assertEqual('abc123cfde', dataset.uuid)
        self.assertEqual("another update", dataset.abstract)
        self.assertEqual("Updated Title", dataset.title)


'''
Just a dummy function required for the smoke test above
'''


def dummy_metadata_storer(dataset, custom):
    if custom.get('processes', None):
        for key, value in custom['processes'].items():
            setattr(dataset, key, value)


def dummy_metadata_storer2(dataset, custom):
    if custom.get('second-stage', None):
        for key, value in custom['second-stage'].items():
            setattr(dataset, key, value)
