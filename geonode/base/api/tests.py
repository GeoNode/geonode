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

import ast
import os
import re
import sys
import json
import logging
from builtins import Exception
from typing import Iterable

from django.test import RequestFactory, override_settings
import gisdata
from PIL import Image
from io import BytesIO
from time import sleep
from uuid import uuid4
from unittest.mock import patch
from urllib.parse import urljoin
from datetime import date, timedelta

from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from owslib.etree import etree
from avatar.templatetags.avatar_tags import avatar_url

from rest_framework.test import APITestCase
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from geonode.catalogue import get_catalogue
from geonode.catalogue.models import catalogue_post_save
from geonode.catalogue.views import csw_global_dispatch

from geonode.resource.manager import resource_manager
from guardian.shortcuts import get_anonymous_user

from geonode.assets.utils import create_asset_and_link
from geonode.maps.models import Map, MapLayer
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.assets.utils import get_default_asset
from geonode.assets.handlers import asset_handler_registry

from geonode.base import enumerations
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.groups.models import GroupMember, GroupProfile
from geonode.thumbs.exceptions import ThumbnailError
from geonode.layers.utils import get_files
from geonode.base.models import (
    HierarchicalKeyword,
    Region,
    ResourceBase,
    TopicCategory,
    ThesaurusKeyword,
    ExtraMetadata,
    RestrictionCodeType,
    License,
    Group,
    LinkedResource,
)

from geonode.layers.models import Dataset
from geonode.favorite.models import Favorite
from geonode.documents.models import Document
from geonode.geoapps.models import GeoApp
from geonode.utils import build_absolute_uri
from geonode.resource.api.tasks import ExecutionRequest
from geonode.base.populate_test_data import (
    create_models,
    create_single_dataset,
    create_single_doc,
    create_single_map,
    create_single_geoapp,
)
from geonode.resource.api.tasks import resouce_service_dispatcher
from guardian.shortcuts import assign_perm

logger = logging.getLogger(__name__)

test_image = Image.new("RGBA", size=(50, 50), color=(155, 0, 0))


