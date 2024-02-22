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
import logging
from datetime import datetime, timedelta
from tastypie.test import ResourceTestCaseMixin, TestApiClient
from unittest.mock import patch
from urllib.parse import urlencode
from uuid import uuid4

from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from guardian.shortcuts import get_anonymous_user

from geonode import geoserver
from geonode.geoserver.manager import GeoServerResourceManager
from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.documents.models import Document
from geonode.base.models import (
    ExtraMetadata,
    Thesaurus,
    ThesaurusLabel,
    ThesaurusKeyword,
    ThesaurusKeywordLabel,
    ResourceBase,
)
from geonode.utils import check_ogc_backend
from geonode.decorators import on_ogc_backend
from geonode.groups.models import GroupProfile
from geonode.base.auth import get_or_create_token
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.populate_test_data import all_public, create_models, remove_models


logger = logging.getLogger(__name__)


class UserAndTokenInfoApiTests(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def test_userinfo_response(self):
        userinfo_url = reverse("userinfo")
        _user = get_user_model().objects.get(username="bobby")
        self.client.login(username="bobby", password="bob")
        response = self.client.get(userinfo_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sub"], str(_user.pk))
        self.client.logout()
        response = self.client.get(userinfo_url)
        self.assertEqual(response.status_code, 401)

    def test_tokeninfo_response(self):
        tokeninfo_url = reverse("tokeninfo")
        _user = get_user_model().objects.get(username="bobby")
        token = get_or_create_token(_user)
        response = self.client.post(tokeninfo_url, data={"token": token})
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["access_token"], token.token)
        self.assertEqual(response_json["user_id"], _user.pk)


class PermissionsApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
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
        self.user = "admin"
        self.passwd = "admin"
        self.perm_spec = {"users": {}, "groups": {}}

    def test_dataset_get_list_unauth_all_public(self):
        """
        Test that the correct number of layers are returned when the
        client is not logged in and all are public
        """
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})
        resp = self.api_client.get(list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 8)

    def test_datasets_get_list_unauth_some_public(self):
        """
        Test that if a layer is not public then not all are returned when the
        client is not logged in
        """
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        layer = Dataset.objects.first()
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 7)

    def test_datasets_get_list_auth_some_public(self):
        """
        Test that if a layer is not public then all are returned if the
        client is not logged in
        """
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        self.api_client.client.login(username=self.user, password=self.passwd)
        layer = Dataset.objects.first()
        layer.set_permissions(self.perm_spec)

        resp = self.api_client.get(list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 8)

    def test_dataset_get_list_dataset_private_to_one_user(self):
        """
        Test that if a layer is only visible by admin, then does not appear
        in the unauthenticated list nor in the list when logged is as bobby
        """
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        perm_spec = {"users": {"admin": ["view_resourcebase"]}, "groups": {}}
        layer = Dataset.objects.first()
        layer.set_permissions(perm_spec)
        resp = self.api_client.get(list_url)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 7)

        self.api_client.client.login(username="bobby", password="bob")
        resp = self.api_client.get(list_url)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 7)

        self.api_client.client.login(username=self.user, password=self.passwd)
        resp = self.api_client.get(list_url)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 8)

        layer.is_published = False
        layer.save()

        # with resource publishing
        with self.settings(RESOURCE_PUBLISHING=True):
            resp = self.api_client.get(list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

            self.api_client.client.login(username="bobby", password="bob")
            resp = self.api_client.get(list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

            self.api_client.client.login(username=self.user, password=self.passwd)
            resp = self.api_client.get(list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

    def test_dataset_get_detail_unauth_dataset_not_public(self):
        """
        Test that layer detail gives 404 when not public and not logged in
        """
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        resp = self.client.get(list_url)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 8)

        layer = Dataset.objects.first()
        layer.set_permissions(self.perm_spec)
        layer.clear_dirty_state()

        resp = self.client.get(list_url)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 7)
        self.assertHttpNotFound(self.client.get(f"{list_url + str(layer.id)}/"))

        self.client.login(username=self.user, password=self.passwd)
        self.assertValidJSONResponse(self.client.get(f"{list_url + str(layer.id)}/"))

        # with delayed security
        with self.settings(DELAYED_SECURITY_SIGNALS=True, GEOFENCE_SECURITY_ENABLED=True):
            if check_ogc_backend(geoserver.BACKEND_PACKAGE):
                gm = GeoServerResourceManager()
                gm.set_permissions(layer.uuid, instance=layer, permissions=self.perm_spec)
                self.assertTrue(layer.dirty_state)

                self.client.login(username=self.user, password=self.passwd)
                resp = self.client.get(list_url)
                self.assertEqual(len(self.deserialize(resp)["objects"]), 7)  # admin can't see resources in dirty_state

                self.client.logout()
                resp = self.client.get(list_url)
                self.assertEqual(len(self.deserialize(resp)["objects"]), 7)

                from django.contrib.auth import get_user_model

                get_user_model().objects.create(
                    username="imnew",
                    password="pbkdf2_sha256$12000$UE4gAxckVj4Z$N6NbOXIQWWblfInIoq/Ta34FdRiPhawCIZ+sOO3YQs=",
                )
                self.client.login(username="imnew", password="thepwd")
                resp = self.client.get(list_url)
                self.assertEqual(len(self.deserialize(resp)["objects"]), 7)

    def test_new_user_has_access_to_old_datasets(self):
        """Test that a new user can access the public available layers"""
        from django.contrib.auth import get_user_model

        get_user_model().objects.create(
            username="imnew",
            password="pbkdf2_sha256$12000$UE4gAxckVj4Z$N\
            6NbOXIQWWblfInIoq/Ta34FdRiPhawCIZ+sOO3YQs=",
        )

        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        self.api_client.client.login(username="imnew", password="thepwd")
        resp = self.api_client.get(list_url)
        self.assertValidJSONResponse(resp)
        self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

        # with delayed security
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            _ogc_geofence_enabled = settings.OGC_SERVER
            try:
                _ogc_geofence_enabled["default"]["GEOFENCE_SECURITY_ENABLED"] = True
                with self.settings(
                    DELAYED_SECURITY_SIGNALS=True,
                    OGC_SERVER=_ogc_geofence_enabled,
                    DEFAULT_ANONYMOUS_VIEW_PERMISSION=True,
                ):
                    layer = Dataset.objects.first()
                    layer.set_default_permissions()
                    layer.refresh_from_db()
                    # self.assertTrue(layer.dirty_state)

                    self.client.login(username=self.user, password=self.passwd)
                    resp = self.client.get(list_url)
                    self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

                    self.client.logout()
                    resp = self.client.get(list_url)
                    self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

                    self.client.login(username="imnew", password="thepwd")
                    resp = self.client.get(list_url)
                    self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)
            finally:
                _ogc_geofence_enabled["default"]["GEOFENCE_SECURITY_ENABLED"] = False

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_outh_token(self):
        user = "admin"
        _user = get_user_model().objects.get(username=user)
        token = get_or_create_token(_user)
        auth_header = f"Bearer {token}"
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        with self.settings(SESSION_EXPIRED_CONTROL_ENABLED=False, DELAYED_SECURITY_SIGNALS=False):
            # all public
            resp = self.api_client.get(list_url)
            self.assertValidJSONResponse(resp)
            self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

            perm_spec = {"users": {"admin": ["view_resourcebase"]}, "groups": {}}
            layer = Dataset.objects.first()
            layer.set_permissions(perm_spec)
            resp = self.api_client.get(list_url)
            self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

            resp = self.api_client.get(list_url, authentication=auth_header)
            self.assertGreaterEqual(len(self.deserialize(resp)["objects"]), 7)

            layer.is_published = False
            layer.save()

    @override_settings(API_LOCKDOWN=True)
    def test_api_lockdown_false(self):
        profiles_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "profiles"})

        # test if results are returned for anonymous users if API_LOCKDOWN is set to False in settings
        filter_url = profiles_list_url

        with self.settings(API_LOCKDOWN=False):
            # anonymous
            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 0)
            # admin
            self.api_client.client.login(username="admin", password="admin")
            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 9)

    @override_settings(API_LOCKDOWN=True)
    def test_profiles_lockdown(self):
        profiles_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "profiles"})

        filter_url = profiles_list_url
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

        # now test with logged in user
        self.api_client.client.login(username="bobby", password="bob")
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 6)
        # Returns limitted info about other users
        bobby = get_user_model().objects.get(username="bobby")
        profiles = self.deserialize(resp)["objects"]
        for profile in profiles:
            if profile["username"] == "bobby":
                self.assertEquals(profile.get("email"), bobby.email)
            else:
                self.assertIsNone(profile.get("email"))

    @override_settings(API_LOCKDOWN=True)
    def test_owners_lockdown(self):
        owners_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "owners"})

        filter_url = owners_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

        # now test with logged in user
        self.api_client.client.login(username="bobby", password="bob")
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 6)
        # Returns limitted info about other users
        bobby = get_user_model().objects.get(username="bobby")
        owners = self.deserialize(resp)["objects"]
        for owner in owners:
            if owner["username"] == "bobby":
                self.assertEquals(owner.get("email"), bobby.email)
            else:
                self.assertIsNone(owner.get("email"))
                self.assertIsNone(owner.get("first_name"))

        # now test with logged in admin
        self.api_client.client.login(username="admin", password="admin")
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 9)

    @override_settings(API_LOCKDOWN=True)
    def test_groups_lockdown(self):
        groups_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "groups"})

        filter_url = groups_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

        # now test with logged in user
        self.api_client.client.login(username="bobby", password="bob")
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

    @override_settings(API_LOCKDOWN=True)
    def test_regions_lockdown(self):
        region_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "regions"})

        filter_url = region_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

        self.api_client.client.login(username="bobby", password="bob")
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertTrue(len(self.deserialize(resp)["objects"]) >= 200)

    @override_settings(API_LOCKDOWN=True)
    def test_tags_lockdown(self):
        tag_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "keywords"})

        filter_url = tag_list_url

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

        self.api_client.client.login(username="bobby", password="bob")
        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 5)


