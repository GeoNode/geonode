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
import requests

from urllib.parse import urlparse
from unittest.mock import patch, Mock
from django.core.exceptions import ObjectDoesNotExist

from io import BytesIO
from PIL import Image
from guardian.shortcuts import assign_perm, get_perms

from geonode.maps.models import Map
from geonode.thumbs import utils as thumb_utils
from geonode.base import enumerations
from geonode.layers.models import Dataset
from geonode.services.models import Service
from geonode.documents.models import Document
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.templatetags.base_tags import display_change_perms_button
from geonode.base.utils import OwnerRightsRequestViewUtils, ManageResourceOwnerPermissions
from geonode.base.models import (
    ResourceBase,
    MenuPlaceholder,
    Menu,
    MenuItem,
    Configuration,
    TopicCategory,
    Thesaurus,
    ThesaurusKeyword,
    generate_thesaurus_reference
)
from django.conf import settings
from django.template import Template, Context
from django.contrib.auth import get_user_model
from geonode.storage.manager import storage_manager
from django.test import Client, TestCase, override_settings, SimpleTestCase
from django.shortcuts import reverse

from geonode.base.middleware import ReadOnlyMiddleware, MaintenanceMiddleware
from geonode.base.templatetags.base_tags import get_visibile_resources, facets
from geonode.base.templatetags.thesaurus import (
    get_name_translation, get_thesaurus_localized_label, get_thesaurus_translation_by_id, get_unique_thesaurus_set,
    get_thesaurus_title,
    get_thesaurus_date,
)
from geonode.base.templatetags.user_messages import show_notification
from geonode import geoserver
from geonode.decorators import on_ogc_backend

from django.core.files import File
from django.core.management import call_command
from django.core.management.base import CommandError
from geonode.base.forms import ThesaurusAvailableForm


test_image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))


