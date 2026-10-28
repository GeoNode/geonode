#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from django import forms
from django.test import TestCase

from geonode.sources.base import BaseSourceProvider, Capability
from geonode.sources.registry import source_provider_registry


class DummyForm(forms.Form):
    name = forms.CharField()


class DummyProvider(BaseSourceProvider):
    key = "dummy"
    declared_capabilities = Capability.READ
    connection_form = DummyForm

    def test_connection(self, auth_config):
        return True, ""

    def browse(self, auth_config):
        return []


class NoFormProvider(DummyProvider):
    key = "noform"
    connection_form = None


class SourceProviderRegistryTests(TestCase):
    def tearDown(self):
        source_provider_registry.init_registry()

    def test_add_should_refuse_classes_that_are_not_providers(self):
        with self.assertRaises(TypeError):
            source_provider_registry.add(DummyForm)

    def test_sanity_checks_should_fail_without_a_connection_form(self):
        source_provider_registry.add(NoFormProvider)
        with self.assertRaisesRegex(ValueError, "connection_form"):
            source_provider_registry.sanity_checks()

    def test_sanity_checks_should_fail_without_an_auth_handler(self):
        """The connection of a provider is an AuthConfig of the same type: without a handler it cannot be read"""
        source_provider_registry.add(DummyProvider)
        with self.assertRaisesRegex(ValueError, "auth handler"):
            source_provider_registry.sanity_checks()
