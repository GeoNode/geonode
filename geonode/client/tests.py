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

import os
import re

from geonode.tests.base import GeoNodeBaseTestSupport

from django.contrib.staticfiles import finders
from django.contrib.auth import get_user_model
from django.template.defaultfilters import slugify

from .models import GeoNodeThemeCustomization
from .utils import (find_all_templates,
                    activate_theme,
                    deactivate_theme,
                    theme_css_template,
                    theme_css_template_regexp,
                    theme_html_template,
                    theme_html_template_regexp,)


class ClientLibraryTest(GeoNodeBaseTestSupport):

    def setUp(self):
        super(GeoNodeBaseTestSupport, self).setUp()
        self.test_user = get_user_model().objects.create_user(
            "serviceowner", "usermail@fake.mail", "somepassword")
        self.geonode_base_css = finders.find('geonode/css/base.css')
        self.geonode_base_html = find_all_templates(pattern="geonode_base.html")

    def test_theme_customization_uuid(self):
        theme = GeoNodeThemeCustomization()
        try:
            theme.save()
            espected_uuid = slugify("theme id %s %s" % (theme.id, theme.date))
            self.assertEqual(espected_uuid, theme.theme_uuid)
            self.assertEqual(espected_uuid, theme.identifier)
        finally:
            theme.delete()

    def test_theme_activation_deactivation(self):

        self.assertTrue(os.path.isfile(self.geonode_base_css))
        self.assertTrue(os.path.isfile(self.geonode_base_html[0]))

        theme = GeoNodeThemeCustomization()
        theme_css = None
        try:
            theme.save()

            activate_theme(theme)
            self.assertTrue(theme.is_enabled)

            theme_css = os.path.join(os.path.dirname(self.geonode_base_css), "%s.css" % theme.theme_uuid)
            self.assertTrue(os.path.isfile(theme_css))

            with open(self.geonode_base_css, 'r') as base_css:
                value = base_css.read()
                theme_regexp = re.compile(theme_css_template_regexp.format(theme.theme_uuid))
                self.assertIsNotNone(theme_regexp.search(value))
                self.assertTrue(value.startswith(theme_css_template.format(theme.theme_uuid)))

                base_css.close()

            with open(self.geonode_base_html[0], 'r') as base_html:
                value = base_html.read()
                theme_regexp = re.compile(theme_html_template_regexp.format(theme.theme_uuid))
                self.assertIsNotNone(theme_regexp.search(value))
                self.assertTrue(value.startswith(theme_html_template.format(theme.theme_uuid)))

                base_html.close()

            deactivate_theme(theme)
            self.assertFalse(theme.is_enabled)
            self.assertIsNotNone(theme_css)
            self.assertFalse(os.path.isfile(theme_css))

            with open(self.geonode_base_css, 'r') as base_css:
                value = base_css.read()
                theme_regexp = re.compile(theme_css_template_regexp.format(theme.theme_uuid))
                self.assertIsNone(theme_regexp.search(value))
                base_css.close()

            with open(self.geonode_base_html[0], 'r') as base_html:
                value = base_html.read()
                theme_regexp = re.compile(theme_html_template_regexp.format(theme.theme_uuid))
                self.assertIsNone(theme_regexp.search(value))
                base_html.close()
        finally:
            theme.delete()

            self.assertIsNotNone(theme_css)
            self.assertFalse(os.path.isfile(theme_css))
