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
from geonode.upload.feature_validators import BaseFeatureValidator


class FeatureValidatorsRegistry:
    """
    A registry for feature validation.
    """

    REGISTRY = []
    HANDLERS = []

    def init_registry(self):
        self.reset()
        self._register()
        self.sanity_checks()

    def init_handlers(self, dataset):
        """
        Initializes the handlers with the given dataset.
        """
        self.HANDLERS = [HandlerClass(dataset) for HandlerClass in self.REGISTRY]

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
        self.HANDLERS = []

    @classmethod
    def get_registry(cls):
        return FeatureValidatorsRegistry.REGISTRY

    def sanity_checks(self):
        for item in self.REGISTRY:
            self.__check_item(item)

    def validate(self, feature):
        """
        Iterates over all registered handlers and validates the feature.
        """
        for handler in self.HANDLERS:
            handler.validate(feature)

    def __check_item(self, item):
        """
        Ensure that the handler is a subclass of BaseFeatureValidator
        """
        if not issubclass(item, BaseFeatureValidator):
            raise Exception(f"Handler {item} is not a subclass of BaseFeatureValidator")

    def _register(self):
        for module_path in settings.FEATURE_VALIDATORS:
            self.add(module_path)


feature_validators_registry = FeatureValidatorsRegistry()
