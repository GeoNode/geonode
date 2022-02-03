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

from unittest.mock import patch
from datetime import datetime, timedelta
from tastypie.test import ResourceTestCaseMixin

from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from guardian.shortcuts import get_anonymous_user

from geonode import geoserver
from geonode.base.models import ExtraMetadata
from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.utils import check_ogc_backend
from geonode.decorators import on_ogc_backend
from geonode.documents.models import Document
from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.populate_test_data import all_public


class PermissionsApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        all_public()
        self.perm_spec = {"users": {}, "groups": {}}

    def test_layer_get_list_unauth_all_public(self):
        """
        Test that the correct number of layers are returned when the
        client is not logged in and all are public
        """

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 8)

    def test_layers_get_list_unauth_some_public(self):
        """
        Test that if a layer is not public then not all are returned when the
        client is not logged in
        """

        layer = Layer.objects.all()[0]
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 7)

    def test_layers_get_list_auth_some_public(self):
        """
        Test that if a layer is not public then all are returned if the
        client is not logged in
        """
        layer = Layer.objects.all().first()
        layer.set_permissions(self.perm_spec)

        auth = self.create_basic(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url, authentication=auth)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 7)

    def test_layer_get_list_layer_private_to_one_user(self):
        """
        Test that if a layer is only visible by admin, then does not appear
        in the unauthenticated list nor in the list when logged is as bobby
        """

        perm_spec = {"users": {"admin": ['view_resourcebase']}, "groups": {}}
        layer = Layer.objects.first()
        layer.set_permissions(perm_spec)
        resp = self.api_client.get(self.list_url)
        self.assertEqual(len(self.deserialize(resp)['objects']), 7)

        auth = self.create_basic(username='bobby', password='bob')
        resp = self.api_client.get(self.list_url, authentication=auth)
        self.assertEqual(len(self.deserialize(resp)['objects']), 7)

        auth = self.create_basic(username=self.user, password=self.passwd)
        resp = self.api_client.get(self.list_url, authentication=auth)
        self.assertEqual(len(self.deserialize(resp)['objects']), 7)

        layer.is_published = False
        layer.save()

        # with resource publishing
        with self.settings(RESOURCE_PUBLISHING=True):
            resp = self.api_client.get(self.list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

            auth = self.create_basic(username='bobby', password='bob')
            resp = self.api_client.get(self.list_url, authentication=auth)
            self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

            auth = self.create_basic(username=self.user, password=self.passwd)
            resp = self.api_client.get(self.list_url, authentication=auth)
            self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

    def test_layer_get_detail_unauth_layer_not_public(self):
        """
        Test that layer detail gives 404 when not public and not logged in
        """
        perm_spec = {"users": {"admin": ['view_resourcebase']}, "groups": {}}
        layer = Layer.objects.first()
        layer.set_permissions(perm_spec)
        layer.clear_dirty_state()
        Layer.objects.filter(id=layer.id).update(is_approved=True, is_published=True)
        self.api_client.client.logout()
        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        import logging
        logging.getLogger(__name__).error(self.deserialize(resp))
        self.assertFalse(layer.id in self.deserialize(resp)['objects'])

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(
            self.list_url,
            authentication=self.create_basic(username=self.user, password=self.passwd))
        self.assertValidJSONResponse(resp)
        # TODO: no way to pass authentication to Tastypie!
        # self.assertTrue(layer.id in self.deserialize(resp)['objects'])
        self.assertEqual(len(self.deserialize(resp)['objects']), 8)

        # with delayed security
        with self.settings(DELAYED_SECURITY_SIGNALS=True):
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                from geonode.security.utils import sync_geofence_with_guardian
                sync_geofence_with_guardian(layer, perm_spec)
                self.assertTrue(layer.dirty_state)

                self.client.login(username=self.user, password=self.passwd)
                resp = self.client.get(self.list_url)
                self.assertEqual(len(self.deserialize(resp)['objects']), 7)

                self.client.logout()
                resp = self.client.get(self.list_url)
                self.assertEqual(len(self.deserialize(resp)['objects']), 7)

                from django.contrib.auth import get_user_model
                get_user_model().objects.create(
                    username='imnew',
                    password='pbkdf2_sha256$12000$UE4gAxckVj4Z$N\
                    6NbOXIQWWblfInIoq/Ta34FdRiPhawCIZ+sOO3YQs=')
                self.client.login(username='imnew', password='thepwd')
                resp = self.client.get(self.list_url)
                self.assertEqual(len(self.deserialize(resp)['objects']), 7)

    def test_new_user_has_access_to_old_layers(self):
        """Test that a new user can access the public available layers"""
        from django.contrib.auth import get_user_model
        get_user_model().objects.create(
            username='imnew',
            password='pbkdf2_sha256$12000$UE4gAxckVj4Z$N\
            6NbOXIQWWblfInIoq/Ta34FdRiPhawCIZ+sOO3YQs=')

        auth = self.create_basic(username='imnew', password='thepwd')
        resp = self.api_client.get(self.list_url, authentication=auth)
        self.assertValidJSONResponse(resp)
        self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

        # with delayed security
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            _ogc_geofence_enabled = settings.OGC_SERVER
            try:
                _ogc_geofence_enabled['default']['GEOFENCE_SECURITY_ENABLED'] = True
                with self.settings(DELAYED_SECURITY_SIGNALS=True,
                                   OGC_SERVER=_ogc_geofence_enabled,
                                   DEFAULT_ANONYMOUS_VIEW_PERMISSION=True):
                    layer = Layer.objects.all().first()
                    layer.set_default_permissions()
                    layer.refresh_from_db()
                    self.assertTrue(layer.dirty_state)

                    self.client.login(username=self.user, password=self.passwd)
                    resp = self.client.get(self.list_url)
                    self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

                    self.client.logout()
                    resp = self.client.get(self.list_url)
                    self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

                    self.client.login(username='imnew', password='thepwd')
                    resp = self.client.get(self.list_url)
                    self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)
            finally:
                _ogc_geofence_enabled['default']['GEOFENCE_SECURITY_ENABLED'] = False


class OAuthApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
    def setUp(self):
        super().setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self._user = get_user_model().objects.get(username=self.user)
        self.token = get_or_create_token(self._user)
        self.auth_header = f'Bearer {self.token}'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        all_public()
        self.perm_spec = {"users": {}, "groups": {}}

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_outh_token(self):

        with self.settings(SESSION_EXPIRED_CONTROL_ENABLED=False, DELAYED_SECURITY_SIGNALS=False):
            # all public
            resp = self.api_client.get(self.list_url)
            self.assertValidJSONResponse(resp)
            self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

            perm_spec = {"users": {"admin": ['view_resourcebase']}, "groups": {}}
            layer = Layer.objects.all()[0]
            layer.set_permissions(perm_spec)
            resp = self.api_client.get(self.list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

            resp = self.api_client.get(self.list_url, authentication=self.auth_header)
            self.assertGreaterEqual(len(self.deserialize(resp)['objects']), 7)

            layer.is_published = False
            layer.save()


class SearchApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    """Test the search"""

    def setUp(self):
        super().setUp()

        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        all_public()
        self.norman = get_user_model().objects.get(username="norman")
        self.norman.groups.add(Group.objects.get(name='anonymous'))
        self.test_user = get_user_model().objects.get(username='test_user')
        self.test_user.groups.add(Group.objects.get(name='anonymous'))
        self.bar = GroupProfile.objects.get(slug='bar')
        self.anonymous_user = get_anonymous_user()
        self.profiles_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'profiles'})
        self.groups_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'groups'})

    def test_profiles_filters(self):
        """Test profiles filtering"""

        with self.settings(API_LOCKDOWN=False):
            filter_url = self.profiles_list_url

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 9)

            filter_url = f"{self.profiles_list_url}?name__icontains=norm"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 1)

            filter_url = f"{self.profiles_list_url}?name__icontains=NoRmAN"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 1)

            filter_url = f"{self.profiles_list_url}?name__icontains=bar"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    def test_groups_filters(self):
        """Test groups filtering"""

        with self.settings(API_LOCKDOWN=False):

            filter_url = self.groups_list_url

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 1)

            filter_url = f"{self.groups_list_url}?name__icontains=bar"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 1)

            filter_url = f"{self.groups_list_url}?name__icontains=BaR"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 1)

            filter_url = f"{self.groups_list_url}?name__icontains=foo"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    def test_category_filters(self):
        """Test category filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different categories
        filter_url = f"{self.list_url}?category__identifier=location"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)

        filter_url = f"{self.list_url}?category__identifier__in=location&category__identifier__in=biota"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 5)

    def test_metadata_filters(self):
        """Test category filtering"""
        _r = Layer.objects.first()
        _m = ExtraMetadata.objects.create(
            resource=_r,
            metadata={
                "name": "metadata-updated",
                "slug": "metadata-slug-updated",
                "help_text": "this is the help text-updated",
                "field_type": "str-updated",
                "value": "my value-updated",
                "category": "category"
            }
        )
        _r.metadata.add(_m)
        # check we get the correct layers number returnered filtering on one
        # and then two different categories
        filter_url = f"{self.list_url}?metadata__category=category"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        filter_url = f"{self.list_url}?metadata__category=not-existing-category"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

    def test_tag_filters(self):
        """Test keywords filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different keywords
        filter_url = f"{self.list_url}?keywords__slug=layertagunique"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        filter_url = f"{self.list_url}?keywords__slug__in=layertagunique&keywords__slug__in=populartag"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 8)

    def test_owner_filters(self):
        """Test owner filtering"""

        # check we get the correct layers number returnered filtering on one
        # and then two different owners
        filter_url = f"{self.list_url}?owner__username=user1"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

        filter_url = f"{self.list_url}?owner__username__in=user1&owner__username__in=foo"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

    def test_title_filter(self):
        """Test title filtering"""

        # check we get the correct layers number returnered filtering on the
        # title
        filter_url = f"{self.list_url}?title=layer2"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)

    def test_date_filter(self):
        """Test date filtering"""

        # check we get the correct layers number returnered filtering on the
        # dates
        step = timedelta(days=60)
        now = datetime.now()
        fstring = '%Y-%m-%d'

        def to_date(val):
            return val.date().strftime(fstring)

        d1 = to_date(now - step)
        filter_url = f"{self.list_url}?date__exact={d1}"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

        d3 = to_date(now - (3 * step))
        filter_url = f"{self.list_url}?date__gte={d3}"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 3)

        d4 = to_date(now - (4 * step))
        filter_url = f"{self.list_url}?date__range={d4},{to_date(now)}"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 4)

    def test_extended_text_filter(self):
        """Test that the extended text filter works as expected"""
        filter_url = f"{self.list_url}?title__icontains=layer2&abstract__icontains=layer2&purpose__icontains=layer2&f_method=or"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 1)