class BaseApiTests(APITestCase):
    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json", "test_thesaurus.json"]

    def setUp(self):
        self.maxDiff = None
        create_models(b"document")
        create_models(b"map")
        create_models(b"dataset")

    def test_groups_list(self):
        """
        Ensure we can access the gropus list.
        """
        pub_1 = GroupProfile.objects.create(slug="pub_1", title="pub_1", access="public")
        priv_1 = GroupProfile.objects.create(slug="priv_1", title="priv_1", access="private")
        priv_2 = GroupProfile.objects.create(slug="priv_2", title="priv_2", access="private")
        pub_invite_1 = GroupProfile.objects.create(slug="pub_invite_1", title="pub_invite_1", access="public-invite")
        pub_invite_2 = GroupProfile.objects.create(slug="pub_invite_2", title="pub_invite_2", access="public-invite")
        try:
            # Anonymous can access only public groups
            url = reverse("group-profiles-list")
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data["total"], 4)
            self.assertEqual(len(response.data["group_profiles"]), 4)
            self.assertTrue(all([_g["access"] != "private" for _g in response.data["group_profiles"]]))

            # Admin can access all groups
            self.assertTrue(self.client.login(username="admin", password="admin"))
            url = reverse("group-profiles-list")
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data["total"], 6)
            self.assertEqual(len(response.data["group_profiles"]), 6)

            # Bobby can access public groups and the ones he is member of
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            priv_1.join(get_user_model().objects.get(username="bobby"))
            url = reverse("group-profiles-list")
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
            self.assertEqual(len(response.data), 5)
            self.assertEqual(response.data["total"], 5)
            self.assertEqual(len(response.data["group_profiles"]), 5)
            self.assertTrue(any([_g["slug"] == "priv_1" for _g in response.data["group_profiles"]]))

            url = reverse("group-profiles-detail", kwargs={"pk": priv_1.pk})
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            logger.debug(response.data)
        finally:
            pub_1.delete()
            priv_1.delete()
            priv_2.delete()
            pub_invite_1.delete()
            pub_invite_2.delete()

    def test_create_group(self):
        """
        Ensure only Admins can create groups.
        """
        data = {
            "title": "group title",
            "group": 1,
            "slug": "group_title",
            "description": "test",
            "access": "private",
            "categories": [],
        }
        try:
            # Anonymous
            url = reverse("group-profiles-list")
            response = self.client.post(url, data=data, format="json")
            self.assertEqual(response.status_code, 403)

            # Registered member
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.post(url, data=data, format="json")
            self.assertEqual(response.status_code, 403)

            # Group manager
            group = GroupProfile.objects.create(slug="test_group_manager", title="test_group_manager")
            group.join(get_user_model().objects.get(username="norman"), role="manager")
            self.assertTrue(self.client.login(username="norman", password="norman"))
            response = self.client.post(url, data=data, format="json")
            self.assertEqual(response.status_code, 403)

            # Admin
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.post(url, data=data, format="json")
            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json()["group_profile"]["title"], "group title")
        finally:
            GroupProfile.objects.get(slug="group_title").delete()
            group.delete()

    def test_edit_group(self):
        """
        Ensure only admins and group managers can edit a group.
        """
        group = GroupProfile.objects.create(slug="pub_1", title="pub_1", access="public")
        data = {"title": "new_title"}
        try:
            # Anonymous
            url = f"{reverse('group-profiles-list')}/{group.id}/"
            response = self.client.patch(url, data=data, format="json")
            self.assertEqual(response.status_code, 403)

            # Registered member
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.patch(url, data=data, format="json")
            self.assertEqual(response.status_code, 403)

            # Group manager
            group.join(get_user_model().objects.get(username="bobby"), role="manager")
            response = self.client.patch(url, data=data, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(GroupProfile.objects.get(id=group.id).title, data["title"])

            # Admin
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.patch(url, data={"title": "admin_title"}, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(GroupProfile.objects.get(id=group.id).title, "admin_title")
        finally:
            group.delete()

    def test_delete_group(self):
        """
        Ensure only admins can delete a group.
        """
        group = GroupProfile.objects.create(slug="pub_1", title="pub_1", access="public")
        try:
            # Anonymous
            url = f"{reverse('group-profiles-list')}/{group.id}/"
            response = self.client.delete(url, format="json")
            self.assertEqual(response.status_code, 403)

            # Registered member
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.delete(url, format="json")
            self.assertEqual(response.status_code, 403)

            # Group manager
            group.join(get_user_model().objects.get(username="bobby"), role="manager")
            response = self.client.delete(f"{reverse('group-profiles-list')}/{group.id}/", format="json")
            self.assertEqual(response.status_code, 403)

            # Admin can delete a group
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.delete(f"{reverse('group-profiles-list')}/{group.id}/", format="json")
            self.assertEqual(response.status_code, 204)
        finally:
            group.delete()

    def test_group_resources_shows_related_permissions(self):
        """
        Calling the resources endpoint of the groups should return also the
        group permission on that specific resource
        """
        group = GroupProfile.objects.create(slug="group1", title="group1", access="public")
        bobby = get_user_model().objects.filter(username="bobby").get()
        GroupMember.objects.get_or_create(group=group, user=bobby, role="member")
        dataset = Dataset.objects.first()
        dataset.set_permissions({"groups": {group: ["base.view_resourcebase"]}})
        try:
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            url = f"{reverse('group-profiles-list')}/{group.id}/resources"
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            perms = response.json().get("resources", [])[0].get("perms")
            self.assertListEqual(["view_resourcebase"], perms)
        finally:
            group.delete()

    def test_users_list(self):
        """
        Ensure we can access the users list.
        """
        url = reverse("users-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)
        # Authorized
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        logger.debug(response.data)
        self.assertEqual(response.data["total"], 9)
        self.assertEqual(len(response.data["users"]), 9)
        # response has link to the response
        self.assertTrue("link" in response.data["users"][0].keys())

        url = reverse("users-detail", kwargs={"pk": 1})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        logger.debug(response.data)
        self.assertEqual(response.data["user"]["username"], "admin")
        self.assertIsNotNone(response.data["user"]["avatar"])

        # anonymous users are not in contributors group
        self.assertNotIn("add_resource", get_user_model().objects.get(id=-1).perms)

        try:
            # Bobby
            group_user = get_user_model().objects.create(username="group_user")
            bobby = get_user_model().objects.filter(username="bobby").get()
            groupx = GroupProfile.objects.create(slug="groupx", title="groupx", access="private")
            groupx.join(bobby)
            groupx.join(group_user)
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            url = reverse("users-detail", kwargs={"pk": group_user.id})
            # Bobby can access other users details from same group
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)

            # Bobby can see himself in the list
            url = reverse("users-list")
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertIn('"username": "bobby"', json.dumps(response.data["users"]))

            # Bobby can access its own details
            url = reverse("users-detail", kwargs={"pk": bobby.id})
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["user"]["username"], "bobby")
            self.assertIsNotNone(response.data["user"]["avatar"])
            # default contributor group_perm is returned in perms
            self.assertIn("add_resource", response.data["user"]["perms"])

            # Bobby can't access other users perms list
            url = reverse("users-detail", kwargs={"pk": group_user.id})
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["user"]["username"], "group_user")
            self.assertIsNotNone(response.data["user"]["avatar"])
            # default contributor group_perm is returned in perms
            self.assertNotIn("perms", response.data["user"])
        finally:
            group_user.delete()
            groupx.delete()

    def test_user_resources_shows_related_permissions(self):
        """
        Calling the resources endpoint of the user should return also the
        user permission on that specific resource
        """
        bobby = get_user_model().objects.filter(username="bobby").get()
        dataset = Dataset.objects.first()
        dataset.set_permissions({"users": {bobby: ["base.view_resourcebase", "base.change_resourcebase"]}})
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        url = f"{reverse('users-list')}/{bobby.id}/resources"
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        perms = response.json().get("resources", [])[0].get("perms")
        self.assertSetEqual({"view_resourcebase", "change_resourcebase"}, set(perms))

    def test_get_self_user_details_outside_registered_member(self):
        try:
            user = get_user_model().objects.create_user(
                username="non_registered_member", email="non_registered_member@geonode.org", password="password"
            )
            # remove user from registered members group
            reg_mem_group = Group.objects.get(name="registered-members")
            reg_mem_group.user_set.remove(user)

            url = reverse("users-detail", kwargs={"pk": user.pk})

            self.assertTrue(self.client.login(username="non_registered_member", password="password"))
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
        finally:
            user.delete()

    def test_get_self_user_details_with_no_group(self):
        try:
            user = get_user_model().objects.create_user(
                username="no_group_member", email="no_group_member@geonode.org", password="password"
            )
            # remove user from all groups
            user.groups.clear()

            url = reverse("users-detail", kwargs={"pk": user.pk})

            self.assertTrue(self.client.login(username="no_group_member", password="password"))
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
        finally:
            user.delete()

    def test_register_users(self):
        """
        Ensure users are created with default groups.
        """
        url = reverse("users-list")
        user_data = {"username": "new_user", "password": "@!2XJSL_S&V^0nt", "email": "user@exampl2e.com"}
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(url, data=user_data, format="json")
        self.assertEqual(response.status_code, 201)
        # default contributor group_perm is returned in perms
        self.assertIn("add_resource", response.data["user"]["perms"])
        # Anonymous
        self.assertIsNone(self.client.logout())
        response = self.client.post(url, data={"username": "new_user_1"}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_acess_profile_edit(self):
        # Registered member
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        user = get_user_model().objects.get(username="bobby")

        url = f'{reverse("profile_edit")}{user.username}'
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)

    def test_update_user_profile(self):
        """
        Ensure users cannot update others.
        """
        try:
            user = get_user_model().objects.create_user(
                username="user_test_delete", email="user_test_delete@geonode.org", password="user"
            )
            url = reverse("users-detail", kwargs={"pk": user.pk})
            data = {"first_name": "user", "password": "@!2XJSL_S&V^0nt", "email": "user@exampl2e.com"}
            # Anonymous
            response = self.client.patch(url, data=data, format="json")
            self.assertEqual(response.status_code, 403)
            # Another registered user
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.patch(url, data=data, format="json")
            self.assertEqual(response.status_code, 403)
            # User self profile
            self.assertTrue(self.client.login(username="user_test_delete", password="user"))
            response = self.client.patch(url, data=data, format="json")
            self.assertEqual(response.status_code, 200)
            # Group manager
            group = GroupProfile.objects.create(slug="test_group_manager", title="test_group_manager")
            group.join(user)
            group.join(get_user_model().objects.get(username="norman"), role="manager")
            self.assertTrue(self.client.login(username="norman", password="norman"))
            response = self.client.post(url, data=data, format="json")
            # malformed url on post
            self.assertEqual(response.status_code, 405)
            # Admin can edit user
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.patch(url, data={"first_name": "user_admin"}, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(get_user_model().objects.get(username="user_test_delete").first_name, "user_admin")
        finally:
            user.delete()
            group.delete()

    def test_delete_user_profile(self):
        """
        Ensure only admins can delete profiles.
        """
        try:
            user = get_user_model().objects.create_user(
                username="user_test_delete", email="user_test_delete@geonode.org", password="user"
            )
            url = reverse("users-detail", kwargs={"pk": user.pk})
            # Anonymous can't read
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 403)
            # Anonymous can't delete user
            response = self.client.delete(url, format="json")
            self.assertEqual(response.status_code, 403)
            # Bob can't delete user
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.delete(url, format="json")
            self.assertEqual(response.status_code, 403)
            # User can delete self profile
            self.assertTrue(self.client.login(username="user_test_delete", password="user"))
            response = self.client.delete(url, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(get_user_model().objects.filter(username="user_test_delete").first(), None)
            # recreate user that was deleted
            user = get_user_model().objects.create_user(
                username="user_test_delete", email="user_test_delete@geonode.org", password="user"
            )
            url = reverse("users-detail", kwargs={"pk": user.pk})
            # Admin can delete user
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.delete(url, format="json")
            self.assertEqual(response.status_code, 200)
        finally:
            user.delete()

    def test_base_resources(self):
        """
        Ensure we can access the Resource Base list.
        """
        url = reverse("base-resources-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 28)

        url = f"{reverse('base-resources-list')}?filter{{metadata_only}}=false"
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        response.data["resources"][0].get("executions")
        # Pagination
        self.assertEqual(len(response.data["resources"]), 10)
        logger.debug(response.data)

        # Remove public permissions to Layers
        from geonode.layers.utils import set_datasets_permissions

        set_datasets_permissions(
            "read",  # permissions_name
            None,  # resources_names == None (all layers)
            [get_anonymous_user()],  # users_usernames
            None,  # groups_names
            True,  # delete_flag
        )
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 10)

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        # response has link to the response
        self.assertTrue("link" in response.data["resources"][0].keys())
        # Pagination
        self.assertEqual(len(response.data["resources"]), 10)
        logger.debug(response.data)

        # Bobby
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 10)
        logger.debug(response.data)

        # Norman
        self.assertTrue(self.client.login(username="norman", password="norman"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 10)
        logger.debug(response.data)

        # Pagination
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get(f"{url}&page_size=17", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 17)

        # Check user permissions
        resource = ResourceBase.objects.filter(owner__username="bobby").first()
        self.assertEqual(resource.owner.username, "bobby")
        # Admin
        url_with_id = f"{reverse('base-resources-list')}/{resource.id}?filter{{metadata_only}}=false"

        response = self.client.get(f"{url_with_id}", format="json")
        self.assertEqual(response.data["resource"]["state"], enumerations.STATE_PROCESSED)
        self.assertEqual(response.data["resource"]["sourcetype"], enumerations.SOURCE_TYPE_LOCAL)
        self.assertTrue("change_resourcebase" in list(response.data["resource"]["perms"]))
        # Annonymous
        self.assertIsNone(self.client.logout())
        response = self.client.get(f"{url_with_id}", format="json")
        self.assertFalse("change_resourcebase" in list(response.data["resource"]["perms"]))
        # user owner
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(f"{url_with_id}", format="json")
        self.assertTrue("change_resourcebase" in list(response.data["resource"]["perms"]))
        # user not owner and not assigned
        self.assertTrue(self.client.login(username="norman", password="norman"))
        response = self.client.get(f"{url_with_id}", format="json")
        self.assertFalse("change_resourcebase" in list(response.data["resource"]["perms"]))
        # Check executions are returned when deffered
        # all resources
        response = self.client.get(f"{url}&include[]=executions", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["resources"][0].get("executions"))
        # specific resource
        exec_req = ExecutionRequest.objects.create(
            user=resource.owner,
            func_name="test",
            geonode_resource=resource,
            input_params={
                "uuid": resource.uuid,
                "owner": resource.owner.username,
                "resource_type": resource.resource_type,
                "defaults": f'{{"owner":"{resource.owner.username}"}}',
            },
        )
        expected_executions_results = [
            {
                "exec_id": exec_req.exec_id,
                "user": exec_req.user.username,
                "status": exec_req.status,
                "func_name": exec_req.func_name,
                "created": exec_req.created,
                "finished": exec_req.finished,
                "last_updated": exec_req.last_updated,
                "input_params": exec_req.input_params,
                "output_params": exec_req.output_params,
                "status_url": urljoin(
                    settings.SITEURL, reverse("rs-execution-status", kwargs={"execution_id": exec_req.exec_id})
                ),
            }
        ]
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(f"{url_with_id}&include[]=executions", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data["resource"].get("executions"))
        self.assertEqual(response.data["resource"].get("executions"), expected_executions_results)

        # test 'tkeywords'
        try:
            for _tkw in ThesaurusKeyword.objects.filter(pk__gte=34):
                resource.tkeywords.add(_tkw)
            self.assertEqual(6, resource.tkeywords.count())
            # Admin
            self.assertTrue(self.client.login(username="admin", password="admin"))
            response = self.client.get(f"{url_with_id}", format="json")
            self.assertIsNotNone(response.data["resource"]["tkeywords"])
            self.assertEqual(6, len(response.data["resource"]["tkeywords"]))
            self.assertListEqual(
                [
                    {
                        "name": "",
                        "slug": "http-inspire-ec-europa-eu-theme-37",
                        "uri": "http://inspire.ec.europa.eu/theme#37",
                        "thesaurus": {
                            "name": "GEMET - INSPIRE themes, version 1.0",
                            "slug": "inspire-theme",
                            "uri": "http://inspire.ec.europa.eu/theme",
                        },
                        "i18n": {},
                    },
                    {
                        "name": "",
                        "slug": "http-localhost-8000-thesaurus-no-about-thesauro-38",
                        "uri": "http://localhost:8000//thesaurus/no-about-thesauro#38",
                        "thesaurus": {"name": "Thesauro without the about", "slug": "no-about-thesauro", "uri": ""},
                        "i18n": {},
                    },
                    {
                        "name": "bar_keyword",
                        "slug": "http-localhost-8000-thesaurus-no-about-thesauro-bar-keyword",
                        "uri": "http://localhost:8000//thesaurus/no-about-thesauro#bar_keyword",
                        "thesaurus": {"name": "Thesauro without the about", "slug": "no-about-thesauro", "uri": ""},
                        "i18n": {},
                    },
                    {
                        "name": "foo_keyword",
                        "slug": "http-inspire-ec-europa-eu-theme-foo-keyword",
                        "uri": "http://inspire.ec.europa.eu/theme#foo_keyword",
                        "thesaurus": {
                            "name": "GEMET - INSPIRE themes, version 1.0",
                            "slug": "inspire-theme",
                            "uri": "http://inspire.ec.europa.eu/theme",
                        },
                        "i18n": {},
                    },
                    {
                        "name": "mf",
                        "slug": "http-inspire-ec-europa-eu-theme-mf",
                        "uri": "http://inspire.ec.europa.eu/theme/mf",
                        "thesaurus": {
                            "name": "GEMET - INSPIRE themes, version 1.0",
                            "slug": "inspire-theme",
                            "uri": "http://inspire.ec.europa.eu/theme",
                        },
                        "i18n": {"en": "Meteorological geographical features"},
                    },
                    {
                        "name": "us",
                        "slug": "http-inspire-ec-europa-eu-theme-us",
                        "uri": "http://inspire.ec.europa.eu/theme/us",
                        "thesaurus": {
                            "name": "GEMET - INSPIRE themes, version 1.0",
                            "slug": "inspire-theme",
                            "uri": "http://inspire.ec.europa.eu/theme",
                        },
                        "i18n": {"en": "Utility and governmental services"},
                    },
                ],
                response.data["resource"]["tkeywords"],
            )
        finally:
            resource.tkeywords.set(ThesaurusKeyword.objects.none())
            self.assertEqual(0, resource.tkeywords.count())

    def test_write_resources(self):
        """
        Ensure we can perform write operation against the Resource Bases.
        """
        url = reverse("base-resources-list")
        # Check user permissions
        for resource_type in ["dataset", "document", "map"]:
            resource = ResourceBase.objects.filter(owner__username="bobby", resource_type=resource_type).first()
            self.assertEqual(resource.owner.username, "bobby")
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.get(f"{url}/{resource.id}/", format="json")
            self.assertTrue("change_resourcebase" in list(response.data["resource"]["perms"]))
            self.assertEqual(True, response.data["resource"]["is_published"], response.data["resource"]["is_published"])
            data = {
                "title": "Foo Title",
                "abstract": "Foo Abstract",
                "attribution": "Foo Attribution",
                "doi": "321-12345-987654321",
                "is_published": False,
            }
            response = self.client.patch(f"{url}/{resource.id}/", data=data, format="json")
            self.assertEqual(response.status_code, 200, response.status_code)
            response = self.client.get(f"{url}/{resource.id}/", format="json")
            self.assertEqual("Foo Title", response.data["resource"]["title"], response.data["resource"]["title"])
            self.assertEqual(
                "Foo Abstract", response.data["resource"]["abstract"], response.data["resource"]["abstract"]
            )
            self.assertEqual(
                "Foo Attribution", response.data["resource"]["attribution"], response.data["resource"]["attribution"]
            )
            self.assertEqual("321-12345-987654321", response.data["resource"]["doi"], response.data["resource"]["doi"])
            self.assertEqual(
                False, response.data["resource"]["is_published"], response.data["resource"]["is_published"]
            )

    def test_resource_serializer_validation(self):
        """
        Testing serializing and deserializing of a Dataset base on django-rest description:
        https://www.django-rest-framework.org/api-guide/serializers/#deserializing-objects
        """
        owner, _ = get_user_model().objects.get_or_create(username="delet-owner")
        title = "TEST DS TITLE"
        HierarchicalKeyword.add_root(name="a")
        keyword = HierarchicalKeyword.objects.get(slug="a")
        keyword.add_child(name="a1")

        Dataset(
            title=title,
            abstract="abstract",
            name="test dataset",
            alternate="Test Remove User",
            attribution="Test Attribution",
            uuid=str(uuid4()),
            doi="test DOI",
            edition=1,
            maintenance_frequency=enumerations.UPDATE_FREQUENCIES[0],
            constraints_other="Test Constrains other",
            temporal_extent_start=date.today() - timedelta(days=1),
            temporal_extent_end=date.today(),
            data_quality_statement="Test data quality statement",
            purpose="Test Purpose",
            owner=owner,
            subtype="raster",
            category=TopicCategory.objects.get(identifier="elevation"),
            resource_type="dataset",
            license=License.objects.all().first(),
            restriction_code_type=RestrictionCodeType.objects.all().first(),
            group=Group.objects.all().first(),
        ).save()

        ds = ResourceBase.objects.get(title=title)
        ds.keywords.add(HierarchicalKeyword.objects.get(slug="a1"))

        factory = RequestFactory()
        rq = factory.get("test")
        rq.user = owner

        serialized = ResourceBaseSerializer(ds, context={"request": rq})
        json = JSONRenderer().render(serialized.data)
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        self.assertIsInstance(data, dict)
        se = ResourceBaseSerializer(data=data, context={"request": rq})
        self.assertTrue(se.is_valid())

    def test_resource_base_serializer_with_settingsfield(self):
        doc = create_single_doc("my_custom_doc")
        factory = RequestFactory()
        rq = factory.get("test")
        rq.user = doc.owner
        serialized = ResourceBaseSerializer(doc, context={"request": rq})
        json = JSONRenderer().render(serialized.data)
        stream = BytesIO(json)
        data = JSONParser().parse(stream)
        self.assertTrue(data.get("is_approved"))
        self.assertTrue(data.get("is_published"))
        self.assertFalse(data.get("featured"))

    def test_resource_settings_field(self):
        """
        Admin is able to change the is_published value
        """
        doc = create_single_doc("my_custom_doc")
        factory = RequestFactory()
        rq = factory.get("test")
        rq.user = doc.owner
        serializer = ResourceBaseSerializer(doc, context={"request": rq})
        field = serializer.fields["is_published"]
        self.assertIsNotNone(field)
        self.assertTrue(field.to_internal_value(True))

    def test_resource_settings_field_non_admin(self):
        """
        Non-Admin is not able to change the is_published value
        if he is not the owner of the resource
        """
        doc = create_single_doc("my_custom_doc")
        factory = RequestFactory()
        rq = factory.get("test")
        rq.user = get_user_model().objects.get(username="bobby")
        serializer = ResourceBaseSerializer(doc, context={"request": rq})
        field = serializer.fields["is_published"]
        self.assertIsNotNone(field)
        # the original value was true, so it should not return false
        self.assertTrue(field.to_internal_value(False))

    def test_delete_user_with_resource(self):
        owner, created = get_user_model().objects.get_or_create(username="delet-owner")
        Dataset(
            title="Test Remove User",
            abstract="abstract",
            name="Test Remove User",
            alternate="Test Remove User",
            uuid=str(uuid4()),
            owner=owner,
            subtype="raster",
            category=TopicCategory.objects.get(identifier="elevation"),
        ).save()
        # Delete user and check if default user is updated
        owner.delete()
        self.assertEqual(
            ResourceBase.objects.get(title="Test Remove User").owner, get_user_model().objects.get(username="admin")
        )

    def test_search_resources(self):
        """
        Ensure we can search across the Resource Base list.
        """
        url = reverse("base-resources-list")
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get(f"{url}?search=ca&search_fields=title&search_fields=abstract", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 1)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 1)

    def test_filter_resources(self):
        """
        Ensure we can filter across the Resource Base list.
        """
        url = reverse("base-resources-list")
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        # Filter by owner == bobby
        response = self.client.get(f"{url}?filter{{owner.username}}=bobby&filter{{metadata_only}}=false", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 3)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 3)

        # Filter by resource_type == document
        response = self.client.get(
            f"{url}?filter{{resource_type}}=document&filter{{metadata_only}}=false", format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 9)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 9)

        # Filter by resource_type == layer and title like 'common morx'
        response = self.client.get(
            f"{url}?filter{{resource_type}}=dataset&filter{{title.icontains}}=common morx&filter{{metadata_only}}=false",
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 1)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 1)

        # Filter by Keywords
        response = self.client.get(f"{url}?filter{{keywords.name}}=here&filter{{metadata_only}}=false", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 1)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 1)

        # Filter by Metadata Regions
        response = self.client.get(
            f"{url}?filter{{regions.name.icontains}}=Italy&filter{{metadata_only}}=false", format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 0)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 0)

        # Filter by Metadata Categories
        response = self.client.get(
            f"{url}?filter{{category.identifier}}=elevation&filter{{metadata_only}}=false", format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 6)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 6)

        # Extent Filter
        response = self.client.get(
            f"{url}?page_size=26&extent=-180,-90,180,90&filter{{metadata_only}}=false", format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 26)

        response = self.client.get(
            f"{url}?page_size=26&extent=0,0,100,100&filter{{metadata_only}}=false", format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 26)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 26)

        response = self.client.get(
            f"{url}?page_size=26&extent=-10,-10,-1,-1&filter{{metadata_only}}=false", format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 12)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 12)

        # Extent Filter: Crossing Dateline
        extent = "-180.0000,56.9689,-162.5977,70.7435,155.9180,56.9689,180.0000,70.7435"
        response = self.client.get(f"{url}?page_size=26&extent={extent}&filter{{metadata_only}}=false", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 12)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 12)

    def test_sort_resources(self):
        """
        Ensure we can sort the Resource Base list.
        """
        url = reverse("base-resources-list")
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get(f"{url}?sort[]=title", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 28)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 10)

        resource_titles = []
        for _r in response.data["resources"]:
            resource_titles.append(_r["title"])
        sorted_resource_titles = sorted(resource_titles.copy())
        self.assertEqual(resource_titles, sorted_resource_titles)

        response = self.client.get(f"{url}?sort[]=-title", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 28)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 10)

        resource_titles = []
        for _r in response.data["resources"]:
            resource_titles.append(_r["title"])

        reversed_resource_titles = sorted(resource_titles.copy())
        self.assertNotEqual(resource_titles, reversed_resource_titles)

    def test_perms_resources(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = reverse("base-resources-list")
        bobby = get_user_model().objects.get(username="bobby")
        norman = get_user_model().objects.get(username="norman")
        anonymous_group = Group.objects.get(name="anonymous")
        contributors_group = Group.objects.get(name="registered-members")

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        resource = ResourceBase.objects.filter(owner__username="bobby").first()
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", "permissions")
        get_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", "permissions")

        url = reverse("base-resources-detail", kwargs={"pk": resource.pk})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data["resource"]["pk"]), int(resource.pk))

        response = self.client.get(get_perms_url, format="json")
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                "users": [
                    {
                        "id": bobby.id,
                        "username": bobby.username,
                        "first_name": bobby.first_name,
                        "last_name": bobby.last_name,
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "owner",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "first_name": "admin",
                        "id": 1,
                        "last_name": "",
                        "permissions": "manage",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": anonymous_group.id, "title": "anonymous", "name": "anonymous", "permissions": "download"},
                    {
                        "id": contributors_group.id,
                        "title": "Registered Members",
                        "name": contributors_group.name,
                        "permissions": "none",
                    },
                ],
            },
            resource_perm_spec,
        )

        # Add perms to Norman
        resource_perm_spec_patch = {
            "uuid": resource.uuid,
            "users": [
                {
                    "id": norman.id,
                    "username": norman.username,
                    "first_name": norman.first_name,
                    "last_name": norman.last_name,
                    "avatar": "",
                    "permissions": "edit",
                    "is_staff": False,
                    "is_superuser": False,
                }
            ],
        }
        response = self.client.patch(set_perms_url, data=resource_perm_spec_patch, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get("status"))
        self.assertIsNotNone(response.data.get("status_url"))
        status = response.data.get("status")
        resp_js = json.loads(response.content.decode("utf-8"))
        status_url = resp_js.get("status_url", None)
        execution_id = resp_js.get("execution_id", "")
        self.assertIsNotNone(status_url)
        self.assertIsNotNone(execution_id)
        for _cnt in range(0, 10):
            response = self.client.get(f"{status_url}")
            self.assertEqual(response.status_code, 200)
            resp_js = json.loads(response.content.decode("utf-8"))
            logger.error(f"[{_cnt + 1}] ... {resp_js}")
            if resp_js.get("status", "") == "finished":
                status = resp_js.get("status", "")
                break
            else:
                resouce_service_dispatcher.apply((execution_id,))
                sleep(3.0)
        self.assertTrue(status, ExecutionRequest.STATUS_FINISHED)

        response = self.client.get(get_perms_url, format="json")
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                "users": [
                    {
                        "id": bobby.id,
                        "username": bobby.username,
                        "first_name": bobby.first_name,
                        "last_name": bobby.last_name,
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "owner",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "id": norman.id,
                        "username": norman.username,
                        "first_name": norman.first_name,
                        "last_name": norman.last_name,
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "edit",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "first_name": "admin",
                        "id": 1,
                        "last_name": "",
                        "permissions": "manage",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": anonymous_group.id, "title": "anonymous", "name": "anonymous", "permissions": "download"},
                    {
                        "id": contributors_group.id,
                        "title": "Registered Members",
                        "name": contributors_group.name,
                        "permissions": "none",
                    },
                ],
            },
            resource_perm_spec,
        )

        # Remove perms to Norman
        resource_perm_spec = {
            "uuid": resource.uuid,
            "users": [
                {
                    "id": bobby.id,
                    "username": bobby.username,
                    "first_name": bobby.first_name,
                    "last_name": bobby.last_name,
                    "avatar": build_absolute_uri(avatar_url(bobby)),
                    "permissions": "owner",
                    "is_staff": False,
                    "is_superuser": False,
                },
                {
                    "avatar": build_absolute_uri(avatar_url(bobby)),
                    "first_name": "admin",
                    "id": 1,
                    "last_name": "",
                    "permissions": "manage",
                    "username": "admin",
                    "is_staff": True,
                    "is_superuser": True,
                },
            ],
            "organizations": [],
            "groups": [
                {"id": anonymous_group.id, "title": "anonymous", "name": "anonymous", "permissions": "view"},
                {
                    "id": contributors_group.id,
                    "title": "Registered Members",
                    "name": contributors_group.name,
                    "permissions": "none",
                },
            ],
        }

        response = self.client.put(set_perms_url, data=resource_perm_spec, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get("status"))
        self.assertIsNotNone(response.data.get("status_url"))
        status = response.data.get("status")
        resp_js = json.loads(response.content.decode("utf-8"))
        status_url = resp_js.get("status_url", None)
        execution_id = resp_js.get("execution_id", "")
        self.assertIsNotNone(status_url)
        self.assertIsNotNone(execution_id)
        for _cnt in range(0, 10):
            response = self.client.get(f"{status_url}")
            self.assertEqual(response.status_code, 200)
            resp_js = json.loads(response.content.decode("utf-8"))
            logger.error(f"[{_cnt + 1}] ... {resp_js}")
            if resp_js.get("status", "") == "finished":
                status = resp_js.get("status", "")
                break
            else:
                resouce_service_dispatcher.apply((execution_id,))
                sleep(3.0)
        self.assertTrue(status, ExecutionRequest.STATUS_FINISHED)

        response = self.client.get(get_perms_url, format="json")
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                "users": [
                    {
                        "id": bobby.id,
                        "username": bobby.username,
                        "first_name": bobby.first_name,
                        "last_name": bobby.last_name,
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "owner",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "first_name": "admin",
                        "id": 1,
                        "last_name": "",
                        "permissions": "manage",
                        "username": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": anonymous_group.id, "title": "anonymous", "name": "anonymous", "permissions": "view"},
                    {
                        "id": contributors_group.id,
                        "title": "Registered Members",
                        "name": contributors_group.name,
                        "permissions": "none",
                    },
                ],
            },
            resource_perm_spec,
        )

        # Ensure get_perms and set_perms are done by users with correct permissions.
        # logout admin user
        self.assertIsNone(self.client.logout())
        # get perms
        response = self.client.get(get_perms_url, format="json")
        self.assertEqual(response.status_code, 403)
        # set perms
        resource_perm_spec["uuid"] = resource.uuid
        response = self.client.put(set_perms_url, data=resource_perm_spec, format="json")
        self.assertEqual(response.status_code, 403)
        # login resourse owner
        # get perms
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(get_perms_url, format="json")
        self.assertEqual(response.status_code, 200)
        # set perms
        response = self.client.put(set_perms_url, data=resource_perm_spec, format="json")
        self.assertEqual(response.status_code, 200)

    def test_featured_and_published_resources(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = reverse("base-resources-list")
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        resources = ResourceBase.objects.filter(owner__username="bobby", metadata_only=False)

        url = urljoin(f"{reverse('base-resources-list')}/", "featured/")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], 0)
        # Pagination
        self.assertEqual(len(response.data["resources"]), 0)

        resources.filter(resource_type="map").update(featured=True)
        url = urljoin(f"{reverse('base-resources-list')}/", "featured/")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data["total"], resources.filter(resource_type="map").count())
        # Pagination
        self.assertEqual(len(response.data["resources"]), resources.filter(resource_type="map").count())

    def test_resource_types(self):
        """
        Ensure we can Get & Set Permissions across the Resource Base list.
        """
        url = urljoin(f"{reverse('base-resources-list')}/", "resource_types/")
        response = self.client.get(url, format="json")
        r_types = [item for item in response.data["resource_types"]]
        r_type_names = [r_type["name"] for r_type in r_types]
        self.assertEqual(response.status_code, 200)
        self.assertTrue("resource_types" in response.data)
        self.assertTrue("dataset" in r_type_names)
        self.assertTrue("map" in r_type_names)
        self.assertTrue("document" in r_type_names)
        self.assertFalse("service" in r_type_names)

        r_type_perms = {r_type["name"]: r_type["allowed_perms"] for r_type in r_types}
        _pp_e = {
            "perms": {
                "anonymous": ["view_resourcebase", "download_resourcebase"],
                "default": [
                    "delete_resourcebase",
                    "view_resourcebase",
                    "change_resourcebase_metadata",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "change_resourcebase_metadata",
                    "download_resourcebase",
                    "change_dataset_data",
                    "change_dataset_style",
                ],
                "registered-members": [
                    "delete_resourcebase",
                    "view_resourcebase",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "change_resourcebase_metadata",
                    "download_resourcebase",
                    "change_dataset_data",
                    "change_dataset_style",
                ],
            },
            "compact": {
                "anonymous": [
                    {"name": "none", "label": "None"},
                    {"name": "view", "label": "View"},
                    {"name": "download", "label": "Download"},
                ],
                "default": [
                    {"name": "view", "label": "View"},
                    {"name": "download", "label": "Download"},
                    {"name": "edit", "label": "Edit"},
                    {"name": "manage", "label": "Manage"},
                    {"name": "owner", "label": "Owner"},
                    {"name": "owner", "label": "Owner"},
                ],
                "registered-members": [
                    {"name": "none", "label": "None"},
                    {"name": "view", "label": "View"},
                    {"name": "download", "label": "Download"},
                    {"name": "edit", "label": "Edit"},
                    {"name": "manage", "label": "Manage"},
                ],
            },
        }
        self.assertListEqual(
            list(r_type_perms["dataset"].keys()),
            list(_pp_e.keys()),
            f"dataset : {list(r_type_perms['dataset'].keys())}",
        )
        for _key in r_type_perms["dataset"]["perms"].keys():
            self.assertListEqual(
                sorted(list(set(r_type_perms["dataset"]["perms"].get(_key)))),
                sorted(list(set(_pp_e["perms"].get(_key)))),
                f"{_key} : {list(set(r_type_perms['dataset']['perms'].get(_key)))}",
            )
        for _key in r_type_perms["dataset"]["compact"].keys():
            self.assertListEqual(
                r_type_perms["dataset"]["compact"].get(_key),
                _pp_e["compact"].get(_key),
                f"{_key} : {r_type_perms['dataset']['compact'].get(_key)}",
            )

        _pp_e = {
            "perms": {
                "anonymous": ["view_resourcebase", "download_resourcebase"],
                "default": [
                    "change_resourcebase_metadata",
                    "delete_resourcebase",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "view_resourcebase",
                    "download_resourcebase",
                ],
                "registered-members": [
                    "change_resourcebase_metadata",
                    "delete_resourcebase",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "view_resourcebase",
                    "download_resourcebase",
                ],
            },
            "compact": {
                "anonymous": [
                    {"name": "none", "label": "None"},
                    {"name": "view", "label": "View Metadata"},
                    {"name": "download", "label": "View and Download"},
                ],
                "default": [
                    {"name": "view", "label": "View Metadata"},
                    {"name": "download", "label": "View and Download"},
                    {"name": "edit", "label": "Edit"},
                    {"name": "manage", "label": "Manage"},
                    {"name": "owner", "label": "Owner"},
                    {"name": "owner", "label": "Owner"},
                ],
                "registered-members": [
                    {"name": "none", "label": "None"},
                    {"name": "view", "label": "View Metadata"},
                    {"name": "download", "label": "View and Download"},
                    {"name": "edit", "label": "Edit"},
                    {"name": "manage", "label": "Manage"},
                ],
            },
        }
        self.assertListEqual(
            list(r_type_perms["document"].keys()),
            list(_pp_e.keys()),
            f"document : {list(r_type_perms['document'].keys())}",
        )
        for _key in r_type_perms["document"]["perms"].keys():
            self.assertListEqual(
                sorted(list(set(r_type_perms["document"]["perms"].get(_key)))),
                sorted(list(set(_pp_e["perms"].get(_key)))),
                f"{_key} : {list(set(r_type_perms['document']['perms'].get(_key)))}",
            )
        for _key in r_type_perms["document"]["compact"].keys():
            self.assertListEqual(
                r_type_perms["document"]["compact"].get(_key),
                _pp_e["compact"].get(_key),
                f"{_key} : {r_type_perms['document']['compact'].get(_key)}",
            )

        _pp_e = {
            "perms": {
                "anonymous": [
                    "view_resourcebase",
                ],
                "default": [
                    "change_resourcebase_metadata",
                    "delete_resourcebase",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "view_resourcebase",
                ],
                "registered-members": [
                    "change_resourcebase_metadata",
                    "delete_resourcebase",
                    "change_resourcebase_permissions",
                    "publish_resourcebase",
                    "change_resourcebase",
                    "view_resourcebase",
                ],
            },
            "compact": {
                "anonymous": [{"name": "none", "label": "None"}, {"name": "view", "label": "View"}],
                "default": [
                    {"name": "view", "label": "View"},
                    {"name": "edit", "label": "Edit"},
                    {"name": "manage", "label": "Manage"},
                    {"name": "owner", "label": "Owner"},
                    {"name": "owner", "label": "Owner"},
                ],
                "registered-members": [
                    {"name": "none", "label": "None"},
                    {"name": "view", "label": "View"},
                    {"name": "edit", "label": "Edit"},
                    {"name": "manage", "label": "Manage"},
                ],
            },
        }
        self.assertListEqual(
            list(r_type_perms["map"].keys()), list(_pp_e.keys()), f"map : {list(r_type_perms['map'].keys())}"
        )
        for _key in r_type_perms["map"]["perms"].keys():
            self.assertListEqual(
                sorted(list(set(r_type_perms["map"]["perms"].get(_key)))),
                sorted(list(set(_pp_e["perms"].get(_key)))),
                f"{_key} : {list(set(r_type_perms['map']['perms'].get(_key)))}",
            )
        for _key in r_type_perms["map"]["compact"].keys():
            self.assertListEqual(
                r_type_perms["map"]["compact"].get(_key),
                _pp_e["compact"].get(_key),
                f"{_key} : {r_type_perms['map']['compact'].get(_key)}",
            )

    def test_get_favorites(self):
        """
        Ensure we get user's favorite resources.
        """
        dataset = Dataset.objects.first()
        url = urljoin(f"{reverse('base-resources-list')}/", "favorites/")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 403)
        # Authenticated user
        bobby = get_user_model().objects.get(username="bobby")
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        favorite = Favorite.objects.create_favorite(dataset, bobby)
        response = self.client.get(url, format="json")
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(response.status_code, 200)
        # clean up
        favorite.delete()

    def test_get_favorites_is_returned_in_the_base_endpoint_per_user(self):
        """
        Ensure we get user's favorite resources.
        """
        dataset = Dataset.objects.order_by("-last_updated").first()
        url = reverse("base-resources-list")
        bobby = get_user_model().objects.get(username="bobby")

        self.client.login(username="bobby", password="bob")

        favorite = Favorite.objects.create_favorite(dataset, bobby)

        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        resource_have_tag = [r.get("favorite", False) for r in response.json().get("resources", {})]

        # check that there is at last 1 favorite for the user
        self.assertTrue(any(resource_have_tag))
        # clean up
        favorite.delete()

        self.client.login(username="admin", password="admin")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        resource_have_tag = [r.get("favorite", False) for r in response.json().get("resources", {})]
        # the admin should not have any favorite assigned to him
        self.assertFalse(all(resource_have_tag))

    def test_get_favorites_is_returned_in_the_base_endpoint(self):
        """
        Ensure we get user's favorite resources.
        """
        url = reverse("base-resources-list")

        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(url, format="json")

        self.assertEqual(response.status_code, 200)
        resource_have_tag = ["favorite" in r.keys() for r in response.json().get("resources", {})]
        self.assertTrue(all(resource_have_tag))

    def test_create_and_delete_favorites(self):
        """
        Ensure we can add and remove resources to user's favorite.
        """
        bobby = get_user_model().objects.get(username="bobby")
        dataset = create_single_dataset(name="test_dataset_for_fav", owner=bobby)
        dataset.set_permissions({"users": {"bobby": ["base.add_resourcebase"]}})
        url = urljoin(f"{reverse('base-resources-list')}/", f"{dataset.pk}/favorite/")
        # Anonymous
        response = self.client.post(url, format="json")
        self.assertEqual(response.status_code, 403)
        # Authenticated user
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.post(url, format="json")
        self.assertEqual(response.data["message"], "Successfuly added resource to favorites")
        self.assertEqual(response.status_code, 201)
        # add resource to favorite again
        response = self.client.post(url, format="json")
        self.assertEqual(response.data["message"], "Resource is already in favorites")
        self.assertEqual(response.status_code, 400)
        # remove resource from favorites
        response = self.client.delete(url, format="json")
        self.assertEqual(response.data["message"], "Successfuly removed resource from favorites")
        self.assertEqual(response.status_code, 200)
        # remove resource to favorite again
        response = self.client.delete(url, format="json")
        self.assertEqual(response.data["message"], "Resource not in favorites")
        self.assertEqual(response.status_code, 404)
        dataset.delete()

    def test_search_resources_with_favorite_true_and_no_favorite_should_return_0(self):
        """
        Ensure we can search across the Resource Base list.
        """
        url = reverse("base-resources-list")
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get(f"{url}?favorite=true", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        # No favorite are saved, so the total should be 0
        self.assertEqual(response.data["total"], 0)
        self.assertEqual(len(response.data["resources"]), 0)

    def test_search_resources_with_favorite_true_and_favorite_should_return_1(self):
        """
        Ensure we can search across the Resource Base list.
        """
        url = reverse("base-resources-list")
        # Admin
        admin = get_user_model().objects.get(username="admin")
        dataset = Dataset.objects.first()
        Favorite.objects.create_favorite(dataset, admin)

        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get(f"{url}?favorite=true", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        # 1 favorite is saved, so the total should be 1
        self.assertEqual(response.data["total"], 1)
        self.assertEqual(len(response.data["resources"]), 1)

    def test_search_resources_with_favorite_true_with_geoapps_icluded(self):
        url = reverse("base-resources-list")
        # Admin
        admin = get_user_model().objects.get(username="admin")
        try:
            geo_app = GeoApp.objects.create(title="Test GeoApp Favorite", owner=admin, resource_type="geostory")
            Favorite.objects.create_favorite(geo_app, admin)

            self.assertTrue(self.client.login(username="admin", password="admin"))

            response = self.client.get(f"{url}?favorite=true", format="json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data["total"], 1)
            self.assertEqual(len(response.data["resources"]), 1)
        finally:
            geo_app.delete()

    def test_thumbnail_urls(self):
        """
        Ensure the thumbnail url reflects the current active Thumb on the resource.
        """
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        resource = ResourceBase.objects.filter(owner__username="bobby").first()
        url = reverse("base-resources-detail", kwargs={"pk": resource.pk})
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.data["resource"]["pk"]), int(resource.pk))
        thumbnail_url = response.data["resource"]["thumbnail_url"]
        self.assertIsNone(thumbnail_url)

    def test_embed_urls(self):
        """
        Ensure the embed urls reflect the concrete instance ones.
        """
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))

        resources = ResourceBase.objects.all()
        for resource in resources:
            url = f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}?filter{{metadata_only}}=false"
            response = self.client.get(url, format="json")
            if resource.title.endswith("metadata true"):
                self.assertEqual(response.status_code, 404)
            else:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(int(response.data["resource"]["pk"]), int(resource.pk))
                embed_url = response.data["resource"]["embed_url"]
                self.assertIsNotNone(embed_url)

                instance = resource.get_real_instance()
                if hasattr(instance, "embed_url"):
                    if instance.embed_url != NotImplemented:
                        self.assertEqual(build_absolute_uri(instance.embed_url), embed_url)
                    else:
                        self.assertEqual("", embed_url)

    def test_owners_list(self):
        """
        Ensure we can access the list of owners.
        """
        url = reverse("owners-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 8)

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 8)
        response = self.client.get(f"{url}?type=geoapp", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 0)
        response = self.client.get(f"{url}?type=dataset&title__icontains=CA", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)
        # response has link to the response
        self.assertTrue("link" in response.data["owners"][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 8)

        # Owners Filtering
        response = self.client.get(f"{url}?filter{{username.icontains}}=bobby", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)

    def test_categories_list(self):
        """
        Ensure we can access the list of categories.
        """
        url = reverse("categories-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], TopicCategory.objects.count())

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], TopicCategory.objects.count())
        # response has link to the response
        self.assertTrue("link" in response.data["categories"][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], TopicCategory.objects.count())

        # Categories Filtering
        response = self.client.get(f"{url}?filter{{identifier.icontains}}=biota", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 1)

    def test_regions_list(self):
        """
        Ensure we can access the list of regions.
        """
        url = reverse("regions-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], Region.objects.count())

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], Region.objects.count())
        # response has link to the response
        self.assertTrue("link" in response.data["regions"][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], Region.objects.count())

        # Regions Filtering
        response = self.client.get(f"{url}?filter{{name.icontains}}=Africa", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 8)

    def test_regions_with_resources(self):
        """
        Ensure we can access the list of regions.
        """
        self.assertTrue(self.client.login(username="admin", password="admin"))
        url = reverse("regions-list")
        response = self.client.get(f"{url}?with_resources=True", format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 0)

        self.assertTrue(self.client.login(username="admin", password="admin"))
        url = reverse("regions-list")
        response = self.client.get(f"{url}?with_resources=False", format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], Region.objects.count())

        self.assertTrue(self.client.login(username="admin", password="admin"))
        url = reverse("regions-list")
        response = self.client.get(f"{url}", format="json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], Region.objects.count())

    def test_keywords_list(self):
        """
        Ensure we can access the list of keywords.
        """
        url = reverse("keywords-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], len(HierarchicalKeyword.resource_keywords_tree(None)))

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        admin = get_user_model().objects.get(username="admin")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], len(HierarchicalKeyword.resource_keywords_tree(admin)))
        # response has link to the response
        if response.data["total"] > 0:
            self.assertTrue("link" in response.data["keywords"][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        bobby = get_user_model().objects.get(username="bobby")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], len(HierarchicalKeyword.resource_keywords_tree(bobby)))

        # Keywords Filtering
        response = self.client.get(f"{url}?filter{{name.icontains}}=Africa", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 0)

        # Testing Hierarchical Keywords tree
        try:
            HierarchicalKeyword.objects.filter(slug__in=["a", "a1", "a2", "b", "b1"]).delete()
            HierarchicalKeyword.add_root(name="a")
            HierarchicalKeyword.add_root(name="b")
            a = HierarchicalKeyword.objects.get(slug="a")
            b = HierarchicalKeyword.objects.get(slug="b")
            a.add_child(name="a1")
            a.add_child(name="a2")
            b.add_child(name="b1")
            resources = ResourceBase.objects.filter(owner__username="bobby")
            res1 = resources.first()
            res2 = resources.last()
            self.assertNotEqual(res1, res2)
            res1.keywords.add(HierarchicalKeyword.objects.get(slug="a1"))
            res1.keywords.add(HierarchicalKeyword.objects.get(slug="a2"))
            res2.keywords.add(HierarchicalKeyword.objects.get(slug="b1"))
            resource_keywords = HierarchicalKeyword.resource_keywords_tree(bobby)
            logger.error(resource_keywords)

            """
            Final api outcome will be something like
            [
                {
                    'id': 116,
                    'text': 'a',
                    'href': 'a',
                    'tags': [],
                    'nodes': [
                        {
                            'id': 118,
                            'text': 'a1',
                            'href': 'a1',
                            'tags': [1]
                        },
                        {
                            'id': 119,
                            'text': 'a2',
                            'href': 'a2',
                            'tags': [1]
                        }
                    ]
                },
                {
                    'id': 117,
                    'text': 'b',
                    'href': 'b',
                    'tags': [],
                    'nodes': [
                        {
                            'id': 120,
                            'text': 'b1',
                            'href': 'b1',
                            'tags': [1]
                        }
                    ]
                },
                ...
            ]
            """
            url = reverse("keywords-list")
            # Authenticated user
            self.assertTrue(self.client.login(username="bobby", password="bob"))
            response = self.client.get(url, format="json")
            self.assertEqual(response.status_code, 200)
            for _kw in response.data["keywords"]:
                if _kw.get("href") in ["a", "b"]:
                    self.assertListEqual(_kw.get("tags"), [], _kw.get("tags"))
                    self.assertEqual(len(_kw.get("nodes")), 2)
                    for _kw_child in _kw.get("nodes"):
                        self.assertEqual(_kw_child.get("tags")[0], 1)
        finally:
            HierarchicalKeyword.objects.filter(slug__in=["a", "a1", "a2", "b", "b1"]).delete()

    def test_tkeywords_list(self):
        """
        Ensure we can access the list of thasaurus keywords.
        """
        url = reverse("tkeywords-list")
        # Anonymous
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], ThesaurusKeyword.objects.count())

        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], ThesaurusKeyword.objects.count())
        # response has uri to the response
        self.assertTrue("uri" in response.data["tkeywords"][0].keys())

        # Authenticated user
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], ThesaurusKeyword.objects.count())

    def test_set_resource_thumbnail(self):
        re_uuid = "[0-F]{8}-([0-F]{4}-){3}[0-F]{12}"
        resource = Dataset.objects.first()
        url = reverse("base-resources-set_thumbnail", args=[resource.pk])
        data = {"file": "http://localhost:8000/thumb.png"}

        # Anonymous user
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 403)

        # Authenticated user
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["thumbnail_url"], data["file"])
        self.assertEqual(Dataset.objects.get(pk=resource.pk).thumbnail_url, data["file"])
        # set with invalid image url
        data = {"file": "invali url"}
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        expected = {
            "success": False,
            "errors": ["file is either a file upload, ASCII byte string or a valid image url string"],
            "code": "invalid",
        }
        self.assertEqual(response.json(), expected)
        # Test with non image url
        data = {"file": "http://localhost:8000/thumb.txt"}
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), "The url must be of an image with format (png, jpeg or jpg)")

        # using Base64 data as an ASCII byte string
        data["file"] = (
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAABHNCSVQICAgI\
        fAhkiAAAABl0RVh0U29mdHdhcmUAZ25vbWUtc2NyZWVuc2hvdO8Dvz4AAAANSURBVAiZYzAxMfkPAALYAZzx61+bAAAAAElFTkSuQmCC"
        )
        with patch("geonode.base.models.is_monochromatic_image") as _mck:
            _mck.return_value = False
            response = self.client.put(url, data=data, format="json")
            self.assertEqual(response.status_code, 200)
            self.assertIsNotNone(
                re.search(
                    f"dataset-{re_uuid}-thumb-{re_uuid}.jpg", Dataset.objects.get(pk=resource.pk).thumbnail_url, re.I
                )
            )
            # File upload
            with patch("PIL.Image.open") as _mck:
                _mck.return_value = test_image
                # rest thumbnail_url to None
                resource.thumbnail_url = None
                resource.save()
                self.assertEqual(Dataset.objects.get(pk=resource.pk).thumbnail_url, None)
                f = SimpleUploadedFile("test_image.png", BytesIO(test_image.tobytes()).read(), "image/png")
                response = self.client.put(url, data={"file": f})
                self.assertIsNotNone(
                    re.search(
                        f"dataset-{re_uuid}-thumb-{re_uuid}.jpg",
                        Dataset.objects.get(pk=resource.pk).thumbnail_url,
                        re.I,
                    )
                )
                self.assertEqual(response.status_code, 200)

    def test_set_thumbnail_from_bbox_from_Anonymous_user_raise_permission_error(self):
        """
        Given a request with Anonymous user, should raise an authentication error.
        """
        dataset_id = sys.maxsize
        url = reverse("base-resources-set-thumb-from-bbox", args=[dataset_id])
        # Anonymous
        expected = {
            "success": False,
            "errors": ["Authentication credentials were not provided."],
            "code": "not_authenticated",
        }
        response = self.client.post(url, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(expected, response.json())

    @patch("geonode.base.api.views.create_thumbnail")
    def test_set_thumbnail_from_bbox_from_logged_user_for_existing_dataset(self, mock_create_thumbnail):
        """
        Given a logged User and an existing dataset, should create the expected thumbnail url.
        """
        mock_create_thumbnail.return_value = "http://localhost:8000/mocked_url.jpg"
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = Dataset.objects.first().resourcebase_ptr_id
        url = reverse("base-resources-set-thumb-from-bbox", args=[dataset_id])
        payload = {
            "bbox": [-9072629.904175375, -9043966.018568434, 1491839.8773032012, 1507127.2829602365],
            "srid": "EPSG:3857",
        }
        response = self.client.post(url, data=payload, format="json")

        expected = {
            "message": "Thumbnail correctly created.",
            "success": True,
            "thumbnail_url": "http://localhost:8000/mocked_url.jpg",
        }
        self.assertEqual(response.status_code, 200)
        self.assertEqual(expected, response.json())

    def test_set_thumbnail_from_bbox_from_logged_user_for_not_existing_dataset(self):
        """
        Given a logged User and an not existing dataset, should raise a 404 error.
        """
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = sys.maxsize
        url = reverse("base-resources-set-thumb-from-bbox", args=[dataset_id])
        payload = {
            "bbox": [-9072629.904175375, -9043966.018568434, 1491839.8773032012, 1507127.2829602365],
            "srid": "EPSG:3857",
        }
        response = self.client.post(url, data=payload, format="json")

        expected = {"message": f"Resource selected with id {dataset_id} does not exists", "success": False}
        self.assertEqual(response.status_code, 404)
        self.assertEqual(expected, response.json())

    def test_set_thumbnail_from_bbox_from_logged_user_for_existing_doc(self):
        """
        Given a logged User and an existing doc, should raise a NotImplemented.
        """
        # Admin
        self.client.login(username="admin", password="admin")
        dataset_id = Document.objects.first().resourcebase_ptr_id
        url = reverse("base-resources-set-thumb-from-bbox", args=[dataset_id])
        payload = {"bbox": [], "srid": "EPSG:3857"}
        response = self.client.post(url, data=payload, format="json")

        expected = {"message": "Not implemented: Endpoint available only for Dataset and Maps", "success": False}
        self.assertEqual(response.status_code, 405)
        self.assertEqual(expected, response.json())

    @patch(
        "geonode.base.api.views.create_thumbnail", side_effect=ThumbnailError("Some exception during thumb creation")
    )
    def test_set_thumbnail_from_bbox_from_logged_user_for_existing_dataset_raise_exp(self, mock_exp):
        """
        Given a logged User and an existing dataset, should raise a ThumbnailException.
        """
        # Admin
        self.assertTrue(self.client.login(username="admin", password="admin"))
        dataset_id = Dataset.objects.first().resourcebase_ptr_id
        url = reverse("base-resources-set-thumb-from-bbox", args=[dataset_id])
        payload = {"bbox": [], "srid": "EPSG:3857"}
        response = self.client.post(url, data=payload, format="json")

        expected = {"message": "Some exception during thumb creation", "success": False}
        self.assertEqual(response.status_code, 500)
        self.assertEqual(expected, response.json())

    def test_manager_can_edit_map(self):
        """
        REST API must not forbid saving maps and apps to non-admin and non-owners.
        """
        self.maxDiff = None
        from geonode.maps.models import Map

        _map = Map.objects.filter(uuid__isnull=False, owner__username="admin").first()
        if not len(_map.uuid):
            _map.uuid = str(uuid4())
            _map.save()
        resource = ResourceBase.objects.filter(uuid=_map.uuid).first()
        bobby = get_user_model().objects.get(username="bobby")

        # Add perms to Bobby
        resource_perm_spec_patch = {
            "uuid": resource.uuid,
            "users": [
                {
                    "id": bobby.id,
                    "username": bobby.username,
                    "first_name": bobby.first_name,
                    "last_name": bobby.last_name,
                    "avatar": "",
                    "permissions": "manage",
                }
            ],
        }

        # Patch the resource perms
        self.assertTrue(self.client.login(username="admin", password="admin"))
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", "permissions")
        response = self.client.patch(set_perms_url, data=resource_perm_spec_patch, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data.get("status"))
        self.assertIsNotNone(response.data.get("status_url"))
        status = response.data.get("status")
        resp_js = json.loads(response.content.decode("utf-8"))
        status_url = resp_js.get("status_url", None)
        execution_id = resp_js.get("execution_id", "")
        self.assertIsNotNone(status_url)
        self.assertIsNotNone(execution_id)
        for _cnt in range(0, 10):
            response = self.client.get(f"{status_url}")
            self.assertEqual(response.status_code, 200)
            resp_js = json.loads(response.content.decode("utf-8"))
            logger.error(f"[{_cnt + 1}] ... {resp_js}")
            if resp_js.get("status", "") == "finished":
                status = resp_js.get("status", "")
                break
            else:
                resouce_service_dispatcher.apply((execution_id,))
                sleep(3.0)
        self.assertTrue(status, ExecutionRequest.STATUS_FINISHED)

        # Test "bobby" can access the "permissions" endpoint
        resource_service_permissions_url = reverse("base-resources-perms-spec", kwargs={"pk": resource.pk})
        response = self.client.get(resource_service_permissions_url, format="json")
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                "users": [
                    {
                        "id": bobby.id,
                        "username": "bobby",
                        "first_name": "bobby",
                        "last_name": "",
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "manage",
                        "is_superuser": False,
                        "is_staff": False,
                    },
                    {
                        "id": 1,
                        "username": "admin",
                        "first_name": "admin",
                        "last_name": "",
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "owner",
                        "is_superuser": True,
                        "is_staff": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": 3, "title": "anonymous", "name": "anonymous", "permissions": "view"},
                    {"id": 2, "title": "Registered Members", "name": "registered-members", "permissions": "none"},
                ],
            },
            resource_perm_spec,
        )

        # Test "bobby" can manage the resource permissions
        get_perms_url = urljoin(
            f"{reverse('base-resources-detail', kwargs={'pk': _map.get_self_resource().pk})}/", "permissions"
        )
        response = self.client.get(get_perms_url, format="json")
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                "users": [
                    {
                        "id": bobby.id,
                        "username": "bobby",
                        "first_name": "bobby",
                        "last_name": "",
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "manage",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "id": 1,
                        "username": "admin",
                        "first_name": "admin",
                        "last_name": "",
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "owner",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": 3, "title": "anonymous", "name": "anonymous", "permissions": "view"},
                    {"id": 2, "title": "Registered Members", "name": "registered-members", "permissions": "none"},
                ],
            },
            resource_perm_spec,
        )

        # Fetch the map perms as user "bobby"
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.get(get_perms_url, format="json")
        self.assertEqual(response.status_code, 200)
        resource_perm_spec = response.data
        self.assertDictEqual(
            resource_perm_spec,
            {
                "users": [
                    {
                        "id": bobby.id,
                        "username": "bobby",
                        "first_name": "bobby",
                        "last_name": "",
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "manage",
                        "is_staff": False,
                        "is_superuser": False,
                    },
                    {
                        "id": 1,
                        "username": "admin",
                        "first_name": "admin",
                        "last_name": "",
                        "avatar": build_absolute_uri(avatar_url(bobby)),
                        "permissions": "owner",
                        "is_staff": True,
                        "is_superuser": True,
                    },
                ],
                "organizations": [],
                "groups": [
                    {"id": 3, "title": "anonymous", "name": "anonymous", "permissions": "view"},
                    {"id": 2, "title": "Registered Members", "name": "registered-members", "permissions": "none"},
                ],
            },
            resource_perm_spec,
        )

    def test_resource_service_copy(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/single_point.shp")
        files_as_dict, _ = get_files(files)
        resource = resource_manager.create(
            str(uuid4()),
            Dataset,
            defaults={
                "owner": get_user_model().objects.get(username="admin"),
                "name": "test_copy",
                "store": "geonode_data",
                "subtype": "vector",
                "alternate": "geonode:test_copy",
            },
        )

        asset, link = create_asset_and_link(
            resource, get_user_model().objects.get(username="admin"), list(files_as_dict.values())
        )
        bobby = get_user_model().objects.get(username="bobby")
        copy_url = reverse("importer_resource_copy", kwargs={"pk": resource.pk})
        response = self.client.put(copy_url, data={"title": "cloned_resource"})
        self.assertEqual(response.status_code, 403)
        # set perms to enable user clone resource
        self.assertTrue(self.client.login(username="admin", password="admin"))
        perm_spec = {
            "uuid": resource.uuid,
            "users": [
                {
                    "id": bobby.id,
                    "username": bobby.username,
                    "first_name": bobby.first_name,
                    "last_name": bobby.last_name,
                    "avatar": "",
                    "permissions": "manage",
                }
            ],
        }
        set_perms_url = urljoin(f"{reverse('base-resources-detail', kwargs={'pk': resource.pk})}/", "permissions")

        response = self.client.patch(set_perms_url, data=perm_spec, format="json")
        self.assertEqual(response.status_code, 200)
        # clone resource
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.put(copy_url)
        self.assertEqual(response.status_code, 200)
        cloned_resource = Dataset.objects.last()
        self.assertEqual(cloned_resource.owner.username, "admin")

        # Check that the 'featured' flag is reset on clone
        resource.refresh_from_db()
        resource.featured = True
        resource.save()
        response = self.client.put(copy_url)
        self.assertEqual(response.status_code, 200)
        second_cloned = Dataset.objects.exclude(pk__in=[resource.pk, cloned_resource.pk]).latest("id")
        self.assertFalse(second_cloned.featured, msg="Cloned resource should have featured=False")

        # clone dataset with invalid file
        # resource.files = ["/path/invalid_file.wrong"]
        # resource.save()
        asset.location = ["/path/invalid_file.wrong"]
        asset.save()
        response = self.client.put(copy_url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Resource can not be cloned.")
        # clone dataset with no files
        link.delete()
        asset.delete()
        response = self.client.put(copy_url)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Resource can not be cloned.")
        # clean
        try:
            resource.delete()
        except Exception as e:
            logger.warning(f"Can't delete test resource {resource}", exc_info=e)

    def test_resource_service_copy_with_perms_dataset(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/single_point.shp")
        files_as_dict, _ = get_files(files)
        resource = Dataset.objects.create(
            owner=get_user_model().objects.get(username="admin"),
            name="test_copy",
            store="geonode_data",
            subtype="vector",
            alternate="geonode:test_copy",
            resource_type="dataset",
            uuid=str(uuid4()),
        )
        _, _ = create_asset_and_link(
            resource, get_user_model().objects.get(username="admin"), list(files_as_dict.values())
        )
        self._assertCloningWithPerms(resource)

    @patch.dict(os.environ, {"ASYNC_SIGNALS": "False"})
    @override_settings(ASYNC_SIGNALS=False)
    def test_resource_service_copy_with_perms_dataset_set_default_perms(self):
        with self.settings(ASYNC_SIGNALS=False):
            files = os.path.join(gisdata.GOOD_DATA, "vector/single_point.shp")
            files_as_dict, _ = get_files(files)
            resource = resource_manager.create(
                None,
                resource_type=Dataset,
                defaults={
                    "owner": get_user_model().objects.first(),
                    "title": "test_copy_with_perms",
                    "name": "test_copy_with_perms",
                    "is_approved": True,
                    "store": "geonode_data",
                    "subtype": "vector",
                    "resource_type": "dataset",
                    "files": files_as_dict.values(),
                },
            )
            _perms = {
                "users": {"bobby": ["base.add_resourcebase", "base.download_resourcebase"]},
                "groups": {"anonymous": ["base.view_resourcebase", "base.download_resourcebase"]},
            }
            resource.set_permissions(_perms)
            # checking that bobby is in the original dataset perms list
            self.assertTrue("bobby" in "bobby" in [x.username for x in resource.get_all_level_info().get("users", [])])
            # copying the resource, should remove the perms for bobby
            # only the default perms should be available
            copy_url = reverse("importer_resource_copy", kwargs={"pk": resource.pk})

            self.assertTrue(self.client.login(username="admin", password="admin"))

            response = self.client.put(copy_url)
            self.assertEqual(response.status_code, 200)

            resouce_service_dispatcher.apply((response.json().get("execution_id"),))

        self.assertEqual("finished", self.client.get(response.json().get("status_url")).json().get("status"))
        _resource = Dataset.objects.filter(title__icontains="test_copy_with_perms").last()
        self.assertIsNotNone(_resource)
        self.assertNotIn("bobby", [x.username for x in _resource.get_all_level_info().get("users", [])])
        self.assertIn("admin", [x.username for x in _resource.get_all_level_info().get("users", [])])

    def test_resource_service_copy_with_perms_doc(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/single_point.shp")
        files_as_dict, _ = get_files(files)
        resource = Document.objects.create(
            owner=get_user_model().objects.get(username="admin"),
            subtype="vector",
            alternate="geonode:test_copy",
            resource_type="document",
            uuid=str(uuid4()),
        )
        _, _ = create_asset_and_link(
            resource, get_user_model().objects.get(username="admin"), list(files_as_dict.values())
        )
        self._assertCloningWithPerms(resource)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_resource_service_copy_with_perms_map(self):
        files = os.path.join(gisdata.GOOD_DATA, "vector/single_point.shp")
        files_as_dict, _ = get_files(files)
        resource = Document.objects.create(
            owner=get_user_model().objects.get(username="admin"),
            alternate="geonode:test_copy",
            resource_type="map",
            uuid=str(uuid4()),
        )
        _, _ = create_asset_and_link(
            resource, get_user_model().objects.get(username="admin"), list(files_as_dict.values())
        )
        self._assertCloningWithPerms(resource)

    def _assertCloningWithPerms(self, resource):
        # login as bobby
        self.assertTrue(self.client.login(username="bobby", password="bob"))

        # bobby cannot copy the resource since he doesnt have all the perms needed
        _perms = {"users": {"bobby": ["base.add_resourcebase"]}, "groups": {"anonymous": []}}
        resource.set_permissions(_perms)
        copy_url = reverse("importer_resource_copy", kwargs={"pk": resource.pk})
        response = self.client.put(copy_url, data={"title": "cloned_resource"})
        self.assertIn(response.status_code, [403, 404])
        # set perms to enable user clone resource
        # bobby can copy the resource since he has all the perms needed
        _perms = {
            "users": {"bobby": ["base.add_resourcebase", "base.download_resourcebase"]},
            "groups": {"anonymous": ["base.view_resourcebase", "base.download_resourcebae"]},
        }
        resource.set_permissions(_perms)
        copy_url = reverse("importer_resource_copy", kwargs={"pk": resource.pk})
        response = self.client.put(copy_url, data={"title": "cloned_resource"})
        self.assertEqual(response.status_code, 200)
        resource.delete()

    def _get_for_object(self, o, viewname):
        url = reverse(viewname, args=[o.id])
        response = self.client.get(url, format="json")
        return response.json()

    def _get_for_map(self, viewname):
        return self._get_for_object(Map.objects.first(), viewname)

    def test_base_resources_return_download_link_if_document(self):
        """
        Ensure we can access the Resource Base list.
        """
        doc = Document.objects.first()

        # From resource base API
        json = self._get_for_object(doc, "base-resources-detail")
        download_url = json.get("resource").get("download_url")
        self.assertEqual(build_absolute_uri(doc.download_url), download_url)

        # from documents api
        json = self._get_for_object(doc, "documents-detail")
        download_url = json.get("document").get("download_url")
        self.assertEqual(build_absolute_uri(doc.download_url), download_url)

    def test_base_resources_return_download_link_if_dataset(self):
        """
        Ensure we can access the Resource Base list.
        """
        _dataset = Dataset.objects.first()

        # From resource base API
        json = self._get_for_object(_dataset, "base-resources-detail")
        download_url = json.get("resource").get("download_url")
        self.assertEqual(_dataset.download_url, download_url)

        # from dataset api
        json = self._get_for_object(_dataset, "datasets-detail")
        download_url = json.get("dataset").get("download_url")
        self.assertEqual(_dataset.download_url, download_url)

    def test_base_resources_dont_return_download_link_if_map(self):
        """
        Ensure we can access the Resource Base list.
        """
        # From resource base API
        json = self._get_for_map("base-resources-detail")
        download_url = json.get("resource").get("download_url", None)
        self.assertIsNone(download_url)

        # from maps api
        json = self._get_for_map("maps-detail")
        download_url = json.get("map").get("download_url")
        self.assertIsNone(download_url)

    def test_base_resources_return_not_download_links_for_maps(self):
        """
        Ensure we can access the Resource Base list.
        """
        # From resource base API
        json = self._get_for_map("base-resources-detail")
        download_url = json.get("resource").get("download_urls", None)
        self.assertListEqual([], download_url)

        # from maps api
        json = self._get_for_map("maps-detail")
        download_url = json.get("map").get("download_urls")
        self.assertListEqual([], download_url)

    def test_base_resources_return_download_links_for_documents(self):
        """
        Ensure we can access the Resource Base list.
        """
        doc = Document.objects.first()
        asset = get_default_asset(doc)
        handler = asset_handler_registry.get_handler(asset)
        expected_payload = [
            {"url": build_absolute_uri(doc.download_url), "ajax_safe": doc.download_is_ajax_safe},
            {"ajax_safe": False, "default": False, "url": handler.create_download_url(asset)},
        ]
        # From resource base API
        json = self._get_for_object(doc, "base-resources-detail")
        download_url = json.get("resource").get("download_urls")
        self.assertListEqual(expected_payload, download_url)

        # from documents api
        json = self._get_for_object(doc, "documents-detail")
        download_url = json.get("document").get("download_urls")
        self.assertListEqual(expected_payload, download_url)

    def test_base_resources_return_download_links_for_datasets(self):
        """
        Ensure we can access the Resource Base list.
        """
        _dataset = Dataset.objects.first()
        expected_payload = [
            {"url": reverse("dataset_download", args=[_dataset.alternate]), "ajax_safe": True, "default": True}
        ]

        # From resource base API
        json = self._get_for_object(_dataset, "base-resources-detail")
        download_url = json.get("resource").get("download_urls")
        self.assertEqual(expected_payload, download_url)

        # from dataset api
        json = self._get_for_object(_dataset, "datasets-detail")
        download_url = json.get("dataset").get("download_urls")
        self.assertEqual(expected_payload, download_url)

    def test_include_linked_resources(self):
        dataset = Dataset.objects.first()
        doc = Document.objects.first()
        map = Map.objects.first()

        for resource, typed_viewname in (
            (dataset, "datasets-detail"),
            (doc, "documents-detail"),
            (map, "maps-detail"),
        ):
            for viewname in (typed_viewname, "base-resources-detail"):
                for include in (True, False):
                    url = reverse(viewname, args=[resource.id])
                    url = f"{url}{'?include[]=linked_resources' if include else ''}"
                    response = self.client.get(url, format="json").json()
                    json = next(iter(response.values()))
                    if include:
                        self.assertIn("linked_resources", json, "Missing content")
                    else:
                        self.assertNotIn("linked_resources", json, "Unexpected content")

    def test_exclude_all_but_one(self):
        dataset = Dataset.objects.first()
        doc = Document.objects.first()
        map = Map.objects.first()

        for resource, typed_viewname in (
            (dataset, "datasets-detail"),
            (doc, "documents-detail"),
            (map, "maps-detail"),
        ):
            for viewname in (typed_viewname, "base-resources-detail"):
                for field in (
                    "pk",
                    "title",
                    "perms",
                    "links",
                    "linked_resources",
                    "data",
                    "link",
                ):  # test some random fields
                    url = reverse(viewname, args=[resource.id])
                    url = f"{url}?exclude[]=*&include[]={field}"
                    response = self.client.get(url, format="json").json()
                    json = next(iter(response.values()))

                    self.assertIn(field, json, "Missing content")
                    self.assertEqual(1, len(json), f"Only expected content was '{field}', found: {json}")

    def test_presets_base(self):
        dataset = Dataset.objects.first()
        doc = Document.objects.first()
        map = Map.objects.first()

        for resource, typed_viewname in (
            (dataset, "datasets-detail"),
            (doc, "documents-detail"),
            (map, "maps-detail"),
        ):
            for viewname in (typed_viewname, "base-resources-detail"):
                url = reverse(viewname, args=[resource.id])
                url = f"{url}?api_preset=bare"
                response = self.client.get(url, format="json").json()
                json = next(iter(response.values()))
                self.assertSetEqual(
                    {"pk", "title"},
                    set(json.keys()),
                    f"Bad json content for object {type(resource)} JSON:{json}",
                )

    def test_api_should_return_all_resources_for_admin(self):
        """
        Api whould return all resources even if advertised=False.
        """
        url = reverse("base-resources-list")
        self.client.login(username="admin", password="admin")
        payload = self.client.get(url)
        prev_count = payload.json().get("total")
        # update all the resource to advertised=False
        Dataset.objects.update(advertised=False)
        url = reverse("base-resources-list")
        payload = self.client.get(url)
        new_count = payload.json().get("total")
        self.assertEqual(new_count, prev_count)

        Dataset.objects.update(advertised=True)

    def test_api_should_return_advertised_resource_if_anonymous(self):
        """
        If anonymous user, only the advertised resoruces whould be returned by the API.
        """
        url = reverse("base-resources-list")
        payload = self.client.get(url)
        prev_count = payload.json().get("total")
        # update all the resource to advertised=False
        Dataset.objects.update(advertised=False)
        url = reverse("base-resources-list")
        payload = self.client.get(url)
        new_count = payload.json().get("total")
        self.assertNotEqual(new_count, prev_count)

        Dataset.objects.update(advertised=True)

    def test_api_should_return_only_the_advertised_false_where_user_is_owner(self):
        """
        Api Should return all the resource with advertised=True
        And the resource with advertised=False if is owner of it
        """
        # defining a new user
        test_user_for_api = get_user_model().objects.create(username="test_user_for_api", password="password")
        # creating a new resource for the user with advertised=False
        dataset = create_single_dataset(name="test_resource_for_api", owner=test_user_for_api, advertised=False)
        url = reverse("base-resources-list")
        self.client.force_login(test_user_for_api)
        payload = self.client.get(f"{url}?limit=1000")
        # the uuid of the dataset is in the returned payload
        self.assertTrue(dataset.uuid in [k["uuid"] for k in payload.json()["resources"]])
        # bobby is not able to see the dataset belonging to the previous user
        self.client.login(username="bobby", password="bob")
        payload = self.client.get(url)
        self.assertFalse(dataset.uuid in [k["uuid"] for k in payload.json()["resources"]])

        # cleanup
        dataset.delete()
        test_user_for_api.delete()

    def test_api_should_filter_by_advertised_param(self):
        """
        If anonymous user, only the advertised resoruces whould be returned by the API.
        """
        dts = create_single_dataset("advertised_false")
        dts.advertised = False
        dts.save()
        # should show the result based on the logic
        url = reverse("base-resources-list")
        payload = self.client.get(url)
        prev_count = payload.json().get("total")
        # the user can see only the advertised resources
        self.assertEqual(ResourceBase.objects.filter(advertised=True).count(), prev_count)

        payload = self.client.get(f"{url}?advertised=True")
        # so if advertised is True, we dont see the advertised=False resource
        new_count = payload.json().get("total")
        # recheck the count
        self.assertEqual(new_count, prev_count)

        payload = self.client.get(f"{url}?advertised=False")
        # so if advertised is False, we see only the resource with advertised==False
        new_count = payload.json().get("total")
        # recheck the count
        self.assertEqual(new_count, 1)

        # if all is requested, we will see all the resources
        payload = self.client.get(f"{url}?advertised=all")
        new_count = payload.json().get("total")
        # recheck the count
        self.assertEqual(new_count, prev_count + 1)

        Dataset.objects.update(advertised=True)

    def test_metadata_uploaded_preserve_can_be_updated(self):
        doc = Document.objects.first()
        user = get_user_model().objects.get(username="bobby")
        url = reverse("base-resources-detail", kwargs={"pk": doc.pk})
        self.assertTrue(self.client.login(username="bobby", password="bob"))

        payload = json.dumps({"metadata_uploaded_preserve": True})
        # should return 403 since bobby doesn't have the perms to update the metadata
        # on this resource
        response = self.client.patch(url, data=payload, content_type="application/json")
        self.assertEqual(403, response.status_code)
        doc.refresh_from_db()
        # the original value should be kept
        self.assertFalse(doc.metadata_uploaded_preserve)

        # let's give to bobby the perms for update the metadata
        assign_perm("base.change_resourcebase_metadata", user, doc.get_self_resource())

        # let's call the API again
        response = self.client.patch(url, data=payload, content_type="application/json")
        self.assertEqual(200, response.status_code)
        doc.refresh_from_db()
        # the value should be updated
        self.assertTrue(doc.metadata_uploaded_preserve)
        self.assertTrue(response.json()["resource"]["metadata_uploaded_preserve"])


class TestExtraMetadataBaseApi(GeoNodeBaseTestSupport):
    def setUp(self):
        self.layer = create_single_dataset("single_layer")
        self.metadata = {
            "filter_header": "Foo Filter header",
            "field_name": "metadata-name",
            "field_label": "this is the help text",
            "field_value": "foo",
        }
        m = ExtraMetadata.objects.create(resource=self.layer, metadata=self.metadata)
        self.layer.metadata.add(m)
        self.mdata = ExtraMetadata.objects.first()

    def test_get_will_return_the_list_of_extra_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse("base-resources-extra-metadata", args=[self.layer.id])
        response = self.client.get(url, content_type="application/json")
        self.assertTrue(200, response.status_code)
        expected = [{**{"id": self.mdata.id}, **self.metadata}]
        self.assertEqual(expected, response.json())

    def test_put_will_update_the_whole_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse("base-resources-extra-metadata", args=[self.layer.id])
        input_metadata = {
            "id": self.mdata.id,
            "filter_header": "Foo Filter header",
            "field_name": "metadata-updated",
            "field_label": "this is the help text",
            "field_value": "foo",
        }
        response = self.client.put(url, data=[input_metadata], content_type="application/json")
        self.assertTrue(200, response.status_code)
        self.assertEqual([input_metadata], response.json())

    def test_post_will_add_new_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse("base-resources-extra-metadata", args=[self.layer.id])
        input_metadata = {
            "filter_header": "Foo Filter header",
            "field_name": "metadata-updated",
            "field_label": "this is the help text",
            "field_value": "foo",
        }
        response = self.client.post(url, data=[input_metadata], content_type="application/json")
        self.assertTrue(201, response.status_code)
        self.assertEqual(2, len(response.json()))

    def test_delete_will_delete_single_metadata(self):
        self.client.login(username="admin", password="admin")
        url = reverse("base-resources-extra-metadata", args=[self.layer.id])
        response = self.client.delete(url, data=[self.mdata.id], content_type="application/json")
        self.assertTrue(200, response.status_code)
        self.assertEqual([], response.json())

    def test_user_without_view_perms_cannot_see_the_endpoint(self):
        from geonode.resource.manager import resource_manager

        self.client.login(username="bobby", password="bob")
        resource_manager.remove_permissions(self.layer.uuid, instance=self.layer.get_self_resource())
        url = reverse("base-resources-extra-metadata", args=[self.layer.id])
        response = self.client.get(url, content_type="application/json")
        self.assertTrue(403, response.status_code)

        perm_spec = {"users": {"bobby": ["view_resourcebase"]}, "groups": {}}
        self.layer.set_permissions(perm_spec)
        url = reverse("base-resources-extra-metadata", args=[self.layer.id])
        response = self.client.get(url, content_type="application/json")
        self.assertTrue(200, response.status_code)


class TestApiLinkedResources(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dataset = create_single_dataset("single_layer")
        cls.map = create_single_map("single_map")
        cls.doc = create_single_doc("single_doc")

    def test_only_get_method_is_available(self):
        url = reverse("base-resources-linked_resources", args=[self.dataset.id])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        response = self.client.patch(url)
        self.assertEqual(response.status_code, 403)

        response = self.client.put(url)
        self.assertEqual(response.status_code, 403)

    def test_insert_one_linked_resource(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        self.client.force_login(get_user_model().objects.get(username="admin"))

        response = self.client.post(url, data={"target": [self.map.id]}, content_type="application/json")

        link_connected = LinkedResource.objects.get(source_id=self.doc.id)

        self.assertEqual(response.status_code, 200)

        response_json = response.json()

        self.assertTrue((self.map.id in response_json["success"]))

        self.assertEqual(self.doc.id, link_connected.source_id)

        self.assertEqual(self.map.id, link_connected.target_id)

    def test_insert_linked_resource_invalid_type(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        self.client.force_login(get_user_model().objects.get(username="admin"))

        response = self.client.post(url, data={"target": self.map.id}, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_insert_self_as_linked_resource(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        # linked resource cannot be linked to itself
        response = self.client.post(url, data={"target": [self.doc.id]}, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertTrue((self.doc.id in response_json["error"]))

    def test_insert_bad_payload_linked_resource(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        # linked resource cannot have an invalid payload
        response = self.client.post(url, data={"target_XXX": [self.doc.id]})

        self.assertEqual(response.status_code, 400)

    def test_insert_existing_linked_resource(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])
        self.client.force_login(get_user_model().objects.get(username="admin"))
        LinkedResource.objects.create(source_id=self.doc.id, target_id=self.doc.id)

        # linked resource cannot be duplicated
        response = self.client.post(url, data={"target": [self.doc.id]}, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertTrue((self.doc.id in response_json["error"]))

    def test_insert_multiple_linked_resource(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        self.client.force_login(get_user_model().objects.get(username="admin"))

        response = self.client.post(
            url, data={"target": [self.map.id, self.dataset.id]}, content_type="application/json"
        )

        list_connected = LinkedResource.objects.filter(source_id=self.doc.id).all()

        list_connected_targets = [linked.target_id for linked in list_connected]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, len(list_connected))
        response_json = response.json()
        self.assertTrue((self.map.id in response_json["success"]))
        self.assertTrue((self.dataset.id in response_json["success"]))
        self.assertEqual(2, len(response_json["success"]))

        self.assertTrue((self.map.id in list_connected_targets))
        self.assertTrue((self.dataset.id in list_connected_targets))

    def test_insert_invalid_linked_resource(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        self.client.force_login(get_user_model().objects.get(username="admin"))

        # generate an invalid id
        invalid_id = ResourceBase.objects.last().id + 1

        # make sure id does not exist
        invalid_resource = ResourceBase.objects.filter(id=invalid_id).first()
        self.assertEqual(None, invalid_resource)

        response = self.client.post(url, data={"target": [invalid_id]}, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertTrue((invalid_id in response_json["error"]))

    def test_insert_valid_and_invalid_linked_resource(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        self.client.force_login(get_user_model().objects.get(username="admin"))

        # generate an invalid id
        invalid_id = ResourceBase.objects.last().id + 1

        # make sure id does not exist
        invalid_resource = ResourceBase.objects.filter(id=invalid_id).first()
        self.assertEqual(None, invalid_resource)

        response = self.client.post(url, data={"target": [invalid_id, self.map.id]}, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertTrue((invalid_id in response_json["error"]))
        self.assertTrue((self.map.id in response_json["success"]))

    def test_delete_invalid_linked_resource(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        self.client.force_login(get_user_model().objects.get(username="admin"))

        # generate an invalid id
        invalid_id = ResourceBase.objects.last().id + 1

        # make sure id does not exist
        invalid_resource = ResourceBase.objects.filter(id=invalid_id).first()
        self.assertEqual(None, invalid_resource)

        response = self.client.delete(url, data={"target": [invalid_id]}, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertTrue((invalid_id in response_json["error"]))

    def test_delete_linked_resource(self):
        url = reverse("base-resources-linked_resources", args=[self.doc.id])

        self.client.force_login(get_user_model().objects.get(username="admin"))

        LinkedResource.objects.create(source_id=self.doc.id, target_id=self.map.id)

        list_connected = LinkedResource.objects.filter(source_id=self.doc.id).all()
        # check count after insertion
        self.assertEqual(1, len(list_connected))

        response = self.client.delete(url, data={"target": [self.map.id]}, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 200)
        # check count after deletion
        self.assertEqual(0, len(LinkedResource.objects.filter(source_id=self.doc.id).all()))
        self.assertTrue((self.map.id in response_json["success"]))

    def test_delete_not_found_from_linked_resource(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        url = reverse("base-resources-linked_resources", args=[self.doc.id])
        # Make sure there are no linked resource
        linked_res = LinkedResource.objects.filter(source_id=self.doc.id).all()
        for link in linked_res:
            link.delete()

        # try deleting a valid resource but not found in linked res

        response = self.client.delete(url, data={"target": [self.map.id]}, content_type="application/json")
        response_json = response.json()
        self.assertEqual(response.status_code, 400)
        self.assertTrue((self.map.id in response_json["error"]))

    def test_linked_resource_for_document(self):
        _d = []
        try:
            # data preparation
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.map.id))
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.dataset.id))

            # call the API
            url = reverse("base-resources-linked_resources", args=[self.doc.id])
            response = self.client.get(url)

            # validation
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assert_linkedres_size(payload, "linked_to", 2)
            self.assert_linkedres_contains(
                payload,
                "linked_to",
                ({"pk": self.map.id, "title": self.map.title}, {"pk": self.dataset.id, "title": self.dataset.title}),
            )
            self.assert_linkedres_size(payload, "linked_by", 0)
        finally:
            for d in _d:
                d.delete()

    def assert_linkedres_size(self, payload, element: str, expected_size: int):
        self.assertEqual(
            expected_size,
            len(payload[element]),
            f"Mismatching payload size of '{element}': exp:{expected_size} found:{payload[element]}",
        )

    def assert_linkedres_contains(self, payload, element: str, expected_elements: Iterable):
        res_list = payload[element]
        for dikt in expected_elements:
            found = False
            for res in res_list:
                try:
                    if dikt.items() <= res.items():
                        found = True
                        break
                except AttributeError:
                    self.fail(f"\nError while comparing \n EXPECTED: {dikt}\n FOUND: {res}")

            if not found:
                self.fail(f"Elements {dikt} could not be found in output: {payload}")

    def test_linked_resource_for_maps_mixed(self):
        _d = []
        try:
            # data preparation
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.map.id))
            _d.append(
                MapLayer.objects.create(
                    map=self.map,
                    dataset=self.dataset,
                    name=self.dataset.name,
                    current_style="test_style",
                    ows_url="https://maps.geosolutionsgroup.com/geoserver/wms",
                )
            )

            # call the API
            url = reverse("base-resources-linked_resources", args=[self.map.id])
            response = self.client.get(url)

            # validation
            self.assertEqual(response.status_code, 200)

            payload = response.json()
            self.assert_linkedres_size(payload, "linked_to", 1)
            self.assert_linkedres_contains(
                payload, "linked_to", ({"pk": self.dataset.id, "title": self.dataset.title},)
            )
            self.assert_linkedres_size(payload, "linked_by", 1)
            self.assert_linkedres_contains(payload, "linked_by", ({"pk": self.doc.id, "title": self.doc.title},))

        finally:
            for d in _d:
                d.delete()

    def test_linked_resources_for_maps(self):
        _m = None
        try:
            # data preparation
            _m = MapLayer.objects.create(
                map=self.map,
                dataset=self.dataset,
                name=self.dataset.name,
                current_style="test_style",
                ows_url="https://maps.geosolutionsgroup.com/geoserver/wms",
            )

            # call the API
            url = reverse("base-resources-linked_resources", args=[self.map.id])
            response = self.client.get(url)

            # validation
            self.assertEqual(response.status_code, 200)

            payload = response.json()
            self.assert_linkedres_size(payload, "linked_to", 1)
            self.assert_linkedres_contains(
                payload, "linked_to", ({"pk": self.dataset.id, "title": self.dataset.title},)
            )
            self.assert_linkedres_size(payload, "linked_by", 0)

        finally:
            if _m:
                _m.delete()

    def test_linked_resource_for_dataset(self):
        _m = None
        try:
            # data preparation
            _m = MapLayer.objects.create(
                map=self.map,
                dataset=self.dataset,
                name=self.dataset.name,
                current_style="test_style",
                ows_url="https://maps.geosolutionsgroup.com/geoserver/wms",
            )

            # call the API
            url = reverse("base-resources-linked_resources", args=[self.dataset.id])
            response = self.client.get(url)

            # validation
            self.assertEqual(response.status_code, 200)

            payload = response.json()
            self.assert_linkedres_size(payload, "linked_to", 0)
            self.assert_linkedres_size(payload, "linked_by", 1)
            self.assert_linkedres_contains(payload, "linked_by", ({"pk": self.map.id, "title": self.map.title},))

        finally:
            if _m:
                _m.delete()

    def test_linked_resource_for_datasets_mixed(self):
        _d = []
        try:
            # data preparation
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.dataset.id))
            _d.append(
                MapLayer.objects.create(
                    map=self.map,
                    dataset=self.dataset,
                    name=self.dataset.name,
                    current_style="test_style",
                    ows_url="https://maps.geosolutionsgroup.com/geoserver/wms",
                )
            )

            # call the API
            url = reverse("base-resources-linked_resources", args=[self.dataset.id])
            response = self.client.get(url)

            # validation
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assert_linkedres_size(payload, "linked_to", 0)
            self.assert_linkedres_size(payload, "linked_by", 2)
            self.assert_linkedres_contains(
                payload,
                "linked_by",
                (
                    {"pk": self.map.id, "title": self.map.title},
                    {"pk": self.doc.id, "title": self.doc.title},
                ),
            )

        finally:
            for d in _d:
                d.delete()

    def test_linked_resource_deprecated_pagination(self):
        _d = []
        try:
            # data preparation
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.dataset.id))
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.map.id))

            # call the API w/ pagination
            url = reverse("base-resources-linked_resources", args=[self.doc.id])
            url = f"{url}?page_size=1"
            response = self.client.get(url)

            # validation
            self.assertEqual(response.status_code, 200)
            payload = response.json()

            self.assertIn("WARNINGS", payload, f"Missing WARNINGS element for URL {url}")
            self.assertIn("PAGINATION", payload["WARNINGS"], "Missing PAGINATION element")

            # call the API w/o pagination
            url = reverse("base-resources-linked_resources", args=[self.doc.id])
            response = self.client.get(url)

            # validation
            self.assertEqual(response.status_code, 200)
            payload = response.json()

            self.assertNotIn("WARNINGS", payload, "Missing WARNINGS element")

        finally:
            for d in _d:
                d.delete()

    def test_linked_resource_filter_one_resource_type(self):
        _d = []
        try:
            # data preparation
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.dataset.id))
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.map.id))
            resource_type_param = "dataset"
            # call api with single resource_type param
            url = reverse("base-resources-linked_resources", args=[self.doc.id])
            response = self.client.get(f"{url}?resource_type={resource_type_param}")

            # validation
            self.assertEqual(response.status_code, 200)
            payload = response.json()

            res_types_orig = resource_type_param.split(",")
            res_types_payload = [res["resource_type"] for res in payload["linked_to"]]
            for r in res_types_payload:
                self.assertTrue(r in res_types_orig)

        finally:
            for d in _d:
                d.delete()

    def test_linked_resource_filter_multiple_resource_type_linktype(self):
        _d = []
        try:
            # data preparation
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.dataset.id))
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.map.id))
            resource_type_param = "map"
            link_type = "linked_to"
            # call the API w/ both parameters
            url = reverse("base-resources-linked_resources", args=[self.doc.id])
            response = self.client.get(f"{url}?resource_type={resource_type_param}&link_type={link_type}")

            # validation
            self.assertEqual(response.status_code, 200)
            payload = response.json()

            res_types_orig = resource_type_param.split(",")
            res_types_payload = [res["resource_type"] for res in payload["linked_to"]]
            for type in res_types_payload:
                self.assertTrue(type in res_types_orig)
            self.assertSetEqual({"linked_to"}, set(payload.keys()))

        finally:
            for d in _d:
                d.delete()

    def test_linked_resource_filter_multiple_resource_type_without_linktype(self):
        _d = []
        try:
            # data preparation
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.dataset.id))
            _d.append(LinkedResource.objects.create(source_id=self.doc.id, target_id=self.map.id))
            resource_type_param = "dataset,map"
            # call the API w/ resource_type
            url = reverse("base-resources-linked_resources", args=[self.doc.id])
            response = self.client.get(f"{url}?resource_type={resource_type_param}")

            # validation
            self.assertEqual(response.status_code, 200)
            payload = response.json()

            res_types_orig = resource_type_param.split(",")
            res_types_payload = [res["resource_type"] for res in payload["linked_to"]]
            for type in res_types_payload:
                self.assertTrue(type in res_types_orig)
            payload_keys = {"linked_by", "linked_to"}
            self.assertSetEqual(payload_keys, set(payload.keys()))

        finally:
            for d in _d:
                d.delete()


