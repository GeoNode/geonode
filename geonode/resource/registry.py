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

from django.utils.module_loading import import_string

from geonode.base.models import ResourceBase
from geonode.resource.manager import BaseResourceManager
from geonode.resource.api.utils import resolve_type_serializer


from . import settings as rm_settings


class ResourceManagerRegistry:
    """Registry for concrete resource managers keyed by handled model class."""

    REGISTRY = {}

    def init_registry(self):
        self.reset()
        self._register()

    def add(self, manager):
        model_cls = getattr(manager, "handled_model", None)
        if model_cls is None:
            raise ValueError(f"Manager {manager.__class__.__name__} must define 'handled_model'")
        self.REGISTRY[model_cls] = manager

    def remove(self, model_cls):
        self.REGISTRY.pop(model_cls, None)

    def reset(self):
        self.REGISTRY = {}

    @classmethod
    def get_registry(cls):
        return ResourceManagerRegistry.REGISTRY

    def get_for_instance(self, instance):
        """
        Accepts either:
        - a model instance
        - a model class (Dataset, Document, ...)
        """
        if instance is None:
            raise ValueError("Cannot resolve manager for a null instance")

        if isinstance(instance, type):
            manager = self.REGISTRY.get(instance)
            if manager is not None:
                return manager
            if issubclass(instance, ResourceBase):
                return BaseResourceManager()
            raise ValueError("No resource manager registered for provided class")

        real = instance.get_real_instance() if hasattr(instance, "get_real_instance") else instance
        for model_cls, manager in self.REGISTRY.items():
            if isinstance(real, model_cls):
                return manager
        if isinstance(real, ResourceBase):
            return BaseResourceManager()
        raise ValueError("No resource manager registered for instance")

    def get_for_type(self, resource_type):
        """
        Accepts:
        - resource type string (e.g. 'dataset', 'map')
        - model class (Dataset, Map, ...)
        """
        if isinstance(resource_type, str):
            resource_type = resolve_type_serializer(resource_type)[0]
        return self.get_for_instance(resource_type)

    def get_for_uuid(self, uuid):
        """
        Accepts:
        - uuid of a resource
        """
        if not uuid:
            raise ValueError("Cannot resolve manager for empty uuid")
        rb = ResourceBase.objects.filter(uuid=uuid).first()
        if rb is None:
            raise ValueError(f"No ResourceBase found for uuid: {uuid}")
        return self.get_for_instance(rb)

    def _register(self):
        for module_path in rm_settings.RESOURCE_MANAGERS:
            manager_class = import_string(module_path)
            self.add(manager_class())


resource_manager_registry = ResourceManagerRegistry()