# noinspection DuplicatedCode
@override_settings(API_LOCKDOWN=True)
class LockdownApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    """Test the api lockdown functionality"""

    def setUp(self):
        super().setUp()
        self.profiles_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'profiles'})
        self.groups_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'groups'})
        self.owners_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'owners'})
        self.tag_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'keywords'})
        self.region_list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'regions'})
        self.bobby = get_user_model().objects.get(username='bobby')

    def test_api_lockdown_false(self):
        # test if results are returned for anonymous users if API_LOCKDOWN is set to False in settings
        filter_url = self.profiles_list_url

        with self.settings(API_LOCKDOWN=False):
            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)['objects']), 9)

    def test_profiles_lockdown(self):
        filter_url = self.profiles_list_url
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

        # now test with logged in user
        self.assertTrue(self.api_client.client.login(username='bobby', password='bob'))
        auth = self.create_basic(username='bobby', password='bob')
        resp = self.api_client.get(filter_url, authentication=auth)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 9)
        # Returns limitted info about other users
        profiles = self.deserialize(resp)['objects']
        for profile in profiles:
            if profile['username'] == 'bobby':
                self.assertEquals(profile.get('email'), self.bobby.email)
            else:
                self.assertIsNone(profile.get('email'))

    def test_owners_lockdown(self):
        filter_url = self.owners_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

        # now test with logged in user
        self.assertTrue(self.api_client.client.login(username='bobby', password='bob'))
        auth = self.create_basic(username='bobby', password='bob')
        resp = self.api_client.get(filter_url, authentication=auth)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 9)
        # Returns limitted info about other users
        owners = self.deserialize(resp)['objects']
        for owner in owners:
            if owner['username'] == 'bobby':
                self.assertEquals(owner.get('email'), self.bobby.email)
            else:
                self.assertIsNone(owner.get('email'))
                self.assertIsNone(owner.get('first_name'))

    def test_groups_lockdown(self):
        filter_url = self.groups_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

        # now test with logged in user
        self.assertTrue(self.api_client.client.login(username='bobby', password='bob'))
        auth = self.create_basic(username='bobby', password='bob')
        resp = self.api_client.get(filter_url, authentication=auth)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 2)

    def test_regions_lockdown(self):
        filter_url = self.region_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

        self.assertTrue(self.api_client.client.login(username='bobby', password='bob'))
        auth = self.create_basic(username='bobby', password='bob')
        resp = self.api_client.get(filter_url, authentication=auth)
        self.assertValidJSONResponse(resp)
        self.assertTrue(len(self.deserialize(resp)['objects']) >= 200)

    def test_tags_lockdown(self):
        filter_url = self.tag_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 0)

        self.assertTrue(self.api_client.client.login(username='bobby', password='bob'))
        auth = self.create_basic(username='bobby', password='bob')
        resp = self.api_client.get(filter_url, authentication=auth)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)['objects']), 5)


class ThesaurusKeywordResourceTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):

    #  loading test thesausuri
    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json',
        "test_thesaurus.json"
    ]

    def setUp(self):
        super().setUp()
        all_public()
        self.list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

    def test_api_will_return_a_valid_json_response(self):
        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)

    def test_will_return_empty_if_the_thesaurus_does_not_exists(self):
        url = f"{self.list_url}?thesaurus=invalid-identifier"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 0)

    def test_will_return_keywords_for_the_selected_thesaurus_if_exists(self):
        url = f"{self.list_url}?thesaurus=inspire-theme"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 36)

    def test_will_return_empty_if_the_alt_label_does_not_exists(self):
        url = f"{self.list_url}?alt_label=invalid-alt_label"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 0)

    def test_will_return_keywords_for_the_selected_alt_label_if_exists(self):
        url = f"{self.list_url}?alt_label=ac"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 1)

    def test_will_return_empty_if_the_kaywordId_does_not_exists(self):
        url = f"{self.list_url}?id=12365478954862"
        resp = self.api_client.get(url)
        print(self.deserialize(resp))
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 0)

    @patch("geonode.api.api.get_language")
    def test_will_return_expected_keyword_label_for_existing_lang(self, lang):
        lang.return_value = "de"
        url = f"{self.list_url}?thesaurus=inspire-theme"
        resp = self.api_client.get(url)
        # the german translations exists, for the other labels, the alt_label will be used
        expected_labels = [
            "", "ac", "Adressen", "af", "am", "au", "br", "bu",
            "cp", "ef", "el", "er", "foo_keyword", "ge", "gg", "gn", "hb", "hh",
            "hy", "lc", "lu", "mf", "mr", "nz", "of", "oi", "pd",
            "pf", "ps", "rs", "sd", "so", "sr", "su", "tn", "us"
        ]
        actual_labels = [x["alt_label"] for x in self.deserialize(resp)["objects"]]
        self.assertValidJSONResponse(resp)
        self.assertListEqual(expected_labels, actual_labels)

    @patch("geonode.api.api.get_language")
    def test_will_return_default_keyword_label_for_not_existing_lang(self, lang):
        lang.return_value = "ke"
        url = f"{self.list_url}?thesaurus=inspire-theme"
        resp = self.api_client.get(url)
        # no translations exists, the alt_label will be used for all keywords
        expected_labels = [
            "", "ac", "ad", "af", "am", "au", "br", "bu",
            "cp", "ef", "el", "er", "foo_keyword", "ge", "gg", "gn", "hb", "hh",
            "hy", "lc", "lu", "mf", "mr", "nz", "of", "oi", "pd",
            "pf", "ps", "rs", "sd", "so", "sr", "su", "tn", "us",
        ]
        actual_labels = [x["alt_label"] for x in self.deserialize(resp)["objects"]]
        self.assertValidJSONResponse(resp)
        self.assertListEqual(expected_labels, actual_labels)


class LayerResourceTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username="admin")
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        all_public()
        self.token = get_or_create_token(self.user)
        self.auth_header = f'Bearer {self.token}'

    def test_the_api_should_return_all_layers_with_metadata_false(self):

        resp = self.api_client.get(self.list_url, authentication=self.auth_header)
        self.assertValidJSONResponse(resp)
        self.assertEqual(8, resp.json()["meta"]["total_count"])

    def test_the_api_should_return_all_layers_with_metadata_true(self):

        url = f"{self.list_url}?metadata_only=True"
        resp = self.api_client.get(url, authentication=self.auth_header)
        self.assertValidJSONResponse(resp)
        self.assertEqual(1, resp.json()["meta"]["total_count"])


class DocumentResourceTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        super().setUp()
        all_public()
        self.user = get_user_model().objects.get(username="admin")
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'documents'})

    def test_the_api_should_return_all_documents_with_metadata_false(self):
        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 9)

    def test_the_api_should_return_all_documents_with_metadata_true(self):
        url = f"{self.list_url}?metadata_only=True"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 1)


class MapResourceTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        super().setUp()
        all_public()
        self.user = get_user_model().objects.get(username="admin")
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'maps'})

    def test_the_api_should_return_all_maps_with_metadata_false(self):
        resp = self.api_client.get(self.list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 9)

    def test_the_api_should_return_all_maps_with_metadata_true(self):
        url = f"{self.list_url}?metadata_only=True"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 1)


class TopicCategoryResourceTest(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
    fixtures = [
        'initial_data.json',
        'group_test_data.json',
        'default_oauth_apps.json'
    ]

    def setUp(self):
        super().setUp()
        self.user = get_user_model().objects.get(username="admin")
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'categories'})

    def test_the_api_should_return_all_maps_with_metadata_false(self):
        url = f"{self.list_url}?type=map"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        actual = sum([x['count'] for x in resp.json()['objects']])
        self.assertEqual(9, actual)

    def test_the_api_should_return_all_maps_with_metadata_true(self):
        x = Map.objects.get(title='map metadata true')
        x.metadata_only = False
        x.save()
        url = f"{self.list_url}?type=map"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        # by adding a new layer, the total should increase
        actual = sum([x['count'] for x in resp.json()['objects']])
        self.assertEqual(10, actual)

    def test_the_api_should_return_all_document_with_metadata_false(self):
        url = f"{self.list_url}?type=document"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        actual = sum([x['count'] for x in resp.json()['objects']])
        self.assertEqual(9, actual)

    def test_the_api_should_return_all_document_with_metadata_true(self):
        x = Document.objects.get(title='doc metadata true')
        x.metadata_only = False
        x.save()
        url = f"{self.list_url}?type=document"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        # by adding a new layer, the total should increase
        actual = sum([x['count'] for x in resp.json()['objects']])
        self.assertEqual(10, actual)
