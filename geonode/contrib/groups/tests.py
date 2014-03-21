import json
from django.contrib.auth import get_backends
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from geonode.contrib.groups.models import Group, GroupInvitation
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.layers.views import LAYER_LEV_NAMES
from geonode.maps.models import Map
from geonode.search.populate_search_test_data import create_models
from geonode.security.models import GroupObjectRoleMapping
from geonode.security.enumerations import ANONYMOUS_USERS, AUTHENTICATED_USERS
from geonode.security.views import _perms_info


class SmokeTest(TestCase):
    "Basic checks to make sure pages load, etc."

    fixtures = ["group_test_data"]

    def setUp(self):
        create_models(type='layer')
        create_models(type='map')
        create_models(type='document')
        self.norman = User.objects.get(username="norman")
        self.bar = Group.objects.get(slug='bar')

    def test_group_permissions_extend_to_user(self):
        """
        Ensures that when a user is in a group, the group permissions
        extend to the user.
        """

        layer = Layer.objects.all()[0]
        backend = get_backends()[0]
        # Set the default permissions
        layer.set_default_permissions()

        # Test that LEVEL_READ is set for ANONYMOUS_USERS and AUTHENTICATED_USERS
        self.assertEqual(layer.get_gen_level(ANONYMOUS_USERS), layer.LEVEL_READ)
        self.assertEqual(layer.get_gen_level(AUTHENTICATED_USERS), layer.LEVEL_READ)

        # Test that the default perms give Norman view permissions but not write permissions
        read_perms = backend.objects_with_perm(self.norman, 'layers.view_layer', Layer)
        write_perms = backend.objects_with_perm(self.norman, 'layers.change_layer', Layer)
        self.assertTrue(layer.id in read_perms)
        self.assertTrue(layer.id not in write_perms)

        # Make sure Norman is not in the bar group.
        self.assertFalse(self.bar.user_is_member(self.norman))

        # Add norman to the bar group.
        self.bar.join(self.norman)

        # Ensure Norman is in the bar group.
        self.assertTrue(self.bar.user_is_member(self.norman))

        # Test that the bar group has default permissions on the layer
        bar_read_perms = backend.objects_with_perm(self.bar, 'layers.view_layer', Layer)
        bar_write_perms = backend.objects_with_perm(self.bar, 'layers.change_layer', Layer)
        self.assertTrue(layer.id in bar_read_perms)
        self.assertTrue(layer.id not in bar_write_perms)

        # Give the bar group permissions to change the layer.
        layer.set_group_level(self.bar, Layer.LEVEL_WRITE)
        bar_read_perms = backend.objects_with_perm(self.bar, 'layers.view_layer', Layer)
        bar_write_perms = backend.objects_with_perm(self.bar, 'layers.change_layer', Layer)
        self.assertTrue(layer.id in bar_read_perms)
        self.assertTrue(layer.id in bar_write_perms)

        # Test that the bar group perms give Norman view and change permissions
        read_perms = backend.objects_with_perm(self.norman, 'layers.view_layer', Layer)
        write_perms = backend.objects_with_perm(self.norman, 'layers.change_layer', Layer)
        self.assertTrue(layer.id in read_perms)
        self.assertTrue(layer.id in write_perms)

    def test_groups_get_perms_when_added_to_object(self):
        """
        Verify that when a group is added to an object, the group gets permissions.

        This ensures the resourcebase_groups_changed signal is working correctly.  The signal has to be manually
        added to models that inherit from the ResourceBase class (layers, documents, maps).
        """
        layer = Layer.objects.all()[0]
        document = Document.objects.all()[0]
        map = Map.objects.all()[0]

        for resource_object in (layer, document, map):
            content_type = ContentType.objects.get_for_model(resource_object)

            # Ensure the object has no groups.
            self.assertEqual(0, resource_object.groups.all().count())

            # Make sure the group does not have any permissions on the layer.
            mappings = GroupObjectRoleMapping.objects.filter(object_id=resource_object.id,
                                                             object_ct=content_type,
                                                             group=self.bar)
            self.assertEqual(mappings.count(), 0)

            # Add the group to the layer.
            resource_object.groups.add(self.bar)

            # Ensure the group has been added to the layer's groups.
            self.assertEqual(1, resource_object.groups.all().count())
            self.assertTrue(self.bar in resource_object.groups.all())

            # Ensure the group now has permissions.
            mappings = GroupObjectRoleMapping.objects.filter(object_id=resource_object.id,
                                                             object_ct=content_type,
                                                             group=self.bar)
            self.assertTrue(mappings.count() > 0)

    def test_perms_info(self):
        """
        Tests the perms_info function (which passes permissions to the response context).
        """
        # Add test to test perms being sent to the front end.
        layer = Layer.objects.all()[0]
        perms_info = _perms_info(layer, LAYER_LEV_NAMES)

        # Ensure there is no group info for the layer object by default
        self.assertEqual(dict(), perms_info['groups'])

        # Add the foo group to the layer object groups
        layer.groups.add(self.bar)

        perms_info = _perms_info(layer, LAYER_LEV_NAMES)

        # Ensure foo is in the perms_info output
        self.assertDictEqual(perms_info['groups'], {u'bar': u'layer_readonly'})

    def test_resource_permissions(self):
        """
        Tests that the client can get and set group permissions through the test_resource_permissions view.
        """
        c = Client()
        self.assertTrue(c.login(username="admin", password="admin"))

        layer = Layer.objects.all()[0]
        document = Document.objects.all()[0]
        map_obj = Map.objects.all()[0]

        objects = layer, document, map_obj

        for obj in objects:
            response = c.get(reverse('resource_permissions', kwargs=dict(type=obj.geonode_type, resource_id=obj.id)))
            self.assertEqual(response.status_code, 200)
            js = json.loads(response.content)
            permissions = js.get('permissions', dict())

            if isinstance(permissions, unicode) or isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Ensure the groups value is empty by default
            self.assertDictEqual(permissions.get('groups'), dict())


            permissions = {"anonymous": "_none", "authenticated": "_none", "users": [["admin", obj.LEVEL_WRITE]],
                           "groups": [[self.bar.slug, obj.LEVEL_WRITE]]}

            # Give the bar group permissions
            response = c.post(reverse('resource_permissions', kwargs=dict(type=obj.geonode_type, resource_id=obj.id)),
                              data=json.dumps(permissions), content_type="application/json")

            self.assertEqual(response.status_code, 200)

            response = c.get(reverse('resource_permissions', kwargs=dict(type=obj.geonode_type, resource_id=obj.id)))

            js = json.loads(response.content)
            permissions = js.get('permissions', dict())

            if isinstance(permissions, unicode) or isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Make sure the bar group now has write permissions
            self.assertDictEqual(permissions['groups'], {'bar': obj.LEVEL_WRITE})

            # Remove group permissions
            permissions = {"anonymous": "_none", "authenticated": "_none", "users": [["admin", obj.LEVEL_WRITE]],
                           "groups": {}}

            # Update the object's permissions to remove the bar group
            response = c.post(reverse('resource_permissions', kwargs=dict(type=obj.geonode_type, resource_id=obj.id)),
                              data=json.dumps(permissions), content_type="application/json")

            self.assertEqual(response.status_code, 200)

            response = c.get(reverse('resource_permissions', kwargs=dict(type=obj.geonode_type, resource_id=obj.id)))

            js = json.loads(response.content)
            permissions = js.get('permissions', dict())

            if isinstance(permissions, unicode) or isinstance(permissions, str):
                permissions = json.loads(permissions)

            # Assert the bar group no longer has permissions
            self.assertDictEqual(permissions['groups'], {})


    def test_public_pages_render(self):
        "Verify pages that do not require login load without internal error"

        c = Client()

        response = c.get("/groups/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/members/")
        self.assertEqual(200, response.status_code)

        # 302 for auth failure since we redirect to login page
        response = c.get("/groups/create/")
        self.assertEqual(302, response.status_code)

        response = c.get("/groups/group/bar/update/")
        self.assertEqual(302, response.status_code)

        response = c.get("/groups/group/bar/maps/")
        self.assertEqual(302, response.status_code)

        response = c.get("/groups/group/bar/layers/")
        self.assertEqual(302, response.status_code)

        response = c.get("/groups/group/bar/remove/")
        self.assertEqual(302, response.status_code)

        # 405 - json endpoint, doesn't support GET
        response = c.get("/groups/group/bar/invite/")
        self.assertEqual(405, response.status_code)

    def test_protected_pages_render(self):
        "Verify pages that require login load without internal error"

        c = Client()
        self.assertTrue(c.login(username="admin", password="admin"))

        response = c.get("/groups/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/members/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/create/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/update/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/maps/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/layers/")
        self.assertEqual(200, response.status_code)

        response = c.get("/groups/group/bar/remove/")
        self.assertEqual(200, response.status_code)

        # 405 - json endpoint, doesn't support GET
        response = c.get("/groups/group/bar/invite/")
        self.assertEqual(405, response.status_code)
 

