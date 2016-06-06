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

import json

from django.core.urlresolvers import reverse
from django.test import TestCase
from tastypie.test import ResourceTestCase
from django.contrib.auth import get_user_model
from guardian.shortcuts import get_anonymous_user, assign_perm, remove_perm

from geonode.base.populate_test_data import create_models, all_public
from geonode.maps.tests_populate_maplayers import create_maplayers
from geonode.people.models import Profile
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.layers.populate_layers_data import create_layer_data
from geonode.groups.models import Group


class BulkPermissionsTests(ResourceTestCase):
    fixtures = ['initial_data.json', 'bobby']

    def setUp(self):
        super(BulkPermissionsTests, self).setUp()

        self.user = 'admin'
        self.passwd = 'admin'
        self.list_url = reverse(
            'api_dispatch_list',
            kwargs={
                'api_name': 'api',
                'resource_name': 'layers'})
        self.bulk_perms_url = reverse('bulk_permissions')
        create_models(type='layer')
        all_public()
        self.perm_spec = {
            "users": {"admin": ["view_resourcebase"]}, "groups": {}}

    def test_set_bulk_permissions(self):
        """Test that after restrict view permissions on two layers
        bobby is unable to see them"""

        layers = Layer.objects.all()[:2].values_list('id', flat=True)
        layers_id = map(lambda x: str(x), layers)

        self.client.login(username='admin', password='admin')
        resp = self.client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 8)
        data = {
            'permissions': json.dumps(self.perm_spec),
            'resources': layers_id
        }
        resp = self.client.post(self.bulk_perms_url, data)
        self.assertHttpOK(resp)
        self.client.logout()

        self.client.login(username='bobby', password='bob')
        resp = self.client.get(self.list_url)
        self.assertEquals(len(self.deserialize(resp)['objects']), 6)

    def test_bobby_cannot_set_all(self):
        """Test that Bobby can set the permissions only only on the ones
        for which he has the right"""

        layer = Layer.objects.all()[0]
        self.client.login(username='admin', password='admin')
        # give bobby the right to change the layer permissions
        assign_perm('change_resourcebase', Profile.objects.get(username='bobby'), layer.get_self_resource())
        self.client.logout()
        self.client.login(username='bobby', password='bob')
        layer2 = Layer.objects.all()[1]
        data = {
            'permissions': json.dumps({"users": {"bobby": ["view_resourcebase"]}, "groups": {}}),
            'resources': [layer.id, layer2.id]
        }
        resp = self.client.post(self.bulk_perms_url, data)
        self.assertTrue(layer2.title in json.loads(resp.content)['not_changed'])


