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
import logging
import typing

from django import forms
from django.conf import settings
from django.utils.module_loading import import_string

from geonode.security.auth_registry import auth_handler_registry
from geonode.sources.base import BaseSourceProvider, Capability

logger = logging.getLogger(__name__)


class SourceProviderRegistry:
    """
    Source providers installed from settings.SOURCE_PROVIDERS, keyed by provider key
    """

    REGISTRY = {}

    def init_registry(self):
        self.reset()
        for module_path in getattr(settings, "SOURCE_PROVIDERS", []):
            self.add(import_string(module_path))
        self.sanity_checks()

    def add(self, provider_cls):
        if not issubclass(provider_cls, BaseSourceProvider):
            raise TypeError(f"{provider_cls} is not a BaseSourceProvider")
        _provider = provider_cls()
        if _provider.key in self.REGISTRY:
            logger.warning(f"Source provider '{_provider.key}' is registered twice, {_provider} wins")
        self.REGISTRY[_provider.key] = _provider

    def remove(self, key):
        self.REGISTRY.pop(key, None)

    def reset(self):
        self.REGISTRY.clear()

    def sanity_checks(self):
        for key, _provider in self.REGISTRY.items():
            if not key:
                raise ValueError(f"Source provider {_provider} has no key")
            if not isinstance(_provider.declared_capabilities, Capability):
                raise ValueError(f"Source provider {_provider} must declare its capabilities as a Capability")
            if not (_provider.connection_form and issubclass(_provider.connection_form, forms.Form)):
                raise ValueError(f"Source provider {_provider} must define its connection_form")
            # the connection of a provider is an AuthConfig of the same type, it needs a handler to be read
            if not auth_handler_registry.get_handler_class(key):
                raise ValueError(f"Source provider {_provider} has no auth handler for type '{key}'")

    def get(self, key) -> typing.Optional[BaseSourceProvider]:
        return self.REGISTRY.get(key)

    @property
    def keys(self) -> typing.List[str]:
        return list(self.REGISTRY.keys())


source_provider_registry = SourceProviderRegistry()