class MembershipTest(TestCase):
    "Tests membership logic in the geonode.contrib.groups models"

    fixtures = ["group_test_data"]

    def test_group_is_member(self):
        "Test checking group membership"

        anon = AnonymousUser()
        normal = User.objects.get(username="norman")
        group = Group.objects.get(slug="bar")

        self.assert_(not group.user_is_member(anon))
        self.assert_(not group.user_is_member(normal))

    def test_group_add_member(self):
        "Test adding a user to a group"

        anon = AnonymousUser()
        normal = User.objects.get(username="norman")
        group = Group.objects.get(slug="bar")
        group.join(normal)
        self.assert_(group.user_is_member(normal))
        self.assertRaises(ValueError, lambda: group.join(anon))


class InvitationTest(TestCase):
    "Tests invitation logic in geonode.contrib.groups models"

    fixtures = ["group_test_data"]

    def test_invite_user(self):
        "Test inviting a registered user"

        anon = AnonymousUser()
        normal = User.objects.get(username="norman")
        admin = User.objects.get(username="admin")
        group = Group.objects.get(slug="bar")
        group.invite(normal, admin, role="member", send=False)

        self.assert_(
            GroupInvitation.objects.filter(user=normal, from_user=admin, group=group).exists()
        )

        invite = GroupInvitation.objects.get(user=normal, from_user=admin, group=group)

        # Test that the user can access the token url.
        c = Client()
        c.login(username="norman", password="norman")
        response = c.get("/groups/group/{group}/invite/{token}/".format(group=group, token=invite.token))
        self.assertEqual(200, response.status_code)

    def test_accept_invitation(self):
        "Test accepting an invitation"

        anon = AnonymousUser()
        normal = User.objects.get(username="norman")
        admin = User.objects.get(username="admin")
        group = Group.objects.get(slug="bar")
        group.invite(normal, admin, role="member", send=False)

        invitation = GroupInvitation.objects.get(user=normal, from_user=admin, group=group)

        self.assertRaises(ValueError, lambda: invitation.accept(anon))
        self.assertRaises(ValueError, lambda: invitation.accept(admin))
        invitation.accept(normal) 

        self.assert_(group.user_is_member(normal))
        self.assert_(invitation.state == "accepted")

    def test_decline_invitation(self):
        "Test declining an invitation"

        anon = AnonymousUser()
        normal = User.objects.get(username="norman")
        admin = User.objects.get(username="admin")
        group = Group.objects.get(slug="bar")
        group.invite(normal, admin, role="member", send=False)

        invitation = GroupInvitation.objects.get(user=normal, from_user=admin, group=group)

        self.assertRaises(ValueError, lambda: invitation.decline(anon))
        self.assertRaises(ValueError, lambda: invitation.decline(admin))
        invitation.decline(normal) 

        self.assert_(not group.user_is_member(normal))
        self.assert_(invitation.state == "declined")