class ThumbnailTests(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        self.rb = ResourceBase.objects.create(owner=get_user_model().objects.get(username='admin'))

    def tearDown(self):
        super().tearDown()

    def test_initial_behavior(self):
        """
        Tests that an empty resource has a missing image as default thumbnail.
        """
        self.assertFalse(self.rb.has_thumbnail())
        missing = self.rb.get_thumbnail_url()
        self.assertTrue('missing_thumb' in os.path.splitext(missing)[0])

    def test_empty_image(self):
        """
        Tests that an empty image does not change the current resource thumbnail.
        """
        current = self.rb.get_thumbnail_url()
        self.rb.save_thumbnail('test-thumb', None)
        self.assertEqual(current, urlparse(self.rb.get_thumbnail_url()).path)

    @patch('PIL.Image.open', return_value=test_image)
    def test_monochromatic_image(self, image):
        """
        Tests that an monochromatic image does not change the current resource thumbnail.
        """
        filename = 'test-thumb'

        current = self.rb.get_thumbnail_url()
        self.rb.save_thumbnail(filename, image)
        self.assertEqual(current, urlparse(self.rb.get_thumbnail_url()).path)

        # cleanup: remove saved thumbnail
        thumb_utils.remove_thumbs(filename)
        self.assertFalse(thumb_utils.thumb_exists(filename))

    @patch('PIL.Image.open', return_value=test_image)
    def test_thumb_utils_methods(self, image):
        """
        Bunch of tests on thumb_utils helpers.
        """
        filename = 'test-thumb'
        upload_path = thumb_utils.thumb_path(filename)
        self.assertEqual(upload_path, os.path.join(settings.THUMBNAIL_LOCATION, filename))
        thumb_utils.remove_thumbs(filename)
        self.assertFalse(thumb_utils.thumb_exists(filename))
        f = BytesIO(test_image.tobytes())
        f.name = filename
        storage_manager.save(upload_path, File(f))
        self.assertTrue(thumb_utils.thumb_exists(filename))
        self.assertEqual(thumb_utils.thumb_size(upload_path), 10000)

        # cleanup: remove saved thumbnail
        thumb_utils.remove_thumbs(filename)
        self.assertFalse(thumb_utils.thumb_exists(filename))


class TestThumbnailUrl(GeoNodeBaseTestSupport):

    def setUp(self):
        super().setUp()
        f = BytesIO(test_image.tobytes())
        f.name = 'test_image.jpeg'


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
        super().setUp()
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
            f'Expected "{self.menu_0_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_0_0.title,
            rendered,
            f'Expected "{self.menu_item_0_0_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_0_1.title,
            rendered,
            f'Expected "{self.menu_item_0_0_1.title}" string in the rendered template'
        )
        # second menu
        self.assertIn(
            self.menu_0_1.title,
            rendered,
            f'Expected "{self.menu_0_1.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_1_0.title,
            rendered,
            f'Expected "{self.menu_item_0_1_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_1_1.title,
            rendered,
            f'Expected "{self.menu_item_0_1_1.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_1_2.title,
            rendered,
            f'Expected "{self.menu_item_0_1_2.title}" string in the rendered template'
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertNotIn(
            self.menu_1_0.title,
            rendered,
            f'No "{self.menu_1_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_1_0_0.title,
            rendered,
            f'No "{self.menu_item_1_0_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_1_0_1.title,
            rendered,
            f'No "{self.menu_item_1_0_1.title}" string expected in the rendered template'
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
            f'No "{self.menu_0_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_0_0.title,
            rendered,
            f'No "{self.menu_item_0_0_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_0_1.title,
            rendered,
            f'No "{self.menu_item_0_0_1.title}" string expected in the rendered template'
        )
        # second menu
        self.assertNotIn(
            self.menu_0_1.title,
            rendered,
            f'No "{self.menu_0_1.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_1_0.title,
            rendered,
            f'No "{self.menu_item_0_1_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_1_1.title,
            rendered,
            f'No "{self.menu_item_0_1_1.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_1_2.title,
            rendered,
            f'No "{self.menu_item_0_1_2.title}" string expected in the rendered template'
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertIn(
            self.menu_1_0.title,
            rendered,
            f'Expected "{self.menu_1_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_1_0_0.title,
            rendered,
            f'Expected "{self.menu_item_1_0_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_1_0_1.title,
            rendered,
            f'Expected "{self.menu_item_1_0_1.title}" string in the rendered template'
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
            f'Expected "{self.menu_0_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_0_0.title,
            rendered,
            f'Expected "{self.menu_item_0_0_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_0_1.title,
            rendered,
            f'Expected "{self.menu_item_0_0_1.title}" string in the rendered template'
        )
        # second menu
        self.assertIn(
            self.menu_0_1.title,
            rendered,
            f'Expected "{self.menu_0_1.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_1_0.title,
            rendered,
            f'Expected "{self.menu_item_0_1_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_1_1.title,
            rendered,
            f'Expected "{self.menu_item_0_1_1.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_0_1_2.title,
            rendered,
            f'Expected "{self.menu_item_0_1_2.title}" string in the rendered template'
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertNotIn(
            self.menu_1_0.title,
            rendered,
            f'No "{self.menu_1_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_1_0_0.title,
            rendered,
            f'No "{self.menu_item_1_0_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_1_0_1.title,
            rendered,
            f'No "{self.menu_item_1_0_1.title}" string expected in the rendered template'
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
            f'No "{self.menu_0_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_0_0.title,
            rendered,
            f'No "{self.menu_item_0_0_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_0_1.title,
            rendered,
            f'No "{self.menu_item_0_0_1.title}" string expected in the rendered template'
        )
        # second menu
        self.assertNotIn(
            self.menu_0_1.title,
            rendered,
            f'No "{self.menu_0_1.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_1_0.title,
            rendered,
            f'No "{self.menu_item_0_1_0.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_1_1.title,
            rendered,
            f'No "{self.menu_item_0_1_1.title}" string expected in the rendered template'
        )
        self.assertNotIn(
            self.menu_item_0_1_2.title,
            rendered,
            f'No "{self.menu_item_0_1_2.title}" string expected in the rendered template'
        )
        # menu_placeholder_1
        # first menu
        # unicode
        self.assertIn(
            self.menu_1_0.title,
            rendered,
            f'Expected "{self.menu_1_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_1_0_0.title,
            rendered,
            f'Expected "{self.menu_item_1_0_0.title}" string in the rendered template'
        )
        self.assertIn(
            self.menu_item_1_0_1.title,
            rendered,
            f'Expected "{self.menu_item_1_0_1.title}" string in the rendered template'
        )


class DeleteResourcesCommandTests(GeoNodeBaseTestSupport):

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
        user, _ = get_user_model().objects.get_or_create(username='user1')
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
        self.la = Dataset.objects.create(owner=self.user, title='test', is_approved=True)

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
        self.la = Dataset.objects.create(owner=self.user, title='test', is_approved=True)
        self.s = Service.objects.create(owner=self.user, title='test', is_approved=True)
        self.m = Map.objects.create(owner=self.user, title='test', is_approved=True)

    def test_get_concrete_resource(self):
        self.assertTrue(isinstance(
            OwnerRightsRequestViewUtils.get_resource(ResourceBase.objects.get(pk=self.d.id)), Document
        ))

        self.assertTrue(isinstance(
            OwnerRightsRequestViewUtils.get_resource(ResourceBase.objects.get(pk=self.la.id)), Dataset
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
        self.assertEqual(users_count, OwnerRightsRequestViewUtils.get_message_recipients(self.user).count())

    @override_settings(ADMIN_MODERATE_UPLOADS=False)
    def test_msg_recipients_workflow_off(self):
        users_count = 0
        self.assertEqual(users_count, OwnerRightsRequestViewUtils.get_message_recipients(self.user).count())

    @override_settings(ADMIN_MODERATE_UPLOADS=True)
    def test_display_change_perms_button_tag_moderated(self):
        admin_perms = display_change_perms_button(self.la, self.admin, {})
        user_perms = display_change_perms_button(self.la, self.user, {})
        self.assertTrue(admin_perms)
        self.assertFalse(user_perms)

    @override_settings(ADMIN_MODERATE_UPLOADS=False)
    def test_display_change_perms_button_tag_standard(self):
        admin_perms = display_change_perms_button(self.la, self.admin, {})
        user_perms = display_change_perms_button(self.la, self.user, {})
        self.assertTrue(admin_perms)
        self.assertTrue(user_perms)


class TestGetVisibleResource(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='mikel_arteta')
        self.category = TopicCategory.objects.create(identifier='biota')
        self.rb = ResourceBase.objects.create(category=self.category, owner=self.user)

    def test_category_data_not_shown_for_missing_resourcebase_permissions(self):
        """
        Test that a user without view permissions of a resource base does not see
        ISO category format data of the ISO category
        """
        categories = get_visibile_resources(self.user)
        self.assertEqual(categories['iso_formats'].count(), 0)

    def test_category_data_shown_for_with_resourcebase_permissions(self):
        """
        Test that a user with view permissions of a resource base can see
        ISO format data of the ISO category
        """
        assign_perm('view_resourcebase', self.user, self.rb)
        categories = get_visibile_resources(self.user)
        self.assertEqual(categories['iso_formats'].count(), 1)

    def test_visible_notifications(self):
        """
        Test that a standard user won't be able to show ADMINS_ONLY_NOTICE_TYPES
        """
        self.assertFalse(show_notification('monitoring_alert', self.user))
        self.assertTrue(show_notification('request_download_resourcebase', self.user))


class TestHtmlTagRemoval(SimpleTestCase):

    def test_not_tags_in_attribute(self):
        attribute_target_value = "This is not a templated text"
        r = ResourceBase()
        filtered_value = r._remove_html_tags(attribute_target_value)
        self.assertEqual(attribute_target_value, filtered_value)

    def test_simple_tags_in_attribute(self):
        tagged_value = "<p>This is not a templated text<p>"
        attribute_target_value = "This is not a templated text"
        r = ResourceBase()
        filtered_value = r._remove_html_tags(tagged_value)
        self.assertEqual(filtered_value, attribute_target_value)

    def test_complex_tags_in_attribute(self):
        tagged_value = """<p style="display:none;" id="test">This is not a templated text<p>
        <div class="test_css">Something in &iacute;container</div> <p>&pound;682m</p>"""
        attribute_target_value = """This is not a templated text         Something in ícontainer £682m"""
        r = ResourceBase()
        filtered_value = r._remove_html_tags(tagged_value)
        self.assertEqual(filtered_value, attribute_target_value)

    def test_converted_html_in_tags_with_char_references(self):
        tagged_value = """<p>&lt;p&gt;Abstract value &amp; some text&lt;/p&gt;</p>"""
        attribute_target_value = """Abstract value & some text"""
        r = ResourceBase()
        filtered_value = r._remove_html_tags(tagged_value)
        self.assertEqual(filtered_value, attribute_target_value)

    def test_converted_html_in_tags_with_with_multiple_tags(self):
        tagged_value = """<p><p><p><p>Abstract value &amp; some text</p></p></p></p>"""
        attribute_target_value = """Abstract value & some text"""
        r = ResourceBase()
        filtered_value = r._remove_html_tags(tagged_value)
        self.assertEqual(filtered_value, attribute_target_value)


class TestTagThesaurus(TestCase):

    #  loading test thesausurs
    fixtures = [
        "test_thesaurus.json"
    ]

    def setUp(self):
        self.sut = Thesaurus(
            identifier="foo_name",
            title="GEMET - INSPIRE themes, version 1.0",
            date="2018-05-23T10:25:56",
            description="GEMET - INSPIRE themes, version 1.0",
            slug="",
            about="http://inspire.ec.europa.eu/theme",
        )
        self.tkeywords = ThesaurusKeyword.objects.all()

    def test_get_unique_thesaurus_list(self):
        actual = get_unique_thesaurus_set(self.tkeywords)
        self.assertSetEqual({1, 3}, actual)

    def test_get_thesaurus_title(self):
        tid = self.__get_last_thesaurus().id
        actual = get_thesaurus_title(tid)
        self.assertEqual(self.sut.title, actual)

    def test_get_thesaurus_date(self):
        tid = self.__get_last_thesaurus().id
        actual = get_thesaurus_date(tid)
        self.assertEqual(self.sut.date, actual)

    def test_get_name_translation_raise_exception_if_identifier_does_not_exists(self):
        with self.assertRaises(ObjectDoesNotExist):
            get_name_translation('foo_indentifier')

    @patch('geonode.base.templatetags.thesaurus.get_language')
    def test_get_name_translation_return_thesauro_title_if_label_for_selected_language_does_not_exists(self, lang):
        lang.return_value = 'ke'
        actual = get_name_translation('inspire-theme')
        expected = "GEMET - INSPIRE themes, version 1.0"
        self.assertEqual(expected, actual)

    @patch('geonode.base.templatetags.thesaurus.get_language')
    def test_get_thesaurus_translation_by_id(self, lang):
        lang.return_value = 'it'
        actual = get_thesaurus_translation_by_id(1)
        expected = "Tema GEMET - INSPIRE, versione 1.0"
        self.assertEqual(expected, actual)

    @patch('geonode.base.templatetags.thesaurus.get_language')
    def test_get_thesaurus_localized_label(self, lang):
        lang.return_value = 'de'
        keyword = ThesaurusKeyword.objects.get(id=1)
        actual = get_thesaurus_localized_label(keyword)
        expected = "Adressen"
        self.assertEqual(expected, actual)

    @patch('geonode.base.templatetags.thesaurus.get_language')
    def test_get_name_translation_return_label_title_if_label_for_selected_language_exists(self, lang):
        lang.return_value = 'it'
        actual = get_name_translation('inspire-theme')
        expected = "Tema GEMET - INSPIRE, versione 1.0"
        self.assertEqual(expected, actual)

    @staticmethod
    def __get_last_thesaurus():
        return Thesaurus.objects.all().order_by("id")[0]


@override_settings(THESAURUS_DEFAULT_LANG="en")
class TestThesaurusAvailableForm(TestCase):

    #  loading test thesausurs
    fixtures = [
        "test_thesaurus.json"
    ]

    def setUp(self):
        self.sut = ThesaurusAvailableForm

    def test_form_is_valid_if_all_fields_are_missing(self):
        #  is now always true since the required is moved to the UI
        #  (like the other fields)
        actual = self.sut(data={})
        self.assertTrue(actual.is_valid())

    def test_form_is_invalid_if_fileds_send_unexpected_values(self):
        actual = self.sut(data={"1": [1, 2]})
        self.assertFalse(actual.is_valid())

    def test_form_is_valid_if_fileds_send_expected_values(self):
        actual = self.sut(data={"1": 1})
        self.assertTrue(actual.is_valid())

    def test_field_class_treq_is_correctly_set_when_field_is_required(self):
        actual = self.sut(data={"1": 1})
        required = actual.fields.get('1')
        obj_class = required.widget.attrs.get('class')
        self.assertTrue(obj_class == 'treq')

    def test_field_class_treq_is_not_set_when_field_is_optional(self):
        actual = self.sut(data={"1": 1})
        required = actual.fields.get('2')
        obj_class = required.widget.attrs.get('class')
        self.assertTrue(obj_class == '')

    def test_will_return_thesaurus_with_the_expected_defined_order(self):
        actual = self.sut(data={"1": 1})
        fields = list(actual.fields.items())
        #  will check if the first element of the tuple is the thesaurus_id = 2
        self.assertEqual(fields[0][0], '2')
        #  will check if the second element of the tuple is the thesaurus_id = 1
        self.assertEqual(fields[1][0], '1')

    def test_will_return_thesaurus_with_the_defaul_order_as_0(self):
        # Update thesaurus order to 0 in order to check if the default order by id is observed
        t = Thesaurus.objects.get(identifier='inspire-theme')
        t.order = 0
        t.save()
        actual = ThesaurusAvailableForm(data={"1": 1})
        fields = list(actual.fields.items())
        #  will check if the first element of the tuple is the thesaurus_id = 2
        self.assertEqual(fields[0][0], '1')
        #  will check if the second element of the tuple is the thesaurus_id = 1
        self.assertEqual(fields[1][0], '2')


class TestFacets(TestCase):

    def setUp(self):
        self.user = get_user_model().objects.create(username='test', email='test@test.com')
        Dataset.objects.create(
            owner=self.user, title='test_boxes', abstract='nothing', subtype='vector', is_approved=True
        )
        Dataset.objects.create(
            owner=self.user, title='test_1', abstract='contains boxes', subtype='vector', is_approved=True
        )
        Dataset.objects.create(
            owner=self.user, title='test_2', purpose='contains boxes', subtype='vector', is_approved=True
        )
        Dataset.objects.create(
            owner=self.user, title='test_3', subtype='vector', is_approved=True
        )

        Dataset.objects.create(
            owner=self.user, title='test_boxes', abstract='nothing', subtype='raster', is_approved=True
        )
        Dataset.objects.create(
            owner=self.user, title='test_1', abstract='contains boxes', subtype='raster', is_approved=True
        )
        Dataset.objects.create(
            owner=self.user, title='test_2', purpose='contains boxes', subtype='raster', is_approved=True
        )
        Dataset.objects.create(
            owner=self.user, title='test_boxes', subtype='raster', is_approved=True
        )

        self.request_mock = Mock(spec=requests.Request, GET=Mock())

    def test_facets_filter_datasets_returns_correctly(self):
        for _l in Dataset.objects.all():
            _l.set_default_permissions()
            _l.clear_dirty_state()
            _l.set_processing_state(enumerations.STATE_PROCESSED)
        self.request_mock.GET.get.side_effect = lambda key, self: {
            'title__icontains': 'boxes',
            'abstract__icontains': 'boxes',
            'purpose__icontains': 'boxes',
            'date__gte': None,
            'date__range': None,
            'date__lte': None,
            'extent': None
        }.get(key)
        self.request_mock.GET.getlist.return_value = None
        self.request_mock.user = self.user
        results = facets({'request': self.request_mock})
        self.assertEqual(results['vector'], 3)
        self.assertEqual(results['raster'], 4)


class TestGenerateThesaurusReference(TestCase):

    fixtures = [
        "test_thesaurus.json"
    ]

    def setUp(self):
        self.site_url = settings.SITEURL if hasattr(settings, "SITEURL") else "http://localhost"

    '''
    If the keyword.about does not exists, the url created will have a prefix and a specifier:
    as prefix:
        - use the Keyword's thesaurus.about URI if it exists,
        - otherwise use as prefix the geonode site URL composed with some thesaurus info: f'{settings.SITEURL}/thesaurus/{thesaurus.identifier}'
    as specifier:
        - we may use the ThesaurusKeyword.alt_label if it exists, otherwise its id

    So the final about field value will be composed as f'{prefix}#{specifier}'
    '''

    def test_should_return_keyword_url(self):
        expected = "http://inspire.ec.europa.eu/theme/ad"
        keyword = ThesaurusKeyword.objects.get(id=1)
        actual = generate_thesaurus_reference(keyword)
        keyword.refresh_from_db()
        '''
        Check if the expected about has been created and that the instance is correctly updated
        '''
        self.assertEqual(expected, actual)
        self.assertEqual(expected, keyword.about)

    def test_should_return_as_url_thesaurus_about_and_keyword_alt_label(self):
        expected = "http://inspire.ec.europa.eu/theme#foo_keyword"
        keyword = ThesaurusKeyword.objects.get(alt_label='foo_keyword')
        actual = generate_thesaurus_reference(keyword)
        keyword.refresh_from_db()
        '''
        Check if the expected about has been created and that the instance is correctly updated
        '''
        self.assertEqual(expected, actual)
        self.assertEqual(expected, keyword.about)

    def test_should_return_as_url_thesaurus_about_and_keyword_id(self):
        expected = "http://inspire.ec.europa.eu/theme#37"
        keyword = ThesaurusKeyword.objects.get(id=37)
        actual = generate_thesaurus_reference(keyword)
        keyword.refresh_from_db()
        '''
        Check if the expected about has been created and that the instance is correctly updated
        '''
        self.assertEqual(expected, actual)
        self.assertEqual(expected, keyword.about)

    def test_should_return_as_url_site_url_and_keyword_label(self):
        expected = f"{self.site_url}/thesaurus/no-about-thesauro#bar_keyword"
        keyword = ThesaurusKeyword.objects.get(id=39)
        actual = generate_thesaurus_reference(keyword)
        keyword.refresh_from_db()
        '''
        Check if the expected about has been created and that the instance is correctly updated
        '''
        self.assertEqual(expected, actual)
        self.assertEqual(expected, keyword.about)

    def test_should_return_as_url_site_url_and_keyword_id(self):
        expected = f"{self.site_url}/thesaurus/no-about-thesauro#38"
        keyword = ThesaurusKeyword.objects.get(id=38)
        actual = generate_thesaurus_reference(keyword)
        keyword.refresh_from_db()
        '''
        Check if the expected about has been created and that the instance is correctly updated
        '''
        self.assertEqual(expected, actual)
        self.assertEqual(expected, keyword.about)