class SearchApiTests(ResourceTestCaseMixin, GeoNodeBaseTestSupport):
    """Test the search"""

    #  loading test thesausuri and initial data
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json", "test_thesaurus.json"]

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

        self.norman = get_user_model().objects.get(username="norman")
        self.norman.groups.add(Group.objects.get(name="anonymous"))
        self.test_user = get_user_model().objects.get(username="test_user")
        self.test_user.groups.add(Group.objects.get(name="anonymous"))
        self.bar = GroupProfile.objects.get(slug="bar")
        self.anonymous_user = get_anonymous_user()
        self.profiles_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "profiles"})
        self.groups_list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "groups"})

    def test_profiles_filters(self):
        """Test profiles filtering"""

        with self.settings(API_LOCKDOWN=False):
            filter_url = self.profiles_list_url

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

            filter_url = f"{self.profiles_list_url}?name__icontains=norm"
            # Anonymous
            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

            self.api_client.client.login(username="admin", password="admin")
            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

            filter_url = f"{self.profiles_list_url}?name__icontains=NoRmAN"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

            filter_url = f"{self.profiles_list_url}?name__icontains=bar"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

    def test_groups_filters(self):
        """Test groups filtering"""

        with self.settings(API_LOCKDOWN=False):
            filter_url = self.groups_list_url

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

            filter_url = f"{self.groups_list_url}?name__icontains=bar"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

            filter_url = f"{self.groups_list_url}?name__icontains=BaR"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

            filter_url = f"{self.groups_list_url}?name__icontains=foo"

            resp = self.api_client.get(filter_url)
            self.assertValidJSONResponse(resp)
            self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

    def test_category_filters(self):
        """Test category filtering"""
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        # check we get the correct layers number returnered filtering on one
        # and then two different categories
        filter_url = f"{list_url}?category__identifier=location"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 3)

        filter_url = f"{list_url}?category__identifier__in=location&category__identifier__in=biota"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 5)

    def test_metadata_filters(self):
        """Test category filtering"""
        _r = Dataset.objects.first()
        _m = ExtraMetadata.objects.create(
            resource=_r,
            metadata={
                "name": "metadata-updated",
                "slug": "metadata-slug-updated",
                "help_text": "this is the help text-updated",
                "field_type": "str-updated",
                "value": "my value-updated",
                "category": "category",
            },
        )

        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})
        _r.metadata.add(_m)
        # check we get the correct layers number returnered filtering on one
        # and then two different categories
        filter_url = f"{list_url}?metadata__category=category"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

        filter_url = f"{list_url}?metadata__category=not-existing-category"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

    def test_tag_filters(self):
        """Test keywords filtering"""
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        # check we get the correct layers number returnered filtering on one
        # and then two different keywords
        filter_url = f"{list_url}?keywords__slug=layertagunique"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

        filter_url = f"{list_url}?keywords__slug__in=layertagunique&keywords__slug__in=populartag"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 8)

    def test_owner_filters(self):
        """Test owner filtering"""
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        # check we get the correct layers number returnered filtering on one
        # and then two different owners
        filter_url = f"{list_url}?owner__username=user1"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

        filter_url = f"{list_url}?owner__username__in=user1&owner__username__in=foo"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 2)

    def test_title_filter(self):
        """Test title filtering"""
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        # check we get the correct layers number returnered filtering on the
        # title
        filter_url = f"{list_url}?title=layer2"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

    def test_date_filter(self):
        """Test date filtering"""
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        # check we get the correct layers number returnered filtering on the
        # dates
        step = timedelta(days=60)
        now = datetime.now()
        fstring = "%Y-%m-%d"

        def to_date(val):
            return val.date().strftime(fstring)

        d1 = to_date(now - step)
        filter_url = f"{list_url}?date__exact={d1}"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 0)

        d3 = to_date(now - (3 * step))
        filter_url = f"{list_url}?date__gte={d3}"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 3)

        d4 = to_date(now - (4 * step))
        filter_url = f"{list_url}?date__range={d4},{to_date(now)}"

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 4)

    def test_extended_text_filter(self):
        """Test that the extended text filter works as expected"""
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})

        filter_url = (
            f"{list_url}?title__icontains=layer2&abstract__icontains=layer2&purpose__icontains=layer2&f_method=or"
        )

        resp = self.api_client.get(filter_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(len(self.deserialize(resp)["objects"]), 1)

    def test_the_api_should_return_all_datasets_with_metadata_false(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})
        user = get_user_model().objects.get(username="admin")
        token = get_or_create_token(user)
        auth_header = f"Bearer {token}"

        resp = self.api_client.get(list_url, authentication=auth_header)
        self.assertValidJSONResponse(resp)
        self.assertEqual(Dataset.objects.filter(metadata_only=False).count(), resp.json()["meta"]["total_count"])

    def test_the_api_should_return_all_datasets_with_metadata_true(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "datasets"})
        user = get_user_model().objects.get(username="admin")
        token = get_or_create_token(user)
        auth_header = f"Bearer {token}"

        url = f"{list_url}?metadata_only=True"
        resp = self.api_client.get(url, authentication=auth_header)
        self.assertValidJSONResponse(resp)
        self.assertEqual(Dataset.objects.filter(metadata_only=True).count(), resp.json()["meta"]["total_count"])

    def test_the_api_should_return_all_documents_with_metadata_false(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "documents"})

        resp = self.api_client.get(list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(Document.objects.filter(metadata_only=False).count(), resp.json()["meta"]["total_count"])

    def test_the_api_should_return_all_documents_with_metadata_true(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "documents"})

        url = f"{list_url}?metadata_only=True"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(Document.objects.filter(metadata_only=True).count(), resp.json()["meta"]["total_count"])

    def test_the_api_should_return_all_maps_with_metadata_false(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "maps"})

        resp = self.api_client.get(list_url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(Map.objects.filter(metadata_only=False).count(), resp.json()["meta"]["total_count"])

    def test_the_api_should_return_all_maps_with_metadata_true(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "maps"})

        url = f"{list_url}?metadata_only=True"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(Map.objects.filter(metadata_only=True).count(), resp.json()["meta"]["total_count"])

    def test_api_will_return_a_valid_json_response(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        resp = self.api_client.get(list_url)
        self.assertValidJSONResponse(resp)

    def test_will_return_empty_if_the_thesaurus_does_not_exists(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        url = f"{list_url}?thesaurus=invalid-identifier"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 0)

    def test_will_return_keywords_for_the_selected_thesaurus_if_exists(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        url = f"{list_url}?thesaurus=inspire-theme"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 36)

    def test_will_return_empty_if_the_alt_label_does_not_exists(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        url = f"{list_url}?alt_label=invalid-alt_label"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 0)

    def test_will_return_keywords_for_the_selected_alt_label_if_exists(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        url = f"{list_url}?alt_label=ac"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 1)

    def test_will_return_empty_if_the_kaywordId_does_not_exists(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        url = f"{list_url}?id=12365478954862"
        resp = self.api_client.get(url)
        print(self.deserialize(resp))
        self.assertValidJSONResponse(resp)
        self.assertEqual(resp.json()["meta"]["total_count"], 0)

    @patch("geonode.api.api.get_language")
    def test_will_return_expected_keyword_label_for_existing_lang(self, lang):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        lang.return_value = "de"
        url = f"{list_url}?thesaurus=inspire-theme"
        resp = self.api_client.get(url)
        # the german translations exists, for the other labels, the alt_label will be used
        expected_labels = [
            "",
            "ac",
            "Adressen",
            "af",
            "am",
            "au",
            "br",
            "bu",
            "cp",
            "ef",
            "el",
            "er",
            "foo_keyword",
            "ge",
            "gg",
            "gn",
            "hb",
            "hh",
            "hy",
            "lc",
            "lu",
            "mf",
            "mr",
            "nz",
            "of",
            "oi",
            "pd",
            "pf",
            "ps",
            "rs",
            "sd",
            "so",
            "sr",
            "su",
            "tn",
            "us",
        ]
        actual_labels = [x["alt_label"] for x in self.deserialize(resp)["objects"]]
        self.assertValidJSONResponse(resp)
        self.assertListEqual(expected_labels, actual_labels)

    @patch("geonode.api.api.get_language")
    def test_will_return_default_keyword_label_for_not_existing_lang(self, lang):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "thesaurus/keywords"})

        lang.return_value = "ke"
        url = f"{list_url}?thesaurus=inspire-theme"
        resp = self.api_client.get(url)
        # no translations exists, the alt_label will be used for all keywords
        expected_labels = [
            "",
            "ac",
            "ad",
            "af",
            "am",
            "au",
            "br",
            "bu",
            "cp",
            "ef",
            "el",
            "er",
            "foo_keyword",
            "ge",
            "gg",
            "gn",
            "hb",
            "hh",
            "hy",
            "lc",
            "lu",
            "mf",
            "mr",
            "nz",
            "of",
            "oi",
            "pd",
            "pf",
            "ps",
            "rs",
            "sd",
            "so",
            "sr",
            "su",
            "tn",
            "us",
        ]
        actual_labels = [x["alt_label"] for x in self.deserialize(resp)["objects"]]
        self.assertValidJSONResponse(resp)
        self.assertListEqual(expected_labels, actual_labels)

    def test_the_api_should_return_all_map_categories_with_metadata_false(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "categories"})

        url = f"{list_url}?type=map"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        actual = sum([x["count"] for x in resp.json()["objects"]])
        self.assertEqual(9, actual)

    def test_the_api_should_return_all_map_categories_with_metadata_true(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "categories"})

        x = Map.objects.get(title="map metadata true")
        x.metadata_only = False
        x.save()
        url = f"{list_url}?type=map"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        # by adding a new layer, the total should increase
        actual = sum([x["count"] for x in resp.json()["objects"]])
        self.assertEqual(10, actual)

    def test_the_api_should_return_all_document_categories_with_metadata_false(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "categories"})

        url = f"{list_url}?type=document"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        actual = sum([x["count"] for x in resp.json()["objects"]])
        self.assertEqual(0, actual)

    def test_the_api_should_return_all_document_categories_with_metadata_true(self):
        list_url = reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "categories"})

        x = Document.objects.get(title="doc metadata true")
        x.metadata_only = False
        x.save()
        url = f"{list_url}?type=document"
        resp = self.api_client.get(url)
        self.assertValidJSONResponse(resp)
        # by adding a new layer, the total should increase
        actual = sum([x["count"] for x in resp.json()["objects"]])
        self.assertEqual(0, actual)


