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
import logging
import importlib

from django.core.exceptions import ValidationError
from . import settings as rm_settings

from django.db import transaction
from django.db.models.query import QuerySet

from abc import ABCMeta, abstractmethod
from geonode.base.models import ResourceBase

logger = logging.getLogger(__name__)


class ResourceManagerInterface(metaclass=ABCMeta):

    @abstractmethod
    def search(self, filter: dict, /, type: object = None) -> QuerySet:
        pass

    @abstractmethod
    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass

    @abstractmethod
    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        pass

    @abstractmethod
    def create(self, uuid: str, /, type: object = None, defaults: dict = {}) -> int:
        pass

    @abstractmethod
    def update(self, uuid: str, /, instance: ResourceBase = None, vals: dict = {}, regions: dict = {}, keywords: dict = {}, custom: dict = {}, notify: bool = True) -> int:
        pass

    @abstractmethod
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, permissions: dict = {}) -> bool:
        pass

    @abstractmethod
    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        pass


class ResourceManager(ResourceManagerInterface):

    def __init__(self):
        self._resource_manager = self._get_concrete_manager()

    def _get_concrete_manager(self):
        module_name, class_name = rm_settings.RESOURCE_MANAGER_CONCRETE_CLASS.rsplit(".", 1)
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        return class_()

    @classmethod
    def _get_instance(cls, uuid: str) -> ResourceBase:
        _resources = ResourceBase.objects.filter(uuid=uuid)
        _exists = _resources.count() == 1
        if _exists:
            return _resources.get()
        return None

    def search(self, filter: dict, /, type: object = None) -> QuerySet:
        _class = type or ResourceBase
        _resources_queryset = _class.objects.filter(**filter)
        _filter = self._resource_manager.search(filter, type=_class)
        if _filter:
            _resources_queryset.filter(_filter)
        return _resources_queryset

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        instance = instance or ResourceManager._get_instance(uuid)
        if instance:
            return self._resource_manager.exists(uuid, instance=instance)
        return False

    @transaction.atomic
    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        instance = instance or ResourceManager._get_instance(uuid)
        if instance:
            try:
                self._resource_manager.delete(uuid, instance=instance)
                instance.get_real_instance().delete()
                return 1
            except Exception as e:
                logger.exception(e)
        return 0

    @transaction.atomic
    def create(self, uuid: str, /, type: object = None, defaults: dict = {}) -> int:
        if type.objects.filter(uuid=uuid).exists():
            raise ValidationError(f'Object of type {type} with uuid [{uuid}] already exists.')
        _resource, _created = type.objects.get_or_create(
            uuid=uuid,
            defaults=defaults)
        if _resource and _created:
            try:
                self._resource_manager.create(uuid, type=type, defaults=defaults)
                return 1
            except Exception as e:
                logger.exception(e)
                _resource.delete()
        return 0

    @transaction.atomic
    def update(self, uuid: str, /, instance: ResourceBase = None, vals: dict = {}, regions: dict = {}, keywords: dict = {}, custom: dict = {}, notify: bool = True) -> int:
        pass

    @transaction.atomic
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, permissions: dict = {}) -> bool:
        instance = instance or ResourceManager._get_instance(uuid)
        if instance and permissions is not None:
            try:
                logger.debug(f'Setting permissions {permissions} for {instance.name}')
                instance.get_real_instance().set_permissions(permissions, created=False)
                self._resource_manager.set_permissions(uuid, instance=instance, permissions=permissions)
                return True
            except Exception as e:
                logger.exception(e)
        return False

    @transaction.atomic
    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        pass


resource_manager = ResourceManager()
