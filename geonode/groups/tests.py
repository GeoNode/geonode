import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.conf import settings

from guardian.shortcuts import get_anonymous_user

from geonode.groups.models import GroupProfile, GroupInvitation
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.base.populate_test_data import create_models
from geonode.security.views import _perms_info_json


class SmokeTest(TestCase):
    """
    Basic checks to make sure pages load, etc.
    """

    fixtures = ["group_test_data"]

    def setUp(self):
        create_models(type='layer')
        create_models(type='map')
        create_models(type='document')
        self.norman = get_user_model().objects.get(username="norman")
        self.norman.groups.add(Group.objects.get(name='anonymous'))
        self.test_user = get_user_model().objects.get(username='test_user')
        self.test_user.groups.add(Group.objects.get(name='anonymous'))
        self.bar = GroupProfile.objects.get(slug='bar')
        self.anonymous_user = get_anonymous_user()

    def test_group_permissions_extend_to_user(self):
        """
        Ensures that when a user is in a group, the group permissions
        extend to the user.
        """

        layer = Layer.objects.all()[0]
        # Set the default permissions
        layer.set_default_permissions()

        # Test that the anonymous user can read
        self.assertTrue(self.anonymous_user.has_perm('view_resourcebase', layer.get_self_resource()))

        # Test that the default perms give Norman view permissions but not
        # write permissions
        self.assertTrue(self.norman.has_perm('view_resourcebase', layer.get_self_resource()))
        self.assertFalse(self.norman.has_perm('change_resourcebase', layer.get_self_resource()))

        # Make sure Norman is not in the bar group.
        self.assertFalse(self.bar.user_is_member(self.norman))

        # Add norman to the bar group.
        self.bar.join(self.norman)

        # Ensure Norman is in the bar group.
        self.assertTrue(self.bar.user_is_member(self.norman))

        # Give the bar group permissions to change the layer.
        permissions = {'groups': {'bar': ['view_resourcebase', 'change_resourcebase']}}
        layer.set_permissions(permissions)

        self.assertTrue(self.norman.has_perm('view_resourcebase', layer.get_self_resource()))
        # check that now norman can change the layer
        self.assertTrue(self.norman.has_perm('change_resourcebase', layer.get_self_resource()))

        # Test adding a new user to the group after setting permissions on the layer.
        # Make sure Test User is not in the bar group.
        self.assertFalse(self.bar.user_is_member(self.test_user))

        self.assertFalse(self.test_user.has_perm('change_resourcebase', layer.get_self_resource()))

        self.bar.join(self.test_user)

        self.assertTrue(self.test_user.has_perm('change_resourcebase', layer.get_self_resource()))

    def test_group_resource(self):
        """
        Tests the resources method on a Group object.
        """

        layer = Layer.objects.all()[0]
        map = Map.objects.all()[0]

        perm_spec = {'groups': {'bar': ['change_resourcebase']}}
        # Give the self.bar group write perms on the layer
        layer.set_permissions(perm_spec)
        map.set_permissions(perm_spec)

        # Ensure the layer is returned in the group's resources
        self.assertTrue(layer.get_self_resource() in self.bar.resources())
        self.assertTrue(map.get_self_resource() in self.bar.resources())

        # Test the resource filter
        self.assertTrue(layer.get_self_resource() in self.bar.resources(resource_type='layer'))
        self.assertTrue(map.get_self_resource() not in self.bar.resources(resource_type='layer'))

        # Revoke permissions on the layer from the self.bar group
        layer.set_permissions("{}")

        # Ensure the layer is no longer returned in the groups resources
        self.assertFalse(layer.get_self_resource() in self.bar.resources())

    def test_perms_info(self):
        """
        Tests the perms_info function (which passes permissions to the response context).
        """
        # Add test to test perms being sent to the front end.
        layer = Layer.objects.all()[0]
        layer.set_default_permissions()
        perms_info = layer.get_all_level_info()

        # Ensure there is only one group 'anonymous' by default
        self.assertEqual(len(perms_info['groups'].keys()), 1)

        # Add the foo group to the layer object groups
        layer.set_permissions({'groups': {'bar': ['view_resourcebase']}})

        perms_info = _perms_info_json(layer)
        # Ensure foo is in the perms_info output
        self.assertDictEqual(json.loads(perms_info)['groups'], {'bar': ['view_resourcebase']})

    def test_resource_permissions(self):
        """
        Tests that the client can get and set group permissions through the test_resource_permissions view.
        """

        self.assertTrue(self.client.login(username="admin", password="admin"))

        layer = Layer.objects.all()[0]
        document = Document.objects.all()[0]
        map_obj = Map.objects.all()[0]
        layer.set_default_permissions()
        document.set_default_permissions()
        map_obj.set_default_permissions()

        objects = layer, document, map_obj

        for obj in objects:
            response = self.client.get(reverse('resource_permissions', kwargs=dict(resource_id=obj.id)))
            self.assertEqual(response.status_code, 200)
            js = json.loads(response.content)
            permissions = js.get('permissions', dict())

            if isinstance(permissions, unicode) or isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Ensure the groups value is empty by default
            expected_permissions = {}
            if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
                expected_permissions.setdefault(u'anonymous', []).append(u'download_resourcebase')
            if settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION:
                expected_permissions.setdefault(u'anonymous', []).append(u'view_resourcebase')

            self.assertDictEqual(permissions.get('groups'), expected_permissions)

            permissions = {
                'groups': {
                    'bar': ['change_resourcebase']
                },
                'users': {
                    'admin': ['change_resourcebase']
                }
            }

            # Give the bar group permissions
            response = self.client.post(
                reverse(
                    'resource_permissions',
                    kwargs=dict(resource_id=obj.id)),
                data=json.dumps(permissions),
                content_type="application/json")

            self.assertEqual(response.status_code, 200)

            response = self.client.get(reverse('resource_permissions', kwargs=dict(resource_id=obj.id)))

            js = json.loads(response.content)
            permissions = js.get('permissions', dict())

            if isinstance(permissions, unicode) or isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Make sure the bar group now has write permissions
            self.assertDictEqual(permissions['groups'], {'bar': ['change_resourcebase']})

            # Remove group permissions
            permissions = {"users": {"admin": ['change_resourcebase']}}

            # Update the object's permissions to remove the bar group
            response = self.client.post(
                reverse(
                    'resource_permissions',
                    kwargs=dict(resource_id=obj.id)),
                data=json.dumps(permissions),
                content_type="application/json")

            self.assertEqual(response.status_code, 200)

            response = self.client.get(reverse('resource_permissions', kwargs=dict(resource_id=obj.id)))

            js = json.loads(response.content)
            permissions = js.get('permissions', dict())

            if isinstance(permissions, unicode) or isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Assert the bar group no longer has permissions
            self.assertDictEqual(permissions['groups'], {})

    def test_create_new_group(self):
        """
        Tests creating a group through the group_create route.
        """

        d = dict(title='TestGroup',
                 description='This is a test group.',
                 access='public',
                 keywords='testing, groups')

        self.client.login(username="admin", password="admin")
        response = self.client.post(reverse('group_create'), data=d)
        # successful POSTS will redirect to the group's detail view.
        self.assertEqual(response.status_code, 302)
        self.assertTrue(GroupProfile.objects.get(title='TestGroup'))

    def test_delete_group_view(self):
        """
        Tests deleting a group through the group_delete route.
        """

        # Ensure the group exists
        self.assertTrue(GroupProfile.objects.get(id=self.bar.id))

        self.client.login(username="admin", password="admin")

        # Delete the group
        response = self.client.post(reverse('group_remove', args=[self.bar.slug]))

        # successful POSTS will redirect to the group list view.
        self.assertEqual(response.status_code, 302)
        self.assertFalse(GroupProfile.objects.filter(id=self.bar.id).count() > 0)

    def test_delete_group_view_no_perms(self):
        """
        Tests deleting a group through the group_delete with a non-manager.
        """

        # Ensure the group exists
        self.assertTrue(GroupProfile.objects.get(id=self.bar.id))

        self.client.login(username="norman", password="norman")

        # Delete the group
        response = self.client.post(reverse('group_remove', args=[self.bar.slug]))

        self.assertEqual(response.status_code, 403)

        # Ensure the group still exists
        self.assertTrue(GroupProfile.objects.get(id=self.bar.id))

    def test_groupmember_manager(self):
        """
        Tests the get_managers method.
        """
        norman = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username='admin')

        # Make sure norman is not a user
        self.assertFalse(self.bar.user_is_member(norman))

        # Add norman to the self.bar group
        self.bar.join(norman)

        # Ensure norman is now a member
        self.assertTrue(self.bar.user_is_member(norman))

        # Ensure norman is not in the managers queryset
        self.assertTrue(norman not in self.bar.get_managers())

        # Ensure admin is in the managers queryset
        self.assertTrue(admin in self.bar.get_managers())

    def test_public_pages_render(self):
        """
        Verify pages that do not require login load without internal error
        """

        response = self.client.get("/groups/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/groups/group/bar/")
        self.assertEqual(200, response.status_code)

        response = self.client.get("/groups/group/bar/members/")
        self.assertEqual(200, response.status_code)

        # 302 for auth failure since we redirect to login page
        response = self.client.get("/groups/create/")
        self.assertEqual(302, response.status_code)

        response = self.client.get("/groups/group/bar/update/")
        self.assertEqual(302, response.status_code)

        # 405 - json endpoint, doesn't support GET
        response = self.client.get("/groups/group/bar/invite/")
        self.assertEqual(405, response.status_code)

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

        # 405 - json endpoint, doesn't support GET
        response = self.client.get("/groups/group/bar/invite/")
        self.assertEqual(405, response.status_code)


