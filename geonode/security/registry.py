#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from geonode.security.handlers import BasePermissionsHandler


class PermissionsHandlerRegistry:

    REGISTRY = []

    def init_registry(self):
        self._register()
        self.sanity_checks()

    def add(self, module_path):
        item = import_string(module_path)()
        self.__check_item(item)
        self.REGISTRY.append(item)

    def reset(self):
        self.REGISTRY = []

    def _register(self):
        for module_path in settings.PERMISSIONS_HANDLERS:
            self.add(module_path)

    def sanity_checks(self):
        for item in self.REGISTRY:
            self.__check_item(item)

    def __check_item(self, item):
        """
        Ensure that the handler is a subclass of BasePermissionsHandler
        """
        if not isinstance(item, BasePermissionsHandler):
            raise Exception(f"Handler {item} is not a subclass of BasePermissionsHandler")

    def fixup_perms(self, instance, payload, *args, **kwargs):
        for handler in self.REGISTRY:
            payload = handler.fixup_perms(instance, payload, *args, **kwargs)
        return payload

    @classmethod
    def get_registry(cls):
        return PermissionsHandlerRegistry.REGISTRY


permissions_registry = PermissionsHandlerRegistry()
