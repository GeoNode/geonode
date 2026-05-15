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
from django.conf import settings
from django.utils.module_loading import import_string


class AuthHandlerRegistry:
    def __init__(self):
        self.registry = {}

    def register(self, auth_handler_cls):
        handled_type = auth_handler_cls.handled_type
        if handled_type is None:
            raise ValueError("Auth handler class must define handled_type")
        self.registry[handled_type] = auth_handler_cls

    def init_registry(self):
        for auth_handler_path in getattr(settings, "AUTH_HANDLERS", []):
            auth_handler_cls = import_string(auth_handler_path)
            self.register(auth_handler_cls)

    def get_handler_class(self, handled_type):
        if not self.registry:
            self.init_registry()
        return self.registry.get(handled_type)

    def build(self, config):
        auth_handler_cls = self.get_handler_class(config.type)
        if auth_handler_cls is None:
            raise ValueError(f"Unsupported auth config type '{config.type}'")
        return auth_handler_cls(config)


auth_handler_registry = AuthHandlerRegistry()
