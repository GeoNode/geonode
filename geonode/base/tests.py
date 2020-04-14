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

import os

from guardian.shortcuts import get_perms

from geonode.base.utils import OwnerRightsRequestViewUtils, ManageResourceOwnerPermissions
from geonode.documents.models import Document
from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.services.models import Service
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.models import (
    ResourceBase, MenuPlaceholder, Menu, MenuItem, Configuration
)
from django.template import Template, Context
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.shortcuts import reverse

from geonode.base.middleware import ReadOnlyMiddleware, MaintenanceMiddleware
from geonode import geoserver
from geonode.decorators import on_ogc_backend

from django.core.management import call_command
from django.core.management.base import CommandError


class ThumbnailTests(GeoNodeBaseTestSupport):

    def setUp(self):
        super(ThumbnailTests, self).setUp()
        self.rb = ResourceBase.objects.create()

    def test_initial_behavior(self):
        self.assertFalse(self.rb.has_thumbnail())
        missing = self.rb.get_thumbnail_url()
        self.assertTrue('missing_thumb' in os.path.splitext(missing)[0])


class TestCreationOfMissingMetadataAuthorsOrPOC(ThumbnailTests):

    def test_add_missing_metadata_author_or_poc(self):
        """
        Test that calling add_missing_metadata_author_or_poc resource method sets
        a missing metadata_author and/or point of contact (poc) to resource owner
        """
        user = get_user_model().objects.create(username='zlatan_i')
        self.rb.owner = user
        self.rb.add_missing_metadata_author_or_poc()
        self.assertEqual(self.rb.metadata_author.username, 'zlatan_i')
        self.assertEqual(self.rb.poc.username, 'zlatan_i')