class PermissionsTest(TestCase):

    """Tests GeoNode permissions
    """

    fixtures = ['initial_data.json', 'bobby']

    perm_spec = {
        "users": {
            "admin": [
                "change_resourcebase",
                "change_resourcebase_permissions",
                "view_resourcebase"]},
        "groups": {}}

    # Permissions Tests

    # Users
    # - admin (pk=2)
    # - bobby (pk=1)

    def setUp(self):
        self.user = 'admin'
        self.passwd = 'admin'
        create_models(type='layer')
        create_layer_data()
        self.anonymous_user = get_anonymous_user()

    def test_layer_set_default_permissions(self):
        """Verify that Layer.set_default_permissions is behaving as expected
        """

        # Get a Layer object to work with
        layer = Layer.objects.all()[0]
        # Set the default permissions
        layer.set_default_permissions()

        # Test that the anonymous user can read
        self.assertTrue(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that the owner user can read
        self.assertTrue(
            layer.owner.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that the owner user can download it
        self.assertTrue(
            layer.owner.has_perm(
                'download_resourcebase',
                layer.get_self_resource()))

        # Test that the owner user can edit metadata
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase_metadata',
                layer.get_self_resource()))

        # Test that the owner user can edit data if is vector type
        if layer.storeType == 'dataStore':
            self.assertTrue(
                layer.owner.has_perm(
                    'change_layer_data',
                    layer))

        # Test that the owner user can edit styles
        self.assertTrue(
            layer.owner.has_perm(
                'change_layer_style',
                layer))

        # Test that the owner can manage the layer
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase',
                layer.get_self_resource()))
        self.assertTrue(
            layer.owner.has_perm(
                'delete_resourcebase',
                layer.get_self_resource()))
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase_permissions',
                layer.get_self_resource()))
        self.assertTrue(
            layer.owner.has_perm(
                'publish_resourcebase',
                layer.get_self_resource()))

    def test_set_layer_permissions(self):
        """Verify that the set_layer_permissions view is behaving as expected
        """

        # Get a layer to work with
        layer = Layer.objects.all()[0]

        # FIXME Test a comprehensive set of permissions specifications

        # Set the Permissions

        layer.set_permissions(self.perm_spec)

        # Test that the Permissions for anonymous user is are set
        self.assertFalse(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that previous permissions for users other than ones specified in
        # the perm_spec (and the layers owner) were removed
        current_perms = layer.get_all_level_info()
        self.assertEqual(len(current_perms['users'].keys()), 2)

        # Test that the User permissions specified in the perm_spec were
        # applied properly
        for username, perm in self.perm_spec['users'].items():
            user = get_user_model().objects.get(username=username)
            self.assertTrue(user.has_perm(perm, layer.get_self_resource()))

    def test_ajax_layer_permissions(self):
        """Verify that the ajax_layer_permissions view is behaving as expected
        """

        # Setup some layer names to work with
        valid_layer_typename = Layer.objects.all()[0].id
        invalid_layer_id = 9999999

        # Test that an invalid layer.typename is handled for properly
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    invalid_layer_id,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEquals(response.status_code, 404)

        # Test that GET returns permissions
        response = self.client.get(
            reverse(
                'resource_permissions',
                args=(
                    valid_layer_typename,
                )))
        assert('permissions' in response.content)

        # Test that a user is required to have maps.change_layer_permissions

        # First test un-authenticated
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_layer_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Next Test with a user that does NOT have the proper perms
        logged_in = self.client.login(username='bobby', password='bob')
        self.assertEquals(logged_in, True)
        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_layer_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")
        self.assertEquals(response.status_code, 401)

        # Login as a user with the proper permission and test the endpoint
        logged_in = self.client.login(username='admin', password='admin')
        self.assertEquals(logged_in, True)

        response = self.client.post(
            reverse(
                'resource_permissions', args=(
                    valid_layer_typename,)), data=json.dumps(
                self.perm_spec), content_type="application/json")

        # Test that the method returns 200
        self.assertEquals(response.status_code, 200)

        # Test that the permissions specification is applied

        # Should we do this here, or assume the tests in
        # test_set_layer_permissions will handle for that?

    def test_perms_info(self):
        """ Verify that the perms_info view is behaving as expected
        """

        # Test with a Layer object
        layer = Layer.objects.all()[0]
        layer.set_default_permissions()
        # Test that the anonymous user can read
        self.assertTrue(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        # Test that layer owner can edit layer
        self.assertTrue(
            layer.owner.has_perm(
                'change_resourcebase',
                layer.get_self_resource()))

        # TODO Much more to do here once jj0hns0n understands the ACL system
        # better

        # Test with a Map object
        # TODO

    # now we test permissions, first on an authenticated user and then on the
    # anonymous user
    # 1. view_resourcebase
    # 2. change_resourcebase
    # 3. delete_resourcebase
    # 4. change_resourcebase_metadata
    # 5. change_resourcebase_permissions
    # 6. change_layer_data
    # 7. change_layer_style

    def test_not_superuser_permissions(self):

        # grab bobby
        bob = get_user_model().objects.get(username='bobby')

        # grab a layer
        layer = Layer.objects.all()[0]
        layer.set_default_permissions()
        # verify bobby has view/change permissions on it but not manage
        self.assertFalse(
            bob.has_perm(
                'change_resourcebase_permissions',
                layer.get_self_resource()))

        self.assertTrue(self.client.login(username='bobby', password='bob'))

        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that bobby can access the layer
        # detail page
        self.assertTrue(
            bob.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))

        response = self.client.get(reverse('layer_detail', args=(layer.typename,)))
        self.assertEquals(response.status_code, 200)
        # 1.2 has not view_resourcebase: verify that bobby can not access the
        # layer detail page
        remove_perm('view_resourcebase', bob, layer.get_self_resource())
        anonymous_group = Group.objects.get(name='anonymous')
        remove_perm('view_resourcebase', anonymous_group, layer.get_self_resource())
        response = self.client.get(reverse('layer_detail', args=(layer.typename,)))
        self.assertEquals(response.status_code, 401)

        # 2. change_resourcebase
        # 2.1 has not change_resourcebase: verify that bobby cannot access the
        # layer replace page
        response = self.client.get(reverse('layer_replace', args=(layer.typename,)))
        self.assertEquals(response.status_code, 401)
        # 2.2 has change_resourcebase: verify that bobby can access the layer
        # replace page
        assign_perm('change_resourcebase', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_replace', args=(layer.typename,)))
        self.assertEquals(response.status_code, 200)

        # 3. delete_resourcebase
        # 3.1 has not delete_resourcebase: verify that bobby cannot access the
        # layer delete page
        response = self.client.get(reverse('layer_remove', args=(layer.typename,)))
        self.assertEquals(response.status_code, 401)
        # 3.2 has delete_resourcebase: verify that bobby can access the layer
        # delete page
        assign_perm('delete_resourcebase', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'delete_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_remove', args=(layer.typename,)))
        self.assertEquals(response.status_code, 200)

        # 4. change_resourcebase_metadata
        # 4.1 has not change_resourcebase_metadata: verify that bobby cannot
        # access the layer metadata page
        response = self.client.get(reverse('layer_metadata', args=(layer.typename,)))
        self.assertEquals(response.status_code, 401)
        # 4.2 has delete_resourcebase: verify that bobby can access the layer
        # delete page
        assign_perm('change_resourcebase_metadata', bob, layer.get_self_resource())
        self.assertTrue(
            bob.has_perm(
                'change_resourcebase_metadata',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_metadata', args=(layer.typename,)))
        self.assertEquals(response.status_code, 200)

        # 5. change_resourcebase_permissions
        # should be impossible for the user without change_resourcebase_permissions
        # to change permissions as the permission form is not available in the
        # layer detail page?

        # 6. change_layer_data
        # must be done in integration test sending a WFS-T request with CURL

        # 7. change_layer_style
        # 7.1 has not change_layer_style: verify that bobby cannot access
        # the layer style page
        response = self.client.get(reverse('layer_style_manage', args=(layer.typename,)))
        self.assertEquals(response.status_code, 401)
        # 7.2 has change_layer_style: verify that bobby can access the
        # change layer style page
        assign_perm('change_layer_style', bob, layer)
        self.assertTrue(
            bob.has_perm(
                'change_layer_style',
                layer))
        response = self.client.get(reverse('layer_style_manage', args=(layer.typename,)))
        self.assertEquals(response.status_code, 200)

    def test_anonymus_permissions(self):

        # grab a layer
        layer = Layer.objects.all()[0]
        layer.set_default_permissions()
        # 1. view_resourcebase
        # 1.1 has view_resourcebase: verify that anonymous user can access
        # the layer detail page
        self.assertTrue(
            self.anonymous_user.has_perm(
                'view_resourcebase',
                layer.get_self_resource()))
        response = self.client.get(reverse('layer_detail', args=(layer.typename,)))
        self.assertEquals(response.status_code, 200)
        # 1.2 has not view_resourcebase: verify that anonymous user can not
        # access the layer detail page
        remove_perm('view_resourcebase', self.anonymous_user, layer.get_self_resource())
        anonymous_group = Group.objects.get(name='anonymous')
        remove_perm('view_resourcebase', anonymous_group, layer.get_self_resource())
        response = self.client.get(reverse('layer_detail', args=(layer.typename,)))
        self.assertEquals(response.status_code, 302)

        # 2. change_resourcebase
        # 2.1 has not change_resourcebase: verify that anonymous user cannot
        # access the layer replace page but redirected to login
        response = self.client.get(reverse('layer_replace', args=(layer.typename,)))
        self.assertEquals(response.status_code, 302)

        # 3. delete_resourcebase
        # 3.1 has not delete_resourcebase: verify that anonymous user cannot
        # access the layer delete page but redirected to login
        response = self.client.get(reverse('layer_remove', args=(layer.typename,)))
        self.assertEquals(response.status_code, 302)

        # 4. change_resourcebase_metadata
        # 4.1 has not change_resourcebase_metadata: verify that anonymous user
        # cannot access the layer metadata page but redirected to login
        response = self.client.get(reverse('layer_metadata', args=(layer.typename,)))
        self.assertEquals(response.status_code, 302)

        # 5 N\A? 6 is an integration test...

        # 7. change_layer_style
        # 7.1 has not change_layer_style: verify that anonymous user cannot access
        # the layer style page but redirected to login
        response = self.client.get(reverse('layer_style_manage', args=(layer.typename,)))
        self.assertEquals(response.status_code, 302)

    def test_map_download(self):
        """Test the correct permissions on layers on map download"""
        create_models(type='map')
        create_maplayers()
        # Get a Map
        the_map = Map.objects.get(title='GeoNode Default Map')

        # Get a MapLayer and set the parameters as it is local and not a background
        # and leave it alone in the map
        map_layer = the_map.layer_set.get(name='geonode:CA')
        map_layer.local = True
        map_layer.group = 'overlay'
        map_layer.save()
        the_map.layer_set.all().delete()
        the_map.layer_set.add(map_layer)

        # Get the Layer and set the permissions for bobby to it and the map
        bobby = Profile.objects.get(username='bobby')
        the_layer = Layer.objects.get(typename='geonode:CA')
        remove_perm('download_resourcebase', bobby, the_layer.get_self_resource())
        remove_perm('download_resourcebase', Group.objects.get(name='anonymous'),
                    the_layer.get_self_resource())
        assign_perm('view_resourcebase', bobby, the_layer.get_self_resource())
        assign_perm('download_resourcebase', bobby, the_map.get_self_resource())

        self.client.login(username='bobby', password='bob')

        response = self.client.get(reverse('map_download', args=(the_map.id,)))
        self.assertTrue('Could not find downloadable layers for this map' in response.content)
