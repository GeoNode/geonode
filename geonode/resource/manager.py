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

from guardian.models import (
    UserObjectPermission,
    GroupObjectPermission)
from guardian.shortcuts import (
    assign_perm,
    get_anonymous_user)

from django.conf import settings
from django.db import transaction
from django.db.models.query import QuerySet
from django.contrib.auth.models import Group
from geonode.documents.models import Document
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType

from geonode.groups.conf import settings as groups_settings
from geonode.security.permissions import VIEW_PERMISSIONS
from geonode.security.utils import (
    get_user_groups,
    set_owner_permissions,
    get_obj_group_managers,
    skip_registered_members_common_group)

from . import settings as rm_settings
from .utils import (
    metadata_storers,
    resourcebase_post_save,
    update_resource)

from ..base import enumerations
from ..base.models import ResourceBase
from ..layers.metadata import parse_metadata
from ..layers.models import Layer

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
    def remove_permissions(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass

    @abstractmethod
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner=None, permissions: dict = {}, created: bool = False) -> bool:
        pass

    @abstractmethod
    def set_workflow_permissions(self, uuid: str, /, instance: ResourceBase = None, approved: bool = False, published: bool = False) -> bool:
        pass

    @abstractmethod
    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        pass

    @abstractmethod
    def append(self, instance: ResourceBase, vals: dict = {}):
        pass

    @abstractmethod
    def replace(self, instance: ResourceBase, vals: dict = {}):
        pass