class MembershipTest(TestCase):
    """
    Tests membership logic in the geonode.groups models
    """

    fixtures = ["group_test_data"]

    def test_group_is_member(self):
        """
        Tests checking group membership
        """

        anon = get_anonymous_user()
        normal = get_user_model().objects.get(username="norman")
        group = GroupProfile.objects.get(slug="bar")

        self.assert_(not group.user_is_member(anon))
        self.assert_(not group.user_is_member(normal))

    def test_group_add_member(self):
        """
        Tests adding a user to a group
        """

        anon = get_anonymous_user()
        normal = get_user_model().objects.get(username="norman")
        group = GroupProfile.objects.get(slug="bar")
        group.join(normal)
        self.assert_(group.user_is_member(normal))
        self.assertRaises(ValueError, lambda: group.join(anon))


class InvitationTest(TestCase):
    """
    Tests invitation logic in geonode.groups models
    """

    fixtures = ["group_test_data"]

    def test_invite_user(self):
        """
        Tests inviting a registered user
        """

        normal = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")
        group = GroupProfile.objects.get(slug="bar")
        group.invite(normal, admin, role="member", send=False)

        self.assert_(GroupInvitation.objects.filter(user=normal, from_user=admin, group=group).exists())

        invite = GroupInvitation.objects.get(user=normal, from_user=admin, group=group)

        # Test that the user can access the token url.
        self.client.login(username="norman", password="norman")
        response = self.client.get("/groups/group/{group}/invite/{token}/".format(group=group, token=invite.token))
        self.assertEqual(200, response.status_code)

    def test_accept_invitation(self):
        """
        Tests accepting an invitation
        """

        anon = get_anonymous_user()
        normal = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")
        group = GroupProfile.objects.get(slug="bar")
        group.invite(normal, admin, role="member", send=False)

        invitation = GroupInvitation.objects.get(user=normal, from_user=admin, group=group)

        self.assertRaises(ValueError, lambda: invitation.accept(anon))
        self.assertRaises(ValueError, lambda: invitation.accept(admin))
        invitation.accept(normal)

        self.assert_(group.user_is_member(normal))
        self.assert_(invitation.state == "accepted")

    def test_decline_invitation(self):
        """
        Tests declining an invitation
        """

        anon = get_anonymous_user()
        normal = get_user_model().objects.get(username="norman")
        admin = get_user_model().objects.get(username="admin")
        group = GroupProfile.objects.get(slug="bar")
        group.invite(normal, admin, role="member", send=False)

        invitation = GroupInvitation.objects.get(user=normal, from_user=admin, group=group)

        self.assertRaises(ValueError, lambda: invitation.decline(anon))
        self.assertRaises(ValueError, lambda: invitation.decline(admin))
        invitation.decline(normal)

        self.assert_(not group.user_is_member(normal))
        self.assert_(invitation.state == "declined")