class TestApiAdditionalBBoxCalculation(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dataset = create_single_dataset("single_layer")
        cls.map = create_single_map("single_map")
        cls.doc = create_single_doc("single_doc")
        cls.geoapp = create_single_geoapp("single_geoapp")
        cls.bbox = {"extent": {"coords": [6847623, 4776382, 7002886, 4878813], "srid": "EPSG:6875"}}

    def setUp(self):
        self.admin = get_user_model().objects.get(username="admin")

    def test_dataset_should_not_update_bbox(self):
        self.client.force_login(self.admin)
        url = reverse("base-resources-detail", kwargs={"pk": self.dataset.get_self_resource().pk})
        response = self.client.patch(
            url,
            data=json.dumps({"extent": {"coords": [6847623, 4776382, 7002886, 4878813], "srid": "EPSG:6875"}}),
            content_type="application/json",
        )

        llbbox = self.dataset.ll_bbox_polygon
        srid = self.dataset.srid

        self.assertEqual(200, response.status_code)
        self.dataset.refresh_from_db()
        self.assertEqual(self.dataset.ll_bbox_polygon, llbbox)
        self.assertEqual(self.dataset.srid, srid)

    def test_map_should_not_update_bbox(self):
        self.client.force_login(self.admin)
        url = reverse("base-resources-detail", kwargs={"pk": self.map.get_self_resource().pk})
        response = self.client.patch(
            url,
            data=json.dumps({"extent": {"coords": [6847623, 4776382, 7002886, 4878813], "srid": "EPSG:6875"}}),
            content_type="application/json",
        )

        llbbox = self.map.ll_bbox_polygon
        srid = self.map.srid

        self.assertEqual(200, response.status_code)
        self.map.refresh_from_db()
        self.assertEqual(self.map.ll_bbox_polygon, llbbox)
        self.assertEqual(self.map.srid, srid)

    def test_document_should_update_bbox(self):
        self.client.force_login(self.admin)
        url = reverse("base-resources-detail", kwargs={"pk": self.doc.get_self_resource().pk})
        response = self.client.patch(
            url,
            data=json.dumps({"extent": {"coords": [6847623, 4776382, 7002886, 4878813], "srid": "EPSG:6875"}}),
            content_type="application/json",
        )

        self.assertEqual(200, response.status_code)
        self.doc.refresh_from_db()
        expected = {
            "coords": [10.094299016880456, 43.172169804633185, 12.036103612263465, 44.11087068031093],
            "srid": "EPSG:4326",
        }
        resp = response.json()["resource"].get("extent")
        self.assertEqual(resp, expected)
        self.assertEqual("EPSG:6875", self.doc.srid)
        expected = "POLYGON ((10.094299016880456 43.172169804633185, 10.094299016880456 44.11087068031093, 12.036103612263465 44.11087068031093, 12.036103612263465 43.172169804633185, 10.094299016880456 43.172169804633185))"  # noqa
        self.assertEqual(self.doc.ll_bbox_polygon.wkt, expected)

    def test_geoapp_should_update_bbox(self):
        self.client.force_login(self.admin)
        url = reverse("base-resources-detail", kwargs={"pk": self.geoapp.get_self_resource().pk})
        response = self.client.patch(
            url,
            data=json.dumps({"extent": {"coords": [6847623, 4776382, 7002886, 4878813], "srid": "EPSG:6875"}}),
            content_type="application/json",
        )

        self.assertEqual(200, response.status_code)
        self.geoapp.refresh_from_db()
        expected = {
            "coords": [10.094299016880456, 43.172169804633185, 12.036103612263465, 44.11087068031093],
            "srid": "EPSG:4326",
        }
        resp = response.json()["resource"].get("extent")
        self.assertEqual(resp, expected)
        expected = "POLYGON ((10.094299016880456 43.172169804633185, 10.094299016880456 44.11087068031093, 12.036103612263465 44.11087068031093, 12.036103612263465 43.172169804633185, 10.094299016880456 43.172169804633185))"  # noqa
        self.assertEqual(self.geoapp.ll_bbox_polygon.wkt, expected)
        self.assertEqual("EPSG:6875", self.geoapp.srid)

    def test_geoapp_send_invalid_bbox_should_raise_error(self):
        self.client.force_login(self.admin)
        url = reverse("base-resources-detail", kwargs={"pk": self.geoapp.get_self_resource().pk})
        response = self.client.patch(
            url,
            data=json.dumps({"extent": {"coords": [6847623, 4776382, 7002886], "srid": "EPSG:6875"}}),
            content_type="application/json",
        )

        self.assertEqual(500, response.status_code)
        expected = {
            "success": False,
            "errors": ["The standard bbox provided is invalid"],
            "code": "invalid_resource_exception",
        }
        self.assertDictEqual(expected, response.json())


pycsw_settings_all = settings.PYCSW.copy()

pycsw_settings_all["FILTER"] = {"resource_type__in": ["dataset", "resourcebase"]}


class TestBaseResourceBase(GeoNodeBaseTestSupport):

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = get_user_model().objects.get(username="admin")

    def test_simple_resourcebase_can_be_created_by_resourcemanager(self):
        self.maxDiff = None
        resource = resource_manager.create(
            str(uuid4()), resource_type=ResourceBase, defaults={"title": "simple resourcebase", "owner": self.user}
        )

        self.assertIsNotNone(resource)
        # minimum resource checks
        self.assertEqual("resourcebase", resource.resource_type)
        self.assertTrue(resource.link_set.all().exists())
        self.assertEqual("simple resourcebase", resource.title)
        self.assertTrue(self.user == resource.owner)
        # check if the perms are set
        anonymous_group = Group.objects.get(name="anonymous")
        perms_expected = {
            "users": {
                self.user: set(
                    [
                        "delete_resourcebase",
                        "publish_resourcebase",
                        "change_resourcebase_permissions",
                        "view_resourcebase",
                        "change_resourcebase_metadata",
                        "change_resourcebase",
                    ]
                )
            },
            "groups": {anonymous_group: set(["view_resourcebase"])},
        }

        actual_perms = resource.get_all_level_info().copy()
        self.assertIsNotNone(actual_perms)
        self.assertTrue(self.user in actual_perms["users"].keys())
        self.assertTrue(anonymous_group in actual_perms["groups"].keys())
        self.assertSetEqual(perms_expected["users"][self.user], set(actual_perms["users"][self.user]))
        self.assertSetEqual(perms_expected["groups"][anonymous_group], set(actual_perms["groups"][anonymous_group]))

        # check if is returned from the API

        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get(reverse("base-resources-list"))

        self.assertTrue(resource.pk in [int(x["pk"]) for x in response.json()["resources"]])

        # checking csw call
        catalogue_post_save(instance=resource, sender=resource.__class__)
        # get all records
        csw = get_catalogue()
        record = csw.get_record(resource.uuid)
        self.assertIsNotNone(record)
        self.assertEqual(record.identification[0].title, resource.title)

    def test_csw_should_not_return_resourcebase_by_default(self):
        resource = resource_manager.create(
            str(uuid4()), resource_type=ResourceBase, defaults={"title": "simple resourcebase", "owner": self.user}
        )
        dt = resource_manager.create(
            str(uuid4()), resource_type=Dataset, defaults={"title": "simple dataset", "owner": self.user}
        )

        self.assertTrue(ResourceBase.objects.filter(pk=resource.pk).exists())
        self.assertTrue(ResourceBase.objects.filter(pk=dt.pk).exists())

        request = self.__csw_request_factory()

        response = csw_global_dispatch(request)
        root = etree.fromstring(response.content)
        child = [x.attrib for x in root if "numberOfRecordsMatched" in x.attrib]
        returned_results = ast.literal_eval(child[0].get("numberOfRecordsMatched", "0")) if child else 0
        self.assertEqual(1, returned_results)

    @override_settings(PYCSW=pycsw_settings_all)
    def test_csw_should_return_resourcebase_if_defined_in_settings(self):
        resource = resource_manager.create(
            str(uuid4()), resource_type=ResourceBase, defaults={"title": "simple resourcebase", "owner": self.user}
        )
        dt = resource_manager.create(
            str(uuid4()), resource_type=Dataset, defaults={"title": "simple dataset", "owner": self.user}
        )

        self.assertTrue(ResourceBase.objects.filter(pk=resource.pk).exists())
        self.assertTrue(ResourceBase.objects.filter(pk=dt.pk).exists())

        request = self.__csw_request_factory()

        response = csw_global_dispatch(request)
        root = etree.fromstring(response.content)
        child = [x.attrib for x in root if "numberOfRecordsMatched" in x.attrib]
        returned_results = ast.literal_eval(child[0].get("numberOfRecordsMatched", "0")) if child else 0
        self.assertEqual(2, returned_results)

    @staticmethod
    def __csw_request_factory():
        from django.contrib.auth.models import AnonymousUser

        factory = RequestFactory()
        url = "http://localhost:8000/catalogue/csw?request=GetRecords"
        url += "&service=CSW&version=2.0.2&outputschema=http%3A%2F%2Fwww.isotc211.org%2F2005%2Fgmd"
        url += "&elementsetname=brief&typenames=csw:Record&resultType=results"
        request = factory.get(url)

        request.user = AnonymousUser()
        return request