class RenderMenuTagTest(GeoNodeBaseTestSupport):
    """
    Test class for render_menu and render_top_menu custom tags of base_tags
    """

    def setUp(self):
        super(RenderMenuTagTest, self).setUp()
        self.placeholder_0 = MenuPlaceholder.objects.create(
            name='test_menu_placeholder_0'
        )
        self.placeholder_1 = MenuPlaceholder.objects.create(
            name='test_unicode_äöü_menu_placeholder_1'
        )
        self.menu_0_0 = Menu.objects.create(
            title='test_menu_0_0',
            order=0,
            placeholder=self.placeholder_0

        )
        self.menu_0_1 = Menu.objects.create(
            title='test_menu_0_1',
            order=1,
            placeholder=self.placeholder_0

        )
        self.menu_1_0 = Menu.objects.create(
            title='test_unicode_äöü_menu_1_0',
            order=0,
            placeholder=self.placeholder_1

        )
        self.menu_item_0_0_0 = MenuItem.objects.create(
            title='test_menu_item_0_0_0',
            order=0,
            blank_target=False,
            url='/about',
            menu=self.menu_0_0
        )
        self.menu_item_0_0_1 = MenuItem.objects.create(
            title='test_menu_item_0_0_1',
            order=1,
            blank_target=False,
            url='/about',
            menu=self.menu_0_0
        )
        self.menu_item_0_1_0 = MenuItem.objects.create(
            title='test_menu_item_0_1_0',
            order=0,
            blank_target=False,
            url='/about',
            menu=self.menu_0_1
        )
        self.menu_item_0_1_1 = MenuItem.objects.create(
            title='test_menu_item_0_1_1',
            order=1,
            blank_target=False,
            url='/about',
            menu=self.menu_0_1
        )
        self.menu_item_0_1_2 = MenuItem.objects.create(
            title='test_menu_item_0_1_2',
            order=2,
            blank_target=False,
            url='/about',
            menu=self.menu_0_1
        )
        self.menu_item_1_0_0 = MenuItem.objects.create(
            title='test_unicode_äöü_menu_item_1_0_0',
            order=0,
            blank_target=False,
            url='/about',
            menu=self.menu_1_0
        )
        self.menu_item_1_0_1 = MenuItem.objects.create(
            title='test_unicode_äöü_menu_item_1_0_1',
            order=1,
            blank_target=False,
            url='/about',
            menu=self.menu_1_0
        )

    def test_get_menu_placeholder_0(self):
        template = Template(
            "{% load base_tags %} {% get_menu 'test_menu_placeholder_0' %}"
        )
        rendered = template.render(Context({}))
        # menu_placeholder_0
        # first menu with ascii chars
        self.assertIn(
            self.menu_0_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_0_0_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_0_0_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_0_1.title
            )
        )
        # second menu
        self.assertIn(
            self.menu_0_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_0_1.title
            )
        )
        self.assertIn(
            self.menu_item_0_1_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_1_0.title
            )
        )
        self.assertIn(
            self.menu_item_0_1_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_1_1.title
            )
        )
        self.assertIn(
            self.menu_item_0_1_2.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_1_2.title
            )
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertNotIn(
            self.menu_1_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_1_0_1.title
            )
        )

    def test_get_menu_placeholder_1(self):
        template = Template(
            "{% load base_tags %} {% get_menu 'test_unicode_äöü_menu_placeholder_1' %}"
        )
        rendered = template.render(Context({}))
        # menu_placeholder_0
        # first menu
        self.assertNotIn(
            self.menu_0_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_0_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_0_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_0_1.title
            )
        )
        # second menu
        self.assertNotIn(
            self.menu_0_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_0_1.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_1_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_1_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_1_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_1_1.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_1_2.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_1_2.title
            )
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertIn(
            self.menu_1_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_1_0_1.title
            )
        )

    def test_render_nav_menu_placeholder_0(self):
        template = Template(
            "{% load base_tags %} {% render_nav_menu 'test_menu_placeholder_0' %}"
        )
        rendered = template.render(Context({}))
        # menu_placeholder_0
        # first menu
        self.assertIn(
            self.menu_0_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_0_0_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_0_0_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_0_1.title
            )
        )
        # second menu
        self.assertIn(
            self.menu_0_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_0_1.title
            )
        )
        self.assertIn(
            self.menu_item_0_1_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_1_0.title
            )
        )
        self.assertIn(
            self.menu_item_0_1_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_1_1.title
            )
        )
        self.assertIn(
            self.menu_item_0_1_2.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_0_1_2.title
            )
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertNotIn(
            self.menu_1_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_1_0_1.title
            )
        )

    def test_render_nav_menu_placeholder_1(self):
        template = Template(
            "{% load base_tags %} {% render_nav_menu 'test_unicode_äöü_menu_placeholder_1' %}"
        )
        rendered = template.render(Context({}))
        # menu_placeholder_0
        # first menu
        self.assertNotIn(
            self.menu_0_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_0_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_0_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_0_1.title
            )
        )
        # second menu
        self.assertNotIn(
            self.menu_0_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_0_1.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_1_0.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_1_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_1_1.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_1_1.title
            )
        )
        self.assertNotIn(
            self.menu_item_0_1_2.title,
            rendered,
            'No "{}" string expected in the rendered template'.format(
                self.menu_item_0_1_2.title
            )
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertIn(
            self.menu_1_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_0.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_1.title,
            rendered,
            'Expected "{}" string in the rendered template'.format(
                self.menu_item_1_0_1.title
            )
        )


class DeleteResourcesCommandTests(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()

    def test_delete_resources_no_arguments(self):
        args = []
        kwargs = {}

        with self.assertRaises(CommandError) as exception:
            call_command('delete_resources', *args, **kwargs)

        self.assertIn(
            'No configuration provided',
            exception.exception.args[0],
            '"No configuration" exception expected.'
        )

    def test_delete_resources_too_many_arguments(self):
        args = []
        kwargs = {'config_path': '/example/config.txt', 'map_filters': "*"}

        with self.assertRaises(CommandError) as exception:
            call_command('delete_resources', *args, **kwargs)

        self.assertIn(
            'Too many configuration options provided',
            exception.exception.args[0],
            '"Too many configuration options provided" exception expected.'
        )

    def test_delete_resource_config_file_not_existing(self):
        args = []
        kwargs = {'config_path': '/example/config.json'}

        with self.assertRaises(CommandError) as exception:
            call_command('delete_resources', *args, **kwargs)

        self.assertIn(
            'Specified configuration file does not exist',
            exception.exception.args[0],
            '"Specified configuration file does not exist" exception expected.'
        )

    def test_delete_resource_config_file_empty(self):
        # create an empty config file
        config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'delete_resources_config.json')
        open(config_file_path, 'a').close()

        args = []
        kwargs = {'config_path': config_file_path}

        with self.assertRaises(CommandError) as exception:
            call_command('delete_resources', *args, **kwargs)

        self.assertIn(
            'Specified configuration file is empty',
            exception.exception.args[0],
            '"Specified configuration file is empty" exception expected.'
        )

        # delete the config file
        os.remove(config_file_path)


class ConfigurationTest(GeoNodeBaseTestSupport):

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    def test_read_only_whitelist(self):
        web_client = Client()

        # set read-only flag
        config = Configuration.load()
        config.read_only = True
        config.maintenance = False
        config.save()

        # post to whitelisted URLs as AnonymousUser
        for url_name in ReadOnlyMiddleware.WHITELISTED_URL_NAMES:
            if url_name == 'login':
                response = web_client.post(reverse('admin:login'))
            elif url_name == 'logout':
                response = web_client.post(reverse('admin:logout'))
            else:
                response = web_client.post(reverse(url_name))

            self.assertNotEqual(response.status_code, 405, 'Whitelisted URL is not available.')

    def test_read_only_casual_user_privileges(self):
        web_client = Client()
        url_name = 'autocomplete_region'

        # set read-only flag
        config = Configuration.load()
        config.read_only = True
        config.maintenance = False
        config.save()

        # get user
        user = get_user_model().objects.get(username='user1')
        web_client.force_login(user)

        # post not whitelisted URL as superuser
        response = web_client.post(reverse(url_name))

        self.assertEqual(response.status_code, 405, 'User is allowed to post to forbidden URL')

    def test_maintenance_whitelist(self):

        web_client = Client()

        # set read-only flag
        config = Configuration.load()
        config.read_only = False
        config.maintenance = True
        config.save()

        # post to whitelisted URLs as AnonymousUser
        for url_name in MaintenanceMiddleware.WHITELISTED_URL_NAMES:
            if url_name == 'login':
                response = web_client.get(reverse('admin:login'))
            elif url_name == 'logout':
                response = web_client.get(reverse('admin:logout'))
            elif url_name == 'index':
                # url needed in the middleware only for admin panel login redirection
                continue
            else:
                response = web_client.get(reverse(url_name))

            self.assertNotEqual(response.status_code, 503, 'Whitelisted URL is not available.')

    def test_maintenance_false(self):
        web_client = Client()

        # set read-only flag
        config = Configuration.load()
        config.read_only = False
        config.maintenance = False
        config.save()

        # post not whitelisted URL as superuser
        response = web_client.get('/')

        self.assertNotEqual(response.status_code, 503, 'User is allowed to get index page')

    def test_maintenance_true(self):
        web_client = Client()

        # set read-only flag
        config = Configuration.load()
        config.read_only = False
        config.maintenance = True
        config.save()

        # post not whitelisted URL as superuser
        response = web_client.get('/')

        self.assertEqual(response.status_code, 503, 'User is allowed to get index page')


class TestOwnerPermissionManagement(TestCase):
    """
    Only Layers has custom permissions so this is the only model which is tested.
    Models are always treat in the same way
    """

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='test', email='test@test.com')
        self.la = Layer.objects.create(owner=self.user, title='test', is_approved=True)

    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_owner_has_no_permissions(self):
        l_manager = ManageResourceOwnerPermissions(self.la)
        l_manager.set_owner_permissions_according_to_workflow()

        self.assertEqual(self._retrieve_resource_perms_definition(self.la, ['read', 'download']).sort(),
                         get_perms(self.user, self.la.get_self_resource()).sort()
                         )

    @override_settings(ADMIN_MODERATE_UPLOADS=False)
    def test_user_has_own_permissions(self):
        l_manager = ManageResourceOwnerPermissions(self.la)
        l_manager.set_owner_permissions_according_to_workflow()

        self.assertEqual(self._retrieve_resource_perms_definition(self.la).sort(),
                         get_perms(self.user, self.la.get_self_resource()).sort()
                         )

    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_user_has_permissions_restored(self):
        self.la.is_approved = False
        self.la.save()
        l_manager = ManageResourceOwnerPermissions(self.la)
        l_manager.set_owner_permissions_according_to_workflow()

        self.assertEqual(self._retrieve_resource_perms_definition(self.la).sort(),
                         get_perms(self.user, self.la.get_self_resource()).sort()
                         )

    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_remove_and_add_perms(self):
        l_manager = ManageResourceOwnerPermissions(self.la)
        l_manager.set_owner_permissions_according_to_workflow()

        self.assertEqual(self._retrieve_resource_perms_definition(self.la, ['read', 'download']).sort(),
                         get_perms(self.user, self.la.get_self_resource()).sort()
                         )

        self.la.is_approved = False
        self.la.save()

        l_manager.set_owner_permissions_according_to_workflow()

        self.assertEqual(self._retrieve_resource_perms_definition(self.la).sort(),
                         get_perms(self.user, self.la.get_self_resource()).sort()
                         )

    def _retrieve_resource_perms_definition(self, resource, perm_key_bundle=[]):
        ret = []
        if perm_key_bundle:
            for key in perm_key_bundle:
                ret.extend(resource.BASE_PERMISSIONS.get(key, []))
                ret.extend(resource.PERMISSIONS.get(key, []))
        else:
            [ret.extend(r) for r in list(resource.BASE_PERMISSIONS.values()) + list(resource.PERMISSIONS.values())]
        return ret


