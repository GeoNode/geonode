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

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.models import (
    ResourceBase, MenuPlaceholder, Menu, MenuItem, Configuration
)
from django.template import Template, Context
from django.contrib.auth import get_user_model
from django.test import Client
from django.shortcuts import reverse

from geonode.base.middleware import ReadOnlyMiddleware, MaintenanceMiddleware
from geonode import geoserver
from geonode.decorators import on_ogc_backend


class ThumbnailTests(GeoNodeBaseTestSupport):

    def setUp(self):
        super(ThumbnailTests, self).setUp()
        self.rb = ResourceBase.objects.create()

    def test_initial_behavior(self):
        self.assertFalse(self.rb.has_thumbnail())
        missing = self.rb.get_thumbnail_url()
        self.assertTrue('missing_thumb' in os.path.splitext(missing)[0])


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
            name=u'test_unicode_äöü_menu_placeholder_1'
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
            title=u'test_unicode_äöü_menu_1_0',
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
            title=u'test_unicode_äöü_menu_item_1_0_0',
            order=0,
            blank_target=False,
            url='/about',
            menu=self.menu_1_0
        )
        self.menu_item_1_0_1 = MenuItem.objects.create(
            title=u'test_unicode_äöü_menu_item_1_0_1',
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
            u'No "{}" string expected in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_0.title,
            rendered,
            u'No "{}" string expected in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_1.title,
            rendered,
            u'No "{}" string expected in the rendered template'.format(
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
            u'Expected "{}" string in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_0.title,
            rendered,
            u'Expected "{}" string in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_1.title,
            rendered,
            u'Expected "{}" string in the rendered template'.format(
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
            u'No "{}" string expected in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_0.title,
            rendered,
            u'No "{}" string expected in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertNotIn(
            self.menu_item_1_0_1.title,
            rendered,
            u'No "{}" string expected in the rendered template'.format(
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
            u'Expected "{}" string in the rendered template'.format(
                self.menu_1_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_0.title,
            rendered,
            u'Expected "{}" string in the rendered template'.format(
                self.menu_item_1_0_0.title
            )
        )
        self.assertIn(
            self.menu_item_1_0_1.title,
            rendered,
            u'Expected "{}" string in the rendered template'.format(
                self.menu_item_1_0_1.title
            )
        )


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
        url_name = 'csw_global_dispatch'

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
