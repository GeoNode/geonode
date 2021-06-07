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

from uuid import uuid1
from abc import ABCMeta, abstractmethod

from django.db import transaction
from django.db.models.query import QuerySet
from django.core.exceptions import ValidationError

from . import settings as rm_settings
from .utils import (
    metadata_storers,
    resourcebase_post_save,
    update_resource)

from ..base import enumerations
from ..base.models import ResourceBase
from ..layers.metadata import parse_metadata

from ..storage.manager import storage_manager

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
    def create(self, uuid: str, /, resource_type: object = None, defaults: dict = {}) -> ResourceBase:
        pass

    @abstractmethod
    def update(self, uuid: str, /, instance: ResourceBase = None, xml_file: str = None, metadata_uploaded: bool = False,
               vals: dict = {}, regions: dict = {}, keywords: dict = {}, custom: dict = {}, notify: bool = True) -> ResourceBase:
        pass

    @abstractmethod
    def exec(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        pass

    @abstractmethod
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, permissions: dict = {}, created: bool = False) -> bool:
        pass

    @abstractmethod
    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        pass


class ResourceManager(ResourceManagerInterface):

    def __init__(self):
        self._gs_resource_manager = self._get_concrete_manager()

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
        _filter = self._gs_resource_manager.search(filter, type=_class)
        if _filter:
            _resources_queryset.filter(_filter)
        return _resources_queryset

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            return self._gs_resource_manager.exists(uuid, instance=_resource)
        return False

    @transaction.atomic
    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            try:
                self._gs_resource_manager.delete(uuid, instance=_resource)
                _resource.get_real_instance().delete()
                return 1
            except Exception as e:
                logger.exception(e)
        return 0

    @transaction.atomic
    def create(self, uuid: str, /, resource_type: object = None, defaults: dict = {}) -> ResourceBase:
        if resource_type.objects.filter(uuid=uuid).exists():
            raise ValidationError(f'Object of type {resource_type} with uuid [{uuid}] already exists.')
        uuid = uuid or str(uuid1())
        _resource, _created = resource_type.objects.get_or_create(
            uuid=uuid,
            defaults=defaults)
        if _resource and _created:
            try:
                _resource.set_processing_state(enumerations.STATE_RUNNING)
                _resource.set_missing_info()
                _resource = self._gs_resource_manager.create(uuid, resource_type=resource_type, defaults=defaults)
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
            except Exception as e:
                _resource.delete()
                raise e
            resourcebase_post_save(_resource)
        return _resource

    @transaction.atomic
    def update(self, uuid: str, /, instance: ResourceBase = None, xml_file: str = None, metadata_uploaded: bool = False,
               vals: dict = {}, regions: list = [], keywords: list = [], custom: dict = {}, notify: bool = True) -> ResourceBase:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            _resource.set_missing_info()
            _resource.metadata_uploaded = metadata_uploaded
            logger.debug(f'Look for xml and finalize Layer metadata {_resource}')
            try:
                if metadata_uploaded and xml_file:
                    _md_file = None
                    try:
                        _md_file = storage_manager.open(xml_file)
                    except Exception as e:
                        logger.exception(e)
                        _md_file = open(xml_file)

                    _resource.metadata_xml = _md_file.read()

                    _uuid, vals, regions, keywords, custom = parse_metadata(_md_file.read())
                    if uuid and uuid != _uuid:
                        raise ValidationError("The UUID identifier from the XML Metadata is different from the {_resource} one.")
                    else:
                        uuid = _uuid

                logger.debug(f'Update Layer with information coming from XML File if available {_resource}')

                _resource = update_resource(instance=_resource.get_real_instance(), regions=regions, keywords=keywords, vals=vals)

                _resource = self._gs_resource_manager.update(uuid, instance=_resource, notify=notify)

                _resource = metadata_storers(_resource.get_real_instance(), custom)
            except Exception as e:
                logger.exception(e)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
                _resource.save(notify=notify)
            resourcebase_post_save(_resource)
        return _resource

    @transaction.atomic
    def exec(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            if hasattr(self._gs_resource_manager, method):
                _method = getattr(self._gs_resource_manager, method)
                return _method(method, uuid, instance=_resource, **kwargs)
        return instance

    @transaction.atomic
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, permissions: dict = {}, created: bool = False) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            logger.debug(f'Finalizing (permissions and notifications) Layer {instance}')
            try:
                logger.debug(f'Setting permissions {permissions} for {_resource.name}')
                if permissions is not None:
                    _resource.get_real_instance().set_permissions(permissions, created=created)
                    self._gs_resource_manager.set_permissions(uuid, instance=_resource, permissions=permissions, created=created)
                else:
                    _resource.get_real_instance().set_default_permissions()
                _resource.handle_moderated_uploads()
                return True
            except Exception as e:
                logger.exception(e)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False

    @transaction.atomic
    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            try:
                self._gs_resource_manager.set_thumbnail(uuid, instance=_resource, overwrite=overwrite, check_bbox=check_bbox)
                return True
            except Exception as e:
                logger.exception(e)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False


resource_manager = ResourceManager()