class ThesauriApiTests(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = get_user_model().objects.create(username="user_00")
        cls.admin = get_user_model().objects.get(username="admin")

        cls._create_thesauri()
        cls._create_resources()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    def setUp(self):
        super().setUp()

        self.api_client = TestApiClient()

        self.assertEqual(self.admin.username, "admin")
        self.assertEqual(self.admin.is_superuser, True)

    @classmethod
    def _create_thesauri(cls):
        cls.thesauri = {}
        cls.thesauri_k = {}

        for tn in range(2):
            t = Thesaurus.objects.create(identifier=f"t_{tn}", title=f"Thesaurus {tn}")
            cls.thesauri[tn] = t
            for tl in (
                "en",
                "it",
            ):
                ThesaurusLabel.objects.create(thesaurus=t, lang=tl, label=f"TLabel {tn} {tl}")

            for tkn in range(10):
                tk = ThesaurusKeyword.objects.create(thesaurus=t, alt_label=f"alt_tkn{tkn}_t{tn}")
                cls.thesauri_k[f"{tn}_{tkn}"] = tk
                for tkl in (
                    "en",
                    "it",
                ):
                    ThesaurusKeywordLabel.objects.create(keyword=tk, lang=tkl, label=f"T{tn}_K{tkn}_{tkl}")

    @classmethod
    def _create_resources(self):
        public_perm_spec = {"users": {"AnonymousUser": ["view_resourcebase"]}, "groups": []}

        for x in range(20):
            d: ResourceBase = ResourceBase.objects.create(
                title=f"dataset_{x:02}",
                uuid=str(uuid4()),
                owner=self.user,
                abstract=f"Abstract for dataset {x:02}",
                subtype="vector",
                is_approved=True,
                is_published=True,
            )

            # These are the assigned keywords to the Resources

            # RB00 ->            T1K0
            # RB01 ->  T0K0      T1K0
            # RB02 ->            T1K0
            # RB03 ->  T0K0      T1K0
            # RB04 ->            T1K0
            # RB05 ->  T0K0      T1K0
            # RB06 ->            T1K0
            # RB07 ->  T0K0      T1K0
            # RB08 ->            T1K0 T1K1
            # RB09 ->  T0K0      T1K0 T1K1
            # RB10 ->                 T1K1
            # RB11 ->  T0K0 T0K1      T1K1
            # RB12 ->                 T1K1
            # RB13 ->  T0K0 T0K1
            # RB14 ->
            # RB15 ->  T0K0 T0K1
            # RB16 ->
            # RB17 ->  T0K0 T0K1
            # RB18 ->
            # RB19 ->  T0K0 T0K1

            if x % 2 == 1:
                print(f"ADDING KEYWORDS {self.thesauri_k['0_0']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["0_0"])
                d.save()
            if x % 2 == 1 and x > 10:
                print(f"ADDING KEYWORDS {self.thesauri_k['0_1']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["0_1"])
                d.save()
            if x < 10:
                print(f"ADDING KEYWORDS {self.thesauri_k['1_0']} to RB {d}")
                d.tkeywords.add(self.thesauri_k["1_0"])
                d.save()
            if 7 < x < 13:
                d.tkeywords.add(self.thesauri_k["1_1"])
                d.save()

            d.set_permissions(public_perm_spec)

    def test_resources_filtered(self):
        # list_url = reverse("base-resources", kwargs={"api_name": "api", "resource_name": "base"})
        list_url = reverse("base-resources-list")

        for tks, exp, exp_and in (
            # single filter
            (("0_0",), 10, 10),
            (("0_1",), 5, 5),
            (("1_0",), 10, 10),
            (("1_1",), 5, 5),
            # same thesaurus: OR
            (("0_0", "0_1"), 10, 5),
            (("1_0", "1_1"), 13, 2),
            # different thesauri: AND
            (("0_0", "1_0"), 5, 5),
            (("0_1", "1_0"), 0, 0),
            (("0_1", "1_0", "1_1"), 1, 0),
            (("0_0", "0_1", "1_0", "1_1"), 6, 0),
        ):
            logger.debug(f"Testing filters for {tks}")
            filter = [("filter{tkeywords}", self.thesauri_k[tk].id) for tk in tks]
            url = f"{list_url}?{urlencode(filter)}"
            resp = self.api_client.get(url).json()
            self.assertEqual(exp, resp["total"], f"Unexpected number of resources for default filter {tks}")

            filter = [("filter{tkeywords}", self.thesauri_k[tk].id) for tk in tks]
            url = f"{list_url}?{urlencode(filter + [('force_and', True)])}"
            resp = self.api_client.get(url).json()
            self.assertEqual(exp_and, resp["total"], f"Unexpected number of resources for FORCE_AND filter {tks}")
