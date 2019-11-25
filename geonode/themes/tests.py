# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

from .models import GeoNodeThemeCustomization


class ThemeLibraryTest(GeoNodeBaseTestSupport):

    def test_theme_customization(self):
        # By default, the homepage should use default welcome text
        response = self.client.get('/')
        self.assertContains(response, "GeoNode is an open source platform for sharing geospatial data and maps.")

        # Creating a theme should change the welcome text
        GeoNodeThemeCustomization.objects.create(
            name='theme_1',
            jumbotron_welcome_content='welcome_1',
            is_enabled=True,
        )
        response = self.client.get('/')
        self.assertNotContains(response, "GeoNode is an open source platform for sharing geospatial data and maps.")
        self.assertContains(response, "welcome_1")

        # Creating another theme should replace the welcome text
        GeoNodeThemeCustomization.objects.create(
            name='theme_2',
            jumbotron_welcome_content='welcome_2',
            is_enabled=True,
        )
        response = self.client.get('/')
        self.assertNotContains(response, "welcome_1")
        self.assertContains(response, "welcome_2")

        # Creating a disabled theme should not replace the welcome text
        theme_3 = GeoNodeThemeCustomization.objects.create(
            name='theme_3',
            jumbotron_welcome_content='welcome_3',
            is_enabled=False,
        )
        response = self.client.get('/')
        self.assertNotContains(response, "welcome_3")
        self.assertContains(response, "welcome_2")

        # Playing a bit with colors
        theme_3.search_bg_color = "#000001"
        theme_3.search_title_color = "#000002"
        theme_3.search_link_color = "#000003"
        theme_3.footer_text_color = "#000004"
        theme_3.footer_href_color = "#000005"

        # Enabling that theme afterwards should replace the welcome text
        theme_3.is_enabled = True
        theme_3.save()
        response = self.client.get('/')
        self.assertNotContains(response, "welcome_2")
        self.assertContains(response, "welcome_3")
        self.assertContains(response, "background: %s;" % theme_3.search_bg_color)
        self.assertContains(response, "color: %s;" % theme_3.search_title_color)
        self.assertContains(response, "color: %s;" % theme_3.search_link_color)
        self.assertContains(response, "color: %s;" % theme_3.footer_text_color)
        self.assertContains(response, "color: %s;" % theme_3.footer_href_color)

        # We should have only one active theme
        active_themes = GeoNodeThemeCustomization.objects.filter(is_enabled=True)
        self.assertEqual(active_themes.count(), 1)

        # Deleting that theme should revert to default
        theme_3.delete()
        response = self.client.get('/')
        self.assertNotContains(response, "welcome_3")
        self.assertContains(response, "GeoNode is an open source platform for sharing geospatial data and maps.")