class ResourceManager(ResourceManagerInterface):

    def __init__(self):
        self._concrete_resource_manager = self._get_concrete_manager()

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
        _filter = self._concrete_resource_manager.search(filter, type=_class)
        if _filter:
            _resources_queryset.filter(_filter)
        return _resources_queryset

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            return self._concrete_resource_manager.exists(uuid, instance=_resource)
        return False

    @transaction.atomic
    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            try:
                self._concrete_resource_manager.delete(uuid, instance=_resource)
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
                _resource = self._concrete_resource_manager.create(uuid, resource_type=resource_type, defaults=defaults)
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
                _resource = self._concrete_resource_manager.update(uuid, instance=_resource, notify=notify)
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
            if hasattr(self._concrete_resource_manager, method):
                _method = getattr(self._concrete_resource_manager, method)
                return _method(method, uuid, instance=_resource, **kwargs)
        return instance

    @transaction.atomic
    def remove_permissions(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        """Remove object permissions on given resource.
        If is a layer removes the layer specific permissions then the
        resourcebase permissions.
        """
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            try:
                logger.debug(f'Removing all permissions on {_resource}')
                from geonode.layers.models import Layer
                _layer = _resource.get_real_instance() if isinstance(_resource.get_real_instance(), Layer) else None
                if not _layer:
                    try:
                        _layer = _resource.layer if hasattr(_resource, "layer") else None
                    except Exception:
                        _layer = None
                if _layer:
                    UserObjectPermission.objects.filter(
                        content_type=ContentType.objects.get_for_model(_layer),
                        object_pk=instance.id
                    ).delete()
                    GroupObjectPermission.objects.filter(
                        content_type=ContentType.objects.get_for_model(_layer),
                        object_pk=instance.id
                    ).delete()
                UserObjectPermission.objects.filter(
                    content_type=ContentType.objects.get_for_model(_resource.get_self_resource()),
                    object_pk=instance.id).delete()
                GroupObjectPermission.objects.filter(
                    content_type=ContentType.objects.get_for_model(_resource.get_self_resource()),
                    object_pk=instance.id).delete()
                return self._concrete_resource_manager.remove_permissions(uuid, instance=_resource)
            except Exception as e:
                logger.exception(e)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False

    @transaction.atomic
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner=None, permissions: dict = {}, created: bool = False) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource = _resource.get_real_instance()
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            logger.debug(f'Finalizing (permissions and notifications) on resource {instance}')
            try:
                logger.debug(f'Setting permissions {permissions} on {_resource}')
                """
                Remove all the permissions except for the owner and assign the
                view permission to the anonymous group
                """
                self.remove_permissions(uuid, instance=_resource)
                if permissions is not None:
                    """
                    Sets an object's the permission levels based on the perm_spec JSON.

                    the mapping looks like:
                    {
                        'users': {
                            'AnonymousUser': ['view'],
                            <username>: ['perm1','perm2','perm3'],
                            <username2>: ['perm1','perm2','perm3']
                            ...
                        }
                        'groups': [
                            <groupname>: ['perm1','perm2','perm3'],
                            <groupname2>: ['perm1','perm2','perm3'],
                            ...
                            ]
                    }
                    """

                    # default permissions for resource owner
                    set_owner_permissions(_resource)

                    # Anonymous User group
                    if 'users' in permissions and "AnonymousUser" in permissions['users']:
                        anonymous_group = Group.objects.get(name='anonymous')
                        for perm in permissions['users']['AnonymousUser']:
                            if _resource.polymorphic_ctype.name == 'layer' and perm in (
                                    'change_layer_data', 'change_layer_style',
                                    'add_layer', 'change_layer', 'delete_layer',):
                                assign_perm(perm, anonymous_group, _resource.layer)
                            else:
                                assign_perm(perm, anonymous_group, _resource.get_self_resource())

                    # All the other users
                    if 'users' in permissions and len(permissions['users']) > 0:
                        for user, perms in permissions['users'].items():
                            _user = get_user_model().objects.get(username=user)
                            if _user != _resource.owner and user != "AnonymousUser":
                                for perm in perms:
                                    if _resource.polymorphic_ctype.name == 'layer' and perm in (
                                            'change_layer_data', 'change_layer_style',
                                            'add_layer', 'change_layer', 'delete_layer',):
                                        assign_perm(perm, _user, _resource.layer)
                                    else:
                                        assign_perm(perm, _user, _resource.get_self_resource())

                    # All the other groups
                    if 'groups' in permissions and len(permissions['groups']) > 0:
                        for group, perms in permissions['groups'].items():
                            _group = Group.objects.get(name=group)
                            for perm in perms:
                                if _resource.polymorphic_ctype.name == 'layer' and perm in (
                                        'change_layer_data', 'change_layer_style',
                                        'add_layer', 'change_layer', 'delete_layer',):
                                    assign_perm(perm, _group, _resource.layer)
                                else:
                                    assign_perm(perm, _group, _resource.get_self_resource())

                    # AnonymousUser
                    if 'users' in permissions and len(permissions['users']) > 0:
                        if "AnonymousUser" in permissions['users']:
                            _user = get_anonymous_user()
                            perms = permissions['users']["AnonymousUser"]
                            for perm in perms:
                                if _resource.polymorphic_ctype.name == 'layer' and perm in (
                                        'change_layer_data', 'change_layer_style',
                                        'add_layer', 'change_layer', 'delete_layer',):
                                    assign_perm(perm, _user, _resource.layer)
                                else:
                                    assign_perm(perm, _user, _resource.get_self_resource())
                else:
                    # default permissions for anonymous users
                    anonymous_group, created = Group.objects.get_or_create(name='anonymous')

                    # default permissions for owner
                    _owner = owner or _resource.owner

                    if not anonymous_group:
                        raise Exception("Could not acquire 'anonymous' Group.")

                    # default permissions for resource owner
                    set_owner_permissions(_resource, members=get_obj_group_managers(_owner))

                    # Anonymous
                    anonymous_can_view = settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION
                    if anonymous_can_view:
                        assign_perm('view_resourcebase',
                                    anonymous_group, _resource.get_self_resource())
                    else:
                        for user_group in get_user_groups(_owner):
                            if not skip_registered_members_common_group(user_group):
                                assign_perm('view_resourcebase',
                                            user_group, _resource.get_self_resource())

                    anonymous_can_download = settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION
                    if anonymous_can_download:
                        assign_perm('download_resourcebase',
                                    anonymous_group, _resource.get_self_resource())
                    else:
                        for user_group in get_user_groups(_owner):
                            if not skip_registered_members_common_group(user_group):
                                assign_perm('download_resourcebase',
                                            user_group, _resource.get_self_resource())

                    if _resource.__class__.__name__ == 'Layer':
                        # only for layer owner
                        assign_perm('change_layer_data', _owner, _resource)
                        assign_perm('change_layer_style', _owner, _resource)

                _resource.handle_moderated_uploads()
                return self._concrete_resource_manager.set_permissions(uuid, instance=_resource, owner=owner, permissions=permissions, created=created)
            except Exception as e:
                logger.exception(e)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False

    @transaction.atomic
    def set_workflow_permissions(self, uuid: str, /, instance: ResourceBase = None, approved: bool = False, published: bool = False) -> bool:
        """
                          |  N/PUBLISHED   | PUBLISHED
          --------------------------------------------
            N/APPROVED    |     GM/OWR     |     -
            APPROVED      |   registerd    |    all
          --------------------------------------------
        """
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            try:
                anonymous_group = Group.objects.get(name='anonymous')
                if approved:
                    if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
                        _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
                        _members_group_group = Group.objects.get(name=_members_group_name)
                        for perm in VIEW_PERMISSIONS:
                            assign_perm(perm,
                                        _members_group_group, _resource.get_self_resource())
                    else:
                        for perm in VIEW_PERMISSIONS:
                            assign_perm(perm,
                                        anonymous_group, _resource.get_self_resource())
                if published:
                    for perm in VIEW_PERMISSIONS:
                        assign_perm(perm,
                                    anonymous_group, _resource.get_self_resource())

                return self._concrete_resource_manager.set_workflow_permissions(uuid, instance=_resource, approved=approved, published=published)
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
                self._concrete_resource_manager.set_thumbnail(uuid, instance=_resource, overwrite=overwrite, check_bbox=check_bbox)
                return True
            except Exception as e:
                logger.exception(e)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False

    @transaction.atomic
    def append(self, instance: ResourceBase, vals: dict = {}):
        if self._validate_resource(instance, 'append'):
            self._concrete_resource_manager.append(instance, vals=vals)
            return self.update(instance.uuid, instance, vals=vals)

    @transaction.atomic
    def replace(self, instance: ResourceBase, vals: dict = {}):
        if self._validate_resource(instance, 'replace'):
            if vals.get('files', None):
                vals.update(storage_manager.replace(instance, vals.get('files')))
            self._concrete_resource_manager.replace(instance, vals=vals)
            return self.update(instance.uuid, instance, vals=vals)

    def _validate_resource(self, instance: ResourceBase, action_type: str) -> bool:
        if not isinstance(instance, Layer) and action_type == 'append':
            raise Exception("Append data is available only for Layers")

        if isinstance(instance, Document) and action_type == "replace":
            return True

        exists = self._concrete_resource_manager.exists(instance.uuid, instance)

        if exists and instance.is_vector() and action_type == "append":
            is_valid = True
        elif exists and action_type == "replace":
            is_valid = True
        else:
            raise ObjectDoesNotExist("Resource does not exists")
        return is_valid


resource_manager = ResourceManager()