class TestOwnerRightsRequestUtils(TestCase):

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(username='test', email='test@test.com')
        self.admin = User.objects.create(username='admin', email='test@test.com', is_superuser=True)
        self.d = Document.objects.create(owner=self.user, title='test', is_approved=True)
        self.la = Layer.objects.create(owner=self.user, title='test', is_approved=True)
        self.s = Service.objects.create(owner=self.user, title='test', is_approved=True)
        self.m = Map.objects.create(owner=self.user, title='test', is_approved=True, zoom=0, center_x=0.0,
                                    center_y=0.0)

    def test_get_concrete_resource(self):
        self.assertTrue(isinstance(
            OwnerRightsRequestViewUtils.get_resource(ResourceBase.objects.get(pk=self.d.id)), Document
        ))

        self.assertTrue(isinstance(
            OwnerRightsRequestViewUtils.get_resource(ResourceBase.objects.get(pk=self.la.id)), Layer
        ))

        self.assertTrue(isinstance(
            OwnerRightsRequestViewUtils.get_resource(ResourceBase.objects.get(pk=self.s.id)), Service
        ))

        self.assertTrue(isinstance(
            OwnerRightsRequestViewUtils.get_resource(ResourceBase.objects.get(pk=self.m.id)), Map
        ))

    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_msg_recipients_admin_mode(self):
        users_count = 1
        self.assertEqual(users_count, OwnerRightsRequestViewUtils.get_message_recipients().count())

    @override_settings(ADMIN_MODERATE_UPLOADS=False)
    def test_msg_recipients_workflow_off(self):
        users_count = 0
        self.assertEqual(users_count, OwnerRightsRequestViewUtils.get_message_recipients().count())
