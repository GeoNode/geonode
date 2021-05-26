# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import importlib
from . import settings as rm_settings

from abc import ABCMeta, abstractmethod
from geonode.base.models import ResourceBase


class ResourceManagerInterface(metaclass=ABCMeta):

    @abstractmethod
    def search(self, filter: dict) -> list:
        pass

    @abstractmethod
    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass

    @abstractmethod
    def delete(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass

    @abstractmethod
    def create(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass


class ResourceManager(ResourceManagerInterface):

    def __init__(self):
        self._resource_manager = self._get_concrete_manager()

    def _get_concrete_manager(self):
        module_name, class_name = rm_settings.RESOURCE_MANAGER_CONCRETE_CLASS.rsplit(".", 1)
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        return class_()

    def search(self, filter: dict) -> list:
        pass

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        _resources = ResourceBase.objects.filter(uuid=uuid)
        _exists = _resources.count() == 1
        if _exists:
            instance = _resources.get()
        _exists = self._resource_manager.exists(uuid, instance=instance)
        return _exists

    def delete(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass

    def create(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass


resource_manager = ResourceManager()
