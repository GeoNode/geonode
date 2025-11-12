#########################################################################
#
# Copyright (C) 2025 OSGeo
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


class BaseRequestConfigurationRuleHandler:
    """
    Base class for request configuration rule handlers.
    """

    def get_rules(self, user):
        return []


class RequestConfigurationRulesRegistry:
    """
    A registry for request configuration rule handlers.
    """

    REGISTRY = []

    def init_registry(self):
        self._register()
        self.sanity_checks()

    def add(self, module_path):
        item = import_string(module_path)
        self.__check_item(item)
        if item not in self.REGISTRY:
            self.REGISTRY.append(item)

    def remove(self, module_path):
        item = import_string(module_path)
        self.__check_item(item)
        if item in self.REGISTRY:
            self.REGISTRY.remove(item)

    def reset(self):
        self.REGISTRY = []

    @classmethod
    def get_registry(cls):
        return cls.REGISTRY

    def sanity_checks(self):
        for item in self.REGISTRY:
            self.__check_item(item)

    def get_rules(self, user):
        rules = []
        if user and user.is_authenticated:
            for HandlerClass in self.REGISTRY:
                handler = HandlerClass()
                rules.extend(handler.get_rules(user))
            return {"rules": rules}
        else:
            raise Exception("User must be authenticated to get request configuration rules")

    def __check_item(self, item):
        """
        Ensure that the handler is a subclass of BaseRequestConfigurationRuleHandler
        """
        if not (isinstance(item, type) and issubclass(item, BaseRequestConfigurationRuleHandler)):
            raise TypeError(f"Item must be a subclass of BaseRequestConfigurationRuleHandler, " f"got {item}")

    def _register(self):
        for module_path in getattr(settings, "REQUEST_CONFIGURATION_RULES_HANDLERS", []):
            self.add(module_path)


request_configuration_rules_registry = RequestConfigurationRulesRegistry()
