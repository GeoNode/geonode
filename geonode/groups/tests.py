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
import json
import logging

from django.urls import reverse
from django.conf import settings
from django.test import override_settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.documents.models import Document
from guardian.shortcuts import get_anonymous_user
from geonode.security.views import _perms_info_json
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.groups.conf import settings as groups_settings

from geonode.groups.models import GroupProfile, GroupMember, GroupCategory

from geonode.base.populate_test_data import all_public, create_models, remove_models, create_single_dataset

logger = logging.getLogger(__name__)


def _log(msg, *args):
    logger.debug(msg, *args)


class GroupsSmokeTest(GeoNodeBaseTestSupport):
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

        self.norman = get_user_model().objects.get(username="norman")
        self.norman.groups.add(Group.objects.get(name="anonymous"))
        self.test_user = get_user_model().objects.get(username="test_user")
        self.test_user.groups.add(Group.objects.get(name="anonymous"))
        self.bar = GroupProfile.objects.get(slug="bar")
        self.anonymous_user = get_anonymous_user()

        c1 = GroupCategory.objects.create(name="test #1 category")
        g = GroupProfile.objects.create(slug="test", title="test")
        g.categories.add(c1)
        g.save()
        User = get_user_model()
        u = User.objects.create(username="test")
        u.set_password("test")
        u.save()

    """
    Basic checks to make sure pages load, etc.
    """

    def test_registered_group_exists(self):
        """
        Ensures that a default group and grouprofile 'registered-users' has been
        created at initialization time.
        """
        group = Group.objects.filter(name=groups_settings.REGISTERED_MEMBERS_GROUP_NAME).first()
        self.assertTrue(group)

    def test_users_group_list_view(self):
        """
        1. Ensures that a superuser can see the whole group list.

        2. Ensures that a user can see only public/public-invite groups.

        3. Ensures that a user belonging to a private group, can see it.
        """
        bobby = get_user_model().objects.get(username="bobby")

        public_group, _public_created = GroupProfile.objects.get_or_create(
            slug="public_group", title="public_group", access="public"
        )
        private_group, _private_created = GroupProfile.objects.get_or_create(
            slug="private_group", title="private_group", access="private"
        )

        private_group.join(bobby)
        data = {"query": "p", "page": 1, "pageSize": 9}

        # Anonymous
        """
            '{
                "users": [], "count": 0,
                "groups": [
                    {"name": "public_group", "title": "public_group"}]
            }'
        """
        response = self.client.post(reverse("account_ajax_lookup"), data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        logger.debug(f"Anonymous --> {content}")
        self.assertEqual(len(content["groups"]), 1)
        self.assertEqual(content["groups"][0]["name"], "public_group")
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "public_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "private_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 404)

        # Admin
        """
            '{
                "users": [], "count": 0,
                "groups": [
                    {"name": "public_group", "title": "public_group"},
                    {"name": "private_group", "title": "private_group"}]
            }'
        """
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(reverse("account_ajax_lookup"), data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        logger.debug(f"admin --> {content}")
        self.assertEqual(len(content["groups"]), 2)
        self.assertEqual(content["groups"][0]["name"], "public_group")
        self.assertEqual(content["groups"][1]["name"], "private_group")
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "public_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "private_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 200)

        # Bobby
        """
            '{
                "users": [], "count": 0,
                "groups": [
                    {"name": "public_group", "title": "public_group"},
                    {"name": "private_group", "title": "private_group"}]
            }'
        """
        self.assertTrue(self.client.login(username="bobby", password="bob"))
        response = self.client.post(reverse("account_ajax_lookup"), data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        logger.debug(f"bobby --> {content}")
        self.assertEqual(len(content["groups"]), 2)
        self.assertEqual(content["groups"][0]["name"], "public_group")
        self.assertEqual(content["groups"][1]["name"], "private_group")
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "public_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "private_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 200)

        # Norman
        """
            '{
                "users": [], "count": 0,
                "groups": [
                    {"name": "public_group", "title": "public_group"}]
            }'
        """
        self.assertTrue(self.client.login(username="norman", password="norman"))
        response = self.client.post(reverse("account_ajax_lookup"), data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        logger.debug(f"norman --> {content}")
        self.assertEqual(len(content["groups"]), 1)
        self.assertEqual(content["groups"][0]["name"], "public_group")
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "public_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 200)
        response = self.client.get(
            reverse(
                "group_detail",
                args=[
                    "private_group",
                ],
            )
        )
        self.assertEqual(response.status_code, 404)

        if _public_created:
            public_group.delete()
            self.assertFalse(GroupProfile.objects.filter(slug="public_group").exists())
        if _private_created:
            private_group.delete()
            self.assertFalse(GroupProfile.objects.filter(slug="private_group").exists())

    def test_group_permissions_extend_to_user(self):
        """
        Ensures that when a user is in a group, the group permissions
        extend to the user.
        """
        layer = Dataset.objects.first()
        # Set the default permissions
        layer.set_default_permissions()

        # Test that the anonymous user can read
        self.assertTrue(self.anonymous_user.has_perm("view_resourcebase", layer.get_self_resource()))

        # Test that the default perms give Norman view permissions but not
        # write permissions
        self.assertTrue(self.norman.has_perm("view_resourcebase", layer.get_self_resource()))
        self.assertFalse(self.norman.has_perm("change_resourcebase", layer.get_self_resource()))

        # Make sure Norman is not in the bar group.
        self.assertFalse(self.bar.user_is_member(self.norman))

        # Add norman to the bar group.
        self.bar.join(self.norman)

        # Ensure Norman is in the bar group.
        self.assertTrue(self.bar.user_is_member(self.norman))

        # Give the bar group permissions to change the layer.
        permissions = {"groups": {"bar": ["view_resourcebase", "change_resourcebase"]}}
        layer.set_permissions(permissions)

        self.assertTrue(self.norman.has_perm("view_resourcebase", layer.get_self_resource()))
        # check that now norman can change the layer
        self.assertTrue(self.norman.has_perm("change_resourcebase", layer.get_self_resource()))

        # Test adding a new user to the group after setting permissions on the layer.
        # Make sure Test User is not in the bar group.
        self.assertFalse(self.bar.user_is_member(self.test_user))

        self.assertFalse(self.test_user.has_perm("change_resourcebase", layer.get_self_resource()))

        self.bar.join(self.test_user)

        self.assertTrue(self.test_user.has_perm("change_resourcebase", layer.get_self_resource()))

    def test_group_resource(self):
        """
        Tests the resources method on a Group object.
        """

        layer = Dataset.objects.first()
        map = Map.objects.first()

        perm_spec = {"groups": {"bar": ["change_resourcebase"]}}
        # Give the self.bar group write perms on the layer
        layer.set_permissions(perm_spec)
        map.set_permissions(perm_spec)

        # Ensure the layer is returned in the group's resources
        self.assertTrue(layer.get_self_resource() in self.bar.resources())
        self.assertTrue(map.get_self_resource() in self.bar.resources())

        # Test the resource filter
        self.assertTrue(layer.get_self_resource() in self.bar.resources(resource_type="dataset"))
        self.assertTrue(map.get_self_resource() not in self.bar.resources(resource_type="dataset"))

        # Revoke permissions on the layer from the self.bar group
        layer.set_permissions("{}")

        # Ensure the layer is no longer returned in the groups resources
        self.assertFalse(layer.get_self_resource() in self.bar.resources())

    def test_perms_info(self):
        """
        Tests the perms_info function (which passes permissions to the response context).
        """
        # Add test to test perms being sent to the front end.
        layer = Dataset.objects.first()
        layer.set_default_permissions()
        perms_info = layer.get_all_level_info()

        # Ensure there is only one group 'anonymous' by default
        self.assertEqual(len(perms_info["groups"].keys()), 1)

        # Add the foo group to the layer object groups
        layer.set_permissions({"groups": {"bar": ["view_resourcebase"]}})

        perms_info = _perms_info_json(layer)
        # Ensure foo is in the perms_info output
        self.assertCountEqual(json.loads(perms_info)["groups"], {"bar": ["view_resourcebase"]})

    def test_resource_permissions(self):
        """
        Tests that the client can get and set group permissions through the test_resource_permissions view.
        """

        self.assertTrue(self.client.login(username="admin", password="admin"))

        layer = Dataset.objects.first()
        document = Document.objects.first()
        map_obj = Map.objects.first()
        layer.set_default_permissions()
        document.set_default_permissions()
        map_obj.set_default_permissions()

        objects = layer, document, map_obj

        for obj in objects:
            response = self.client.get(reverse("resource_permissions", kwargs=dict(resource_id=obj.id)))
            self.assertEqual(response.status_code, 200)
            content = response.content
            if isinstance(content, bytes):
                content = content.decode("UTF-8")
            js = json.loads(content)
            permissions = js.get("permissions", dict())

            if isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Ensure the groups value is empty by default
            expected_permissions = {}
            if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
                expected_permissions.setdefault("anonymous", []).append("download_resourcebase")
            if settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION:
                expected_permissions.setdefault("anonymous", []).append("view_resourcebase")

            self.assertCountEqual(permissions.get("groups"), expected_permissions)

            permissions = {"groups": {"bar": ["change_resourcebase"]}, "users": {"admin": ["change_resourcebase"]}}

            # Give the bar group permissions
            response = self.client.post(
                reverse("resource_permissions", kwargs=dict(resource_id=obj.id)),
                data=json.dumps(permissions),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 200)

            response = self.client.get(reverse("resource_permissions", kwargs=dict(resource_id=obj.id)))

            content = response.content
            if isinstance(content, bytes):
                content = content.decode("UTF-8")
            js = json.loads(content)
            permissions = js.get("permissions", dict())

            if isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Make sure the bar group now has write permissions
            self.assertCountEqual(permissions["groups"], {"bar": ["change_resourcebase"]})

            # Remove group permissions
            permissions = {"users": {"admin": ["change_resourcebase"]}}

            # Update the object's permissions to remove the bar group
            response = self.client.post(
                reverse("resource_permissions", kwargs=dict(resource_id=obj.id)),
                data=json.dumps(permissions),
                content_type="application/json",
            )

            self.assertEqual(response.status_code, 200)

            response = self.client.get(reverse("resource_permissions", kwargs=dict(resource_id=obj.id)))

            content = response.content
            if isinstance(content, bytes):
                content = content.decode("UTF-8")
            js = json.loads(content)
            permissions = js.get("permissions", dict())

            if isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Assert the bar group no longer has permissions
            self.assertCountEqual(permissions["groups"], {})

    def test_create_new_group(self):
        """
        Tests creating a group through the group_create route.
        """

        d = dict(title="TestGroup", description="This is a test group.", access="public", keywords="testing, groups")

        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse("group_create"), data=d)
        # successful POSTS will redirect to the group's detail view.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(GroupProfile.objects.get(title="TestGroup"))

    def test_delete_group_view(self):
        """
        Tests deleting a group through the group_delete route.
        """

        # Ensure the group exists
        self.assertTrue(GroupProfile.objects.get(id=self.bar.id))

        self.client.login(username="admin", password="admin")

        # Delete the group
        response = self.client.post(reverse("group_remove", args=[self.bar.slug]))

        # successful POSTS will redirect to the group list view.
        self.assertEqual(response.status_code, 302)
        self.assertFalse(GroupProfile.objects.filter(id=self.bar.id).exists())

    def test_delete_group_view_no_perms(self):
        """
        Tests deleting a group through the group_delete with a non-manager.
        """

        # Ensure the group exists
        self.assertTrue(GroupProfile.objects.get(id=self.bar.id))

        self.client.login(username="norman", password="norman")

        # Delete the group
        response = self.client.post(reverse("group_remove", args=[self.bar.slug]))

        self.assertEqual(response.status_code, 403)

        # Ensure the group still exists
        self.assertTrue(GroupProfile.objects.get(id=self.bar.id))

    def test_groupmember_manager(self):
        """
        Tests the get_managers method.
        """
        norman = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")

        # Make sure norman is not a user
        self.assertFalse(self.bar.user_is_member(norman))

        # Add norman to the self.bar group
        self.bar.join(norman)

        # Ensure norman is now a member
        self.assertTrue(self.bar.user_is_member(norman))

        # Ensure norman is not in the managers queryset
        self.assertTrue(norman not in self.bar.get_managers())

        # Ensure admin is in the managers queryset
        self.bar.join(admin, role=GroupMember.MANAGER)
        self.assertTrue(admin in self.bar.get_managers())

    def test_public_pages_render(self):
        """
        Verify pages that do not require login load without internal error
        """

        response = self.client.get("/groups/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/groups/group/bar/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/groups/group/bar/members/")
        self.assertEqual(response.status_code, 200)

        # 302 for auth failure since we redirect to login page
        response = self.client.get("/groups/create/")
        self.assertTrue(response.status_code in (302, 403))

        response = self.client.get("/groups/group/bar/update/")
        self.assertEqual(response.status_code, 302)

        # # 405 - json endpoint, doesn't support GET
        # response = self.client.get("/groups/group/bar/invite/")
        # self.assertEqual(405, response.status_code)

    def test_protected_pages_render(self):
        """
        Verify pages that require login load without internal error
        """

        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get("/groups/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/groups/group/bar/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/groups/group/bar/members/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/groups/create/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/groups/group/bar/update/")
        self.assertEqual(200, response.status_code)

        # # 405 - json endpoint, doesn't support GET
        # response = self.client.get("/groups/group/bar/invite/")
        # self.assertEqual(405, response.status_code)

    """
    Tests membership logic in the geonode.groups models
    """

    def test_group_is_member(self):
        """
        Tests checking group membership
        """

        anon = get_anonymous_user()
        normal = get_user_model().objects.get(username="norman")
        group = GroupProfile.objects.get(slug="bar")

        self.assertFalse(group.user_is_member(anon))
        self.assertFalse(group.user_is_member(normal))

    def test_group_add_member(self):
        """
        Tests adding a user to a group
        """

        anon = get_anonymous_user()
        normal = get_user_model().objects.get(username="norman")
        group = GroupProfile.objects.get(slug="bar")
        group.join(normal)
        self.assertTrue(group.user_is_member(normal))
        self.assertRaises(ValueError, lambda: group.join(anon))

    def test_group_promote_demote_member(self):
        """
        Tests promoting a member to manager, demoting to member
        """

        normal = get_user_model().objects.get(username="norman")
        group = GroupProfile.objects.get(slug="bar")
        group.join(normal)
        self.assertFalse(group.user_is_role(normal, "manager"))
        GroupMember.objects.get(group=group, user=normal).promote()
        self.assertTrue(group.user_is_role(normal, "manager"))
        GroupMember.objects.get(group=group, user=normal).demote()
        self.assertFalse(group.user_is_role(normal, "manager"))

    def test_profile_is_member_of_group(self):
        """
        Tests profile is_member_of_group property
        """

        normal = get_user_model().objects.get(username="norman")
        group = GroupProfile.objects.get(slug="bar")
        self.assertFalse(normal.is_member_of_group(group.slug))

        group.join(normal)
        self.assertTrue(normal.is_member_of_group(group.slug))

    def test_group_remove_member(self):
        """
        Tests removing a user from a group
        """

        normal = get_user_model().objects.get(username="norman")
        group = GroupProfile.objects.get(slug="bar")
        group.join(normal)
        self.assertTrue(group.user_is_member(normal))
        group.leave(normal)
        self.assertFalse(group.user_is_member(normal))

    @override_settings(MEDIA_ROOT="/tmp/geonode_tests")
    def test_group_logo_is_present_on_list_view(self):
        """Verify that a group's logo is rendered on list view."""
        with self.settings(API_LOCKDOWN=False):
            test_profile, _ = GroupProfile.objects.update_or_create(
                slug="test",
                defaults=dict(
                    description="test", access="public", logo=SimpleUploadedFile("dummy-file.jpg", b"dummy contents")
                ),
            )

            response = self.client.get(
                reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "groups"})
            )
        content = response.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
            response_payload = json.loads(content)
            returned = response_payload["objects"]
            group_profile = [g["group_profile"] for g in returned if g["group_profile"]["title"] == test_profile.title][
                0
            ]
            self.assertEqual(200, response.status_code)
            self.assertEqual(group_profile["logo"], test_profile.logo.url)

    def test_group_logo_is_not_present_on_list_view(self):
        """
        Verify that no logo exists in list view when a group doesn't have one.
        """

        with self.settings(API_LOCKDOWN=False):
            test_profile, _ = GroupProfile.objects.update_or_create(
                slug="test", defaults=dict(title="test", description="test", access="public")
            )

            response = self.client.get(
                reverse("api_dispatch_list", kwargs={"api_name": "api", "resource_name": "groups"})
            )
        content = response.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
            response_payload = json.loads(content)
            returned = response_payload["objects"]
            group_profile = [g["group_profile"] for g in returned if g["group_profile"]["title"] == test_profile.title][
                0
            ]
            self.assertEqual(200, response.status_code)
            self.assertIsNone(group_profile["logo"])

    def test_group_activity_pages_render(self):
        """
        Verify Activity List pages
        """

        self.assertTrue(self.client.login(username="admin", password="admin"))

        response = self.client.get("/groups/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/groups/group/bar/activity/")
        self.assertEqual(200, response.status_code)

        self.assertContains(response, "Datasets", count=3, status_code=200, msg_prefix="", html=False)
        self.assertContains(response, "Maps", count=3, status_code=200, msg_prefix="", html=False)
        self.assertContains(response, "Documents", count=3, status_code=200, msg_prefix="", html=False)
        self.assertContains(
            response, '<a href="/datasets/:geonode:CA">CA</a>', count=0, status_code=200, msg_prefix="", html=False
        )
        self.assertContains(response, "uploaded", count=0, status_code=200, msg_prefix="", html=False)
        dataset = create_single_dataset("single_point.shp")
        try:
            # Add test to test perms being sent to the front end.
            dataset.set_default_permissions()
            perms_info = dataset.get_all_level_info()

            # Ensure there is only one group 'anonymous' by default
            self.assertEqual(len(perms_info["groups"].keys()), 1)

            # Add the foo group to the dataset object groups
            perms_info["groups"]["bar"] = ["view_resourcebase"]
            dataset.set_permissions(perms_info)

            perms_info = _perms_info_json(dataset)
            # Ensure foo is in the perms_info output
            self.assertCountEqual(json.loads(perms_info)["groups"]["bar"], ["view_resourcebase"])

            dataset.group = self.bar.group
            dataset.save()

            response = self.client.get("/groups/group/bar/activity/")
            self.assertEqual(200, response.status_code)
            _log(response)
            self.assertContains(
                response,
                f'<a href="{dataset.detail_url}">geonode:single_point.shp</a>',
                count=2,
                status_code=200,
                msg_prefix="",
                html=False,
            )
            self.assertContains(response, "uploaded", count=2, status_code=200, msg_prefix="", html=False)
        finally:
            dataset.set_default_permissions()
            dataset.group = None
            dataset.save()

    """
    Group Categories tests
    """

    def test_api(self):
        api_url = "/api/groupcategory/"

        self.client.login(username="test", password="test")  # login necessary because settings.API_LOCKDOWN=True
        r = self.client.get(api_url)
        self.assertEqual(r.status_code, 200)
        content = r.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        data = json.loads(content)
        self.assertEqual(data["meta"]["total_count"], GroupCategory.objects.all().count())

        # check if we have non-empty group category
        self.assertTrue(GroupCategory.objects.filter(groups__isnull=False).exists())

        for item in data["objects"]:
            self.assertTrue(GroupCategory.objects.filter(slug=item["slug"]).count() == 1)
            g = GroupCategory.objects.get(slug=item["slug"])
            self.assertEqual(item["member_count"], g.groups.all().count())

        self.client.logout()
        r = self.client.get(api_url)
        self.assertEqual(r.status_code, 200)
        content = r.content
        if isinstance(content, bytes):
            content = content.decode("UTF-8")
        data = json.loads(content)
        self.assertEqual(data["meta"]["total_count"], 1)

        # check if we have non-empty group category
        self.assertTrue(GroupCategory.objects.filter(groups__isnull=False).exists())

        for item in data["objects"]:
            self.assertTrue(GroupCategory.objects.filter(slug=item["slug"]).count() == 1)
            g = GroupCategory.objects.get(slug=item["slug"])
            self.assertEqual(item["member_count"], 1)

    def test_group_categories_list(self):
        view_url = reverse("group_category_list")
        r = self.client.get(view_url)
        self.assertEqual(r.status_code, 200)

    def test_group_categories_add(self):
        view_url = reverse("group_category_create")
        # Test that the view is protected to anonymous users
        r = self.client.get(view_url)
        self.assertTrue(r.status_code in (302, 403))

        # Test that the view is protected to non-admin users
        self.client.login(username="test", password="test")
        r = self.client.post(view_url)
        self.assertTrue(r.status_code in (401, 403))

        # Test that the view is accessible to administrators
        self.client.login(username="admin", password="admin")
        r = self.client.get(view_url)
        self.assertEqual(r.status_code, 200)

        # Create e new category
        category = "test #3 category"
        r = self.client.post(view_url, {"name": category})

        self.assertEqual(r.status_code, 302)
        q = GroupCategory.objects.filter(name=category)
        self.assertEqual(q.count(), 1)
        self.assertTrue(q.get().slug)
