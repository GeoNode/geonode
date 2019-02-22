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

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.base.models import (
    ResourceBase, MenuPlaceholder, Menu, MenuItem
)
from django.template import Template, Context


class ThumbnailTests(GeoNodeBaseTestSupport):

    def setUp(self):
        super(ThumbnailTests, self).setUp()
        self.rb = ResourceBase.objects.create()

    def test_initial_behavior(self):
        self.assertFalse(self.rb.has_thumbnail())
        missing = self.rb.get_thumbnail_url()
        self.assertEquals('/static/geonode/img/missing_thumb.png', missing)


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
            name='test_menu_placeholder_1'
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
            title='test_menu_1_0',
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
            title='test_menu_item_1_0_0',
            order=0,
            blank_target=False,
            url='/about',
            menu=self.menu_1_0
        )
        self.menu_item_1_0_1 = MenuItem.objects.create(
            title='test_menu_item_1_0_1',
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
            "{% load base_tags %} {% get_menu 'test_menu_placeholder_1' %}"
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
            "{% load base_tags %} {% render_nav_menu 'test_menu_placeholder_1' %}"
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
