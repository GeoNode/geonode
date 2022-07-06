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

import os
import copy
import typing
import logging
import importlib

from uuid import uuid1, uuid4
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
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import (
    ObjectDoesNotExist,
    ValidationError,
    FieldDoesNotExist)

from geonode.thumbs.thumbnails import _generate_thumbnail_name
from geonode.documents.tasks import create_document_thumbnail
from geonode.security.permissions import (
    PermSpecCompact,
    DATA_STYLABLE_RESOURCES_SUBTYPES)
from geonode.security.utils import (
    perms_as_set,
    get_user_groups,
    skip_registered_members_common_group)

from . import settings as rm_settings
from .utils import (
    update_resource,
    metadata_storers,
    resourcebase_post_save)

from ..base import enumerations
from ..base.models import ResourceBase
from ..security.utils import AdvancedSecurityWorkflowManager
from ..layers.metadata import parse_metadata
from ..documents.models import Document, DocumentResourceLink
from ..layers.models import Dataset, Attribute
from ..maps.models import Map
from ..storage.manager import storage_manager

logger = logging.getLogger(__name__)


class ResourceManagerInterface(metaclass=ABCMeta):

    @abstractmethod
    def search(self, filter: dict, /, resource_type: typing.Optional[object]) -> QuerySet:
        """Returns a QuerySet of the filtered resources into the DB.

         - The 'filter' parameter should be an dictionary with the filtering criteria;
           - 'filter' = None won't return any result
           - 'filter' = {} will return the whole set
         - The 'resource_type' parameter allows to specify the concrete resource model (e.g. Dataset, Document, Map, ...)
           - 'resource_type' must be a class
           - 'resource_type' = Dataset will return a set of the only available Layers
        """
        pass

    @abstractmethod
    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        """Returns 'True' or 'False' if the resource exists or not.

         - If 'instance' is provided, it will take precedence on 'uuid'
         - The existance criteria might be subject to the 'concrete resource manager' one, dependent on the resource type
           e.g.: a local Dataset existance check will be constrained by the existance of the layer on the GIS backend
        """
        pass

    @abstractmethod
    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        """Deletes a resource from the DB.

         - If 'instance' is provided, it will take precedence on 'uuid'
         - It will also fallback to the 'concrete resource manager' delete model.
         - This will eventually delete the related resources on the GIS backend too.
        """
        pass

    @abstractmethod
    def create(self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}) -> ResourceBase:
        """The method will just create a new 'resource_type' on the DB model and invoke the 'post save' triggers.

         - It assumes any GIS backend resource (e.g. layers on GeoServer) already exist.
         - It is possible to pass initial default values, like the 'files' from the 'storage_manager' trhgouh the 'defaults' dictionary
        """
        pass

    @abstractmethod
    def update(self, uuid: str, /, instance: ResourceBase = None, xml_file: str = None, metadata_uploaded: bool = False,
               vals: dict = {}, regions: dict = {}, keywords: dict = {}, custom: dict = {}, notify: bool = True) -> ResourceBase:
        """The method will update an existing 'resource_type' on the DB model and invoke the 'post save' triggers.

         - It assumes any GIS backend resource (e.g. layers on GeoServer) already exist.
         - It is possible to pass initial default values, like the 'files' from the 'storage_manager' trhgouh the 'vals' dictionary
         - The 'xml_file' parameter allows to fetch metadata values from a file
         - The 'notify' parameter allows to notify the members that the resource has been updated
        """
        pass

    @abstractmethod
    def ingest(self, files: typing.List[str], /, uuid: str = None, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs) -> ResourceBase:
        """The method allows to create a resource by providing the list of files.

        e.g.:
            In [1]: from geonode.resource.manager import resource_manager

            In [2]: from geonode.layers.models import Dataset

            In [3]: from django.contrib.auth import get_user_model

            In [4]: admin = get_user_model().objects.get(username='admin')

            In [5]: files = ["/.../san_andres_y_providencia_administrative.dbf", "/.../san_andres_y_providencia_administrative.prj",
            ...:  "/.../san_andres_y_providencia_administrative.shx", "/.../san_andres_y_providencia_administrative.sld", "/.../san_andres_y_providencia_administrative.shp"]

            In [6]: resource_manager.ingest(files, resource_type=Dataset, defaults={'owner': admin})
        """
        pass

    @abstractmethod
    def copy(self, instance: ResourceBase, /, uuid: str = None, owner: settings.AUTH_USER_MODEL = None, defaults: dict = {}) -> ResourceBase:
        """The method makes a copy of the existing resource.

         - It makes a copy of the files
         - It creates a new layer on the GIS backend in the case the ResourceType is a Dataset
        """
        pass

    @abstractmethod
    def append(self, instance: ResourceBase, vals: dict = {}) -> ResourceBase:
        """The method appends data to an existing resource.

         - It assumes any GIS backend resource (e.g. layers on GeoServer) already exist.
        """
        pass

    @abstractmethod
    def replace(self, instance: ResourceBase, vals: dict = {}) -> ResourceBase:
        """The method replaces data of an existing resource.

         - It assumes any GIS backend resource (e.g. layers on GeoServer) already exist.
        """
        pass

    @abstractmethod
    def exec(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        """A generic 'exec' method allowing to invoke specific methods of the concrete resource manager not exposed by the interface.

         - The parameter 'method' represents the actual name of the concrete method to invoke.
        """
        pass

    @abstractmethod
    def remove_permissions(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        """Completely cleans the permissions of a resource, resetting it to the default state (owner only)
        """
        pass

    @abstractmethod
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner: settings.AUTH_USER_MODEL = None, permissions: dict = {}, created: bool = False,
                        approval_status_changed: bool = False, group_status_changed: bool = False) -> bool:
        """Sets the permissions of a resource.

         - It optionally gets a JSON 'perm_spec' through the 'permissions' parameter
         - If no 'perm_spec' is provided, it will set the default permissions (owner only)
        """
        pass

    @abstractmethod
    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        """Allows to generate or re-generate the Thumbnail of a Resource."""
        pass


class ResourceManager(ResourceManagerInterface):

    def __init__(self, concrete_manager=None):
        self._concrete_resource_manager = concrete_manager or self._get_concrete_manager()

    def _get_concrete_manager(self):
        module_name, class_name = rm_settings.RESOURCE_MANAGER_CONCRETE_CLASS.rsplit(".", 1)
        module = importlib.import_module(module_name)
        class_ = getattr(module, class_name)
        return class_()

    @classmethod
    def _get_instance(cls, uuid: str) -> ResourceBase:
        return ResourceBase.objects.filter(uuid=uuid).first()

    def search(self, filter: dict, /, resource_type: typing.Optional[object]) -> QuerySet:
        _class = resource_type or ResourceBase
        _resources_queryset = _class.objects.filter(**filter)
        _filter = self._concrete_resource_manager.search(filter, resource_type=_class)
        if _filter:
            _resources_queryset.filter(_filter)
        return _resources_queryset

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            return self._concrete_resource_manager.exists(uuid, instance=_resource)
        return False

    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        _resource = instance or ResourceManager._get_instance(uuid)
        uuid = uuid or _resource.uuid
        if _resource and ResourceBase.objects.filter(uuid=uuid).exists():
            try:
                _resource.set_processing_state(enumerations.STATE_RUNNING)
                try:
                    if isinstance(_resource.get_real_instance(), Dataset):
                        """
                        - Remove any associated style to the dataset, if it is not used by other datasets.
                        - Default style will be deleted in post_delete_dataset.
                        - Remove the dataset from any associated map, if any.
                        - Remove the dataset default style.
                        """
                        try:
                            from geonode.maps.models import MapLayer
                            logger.debug(
                                "Going to delete associated maplayers for [%s]", _resource.get_real_instance().name)
                            MapLayer.objects.filter(
                                name=_resource.get_real_instance().alternate,
                                ows_url=_resource.get_real_instance().ows_url).delete()
                        except Exception as e:
                            logger.exception(e)

                        try:
                            from pinax.ratings.models import OverallRating
                            ct = ContentType.objects.get_for_model(_resource.get_real_instance())
                            OverallRating.objects.filter(
                                content_type=ct,
                                object_id=_resource.get_real_instance().id).delete()
                        except Exception as e:
                            logger.exception(e)

                        # Remove uploaded files, if any
                        ResourceBase.objects.cleanup_uploaded_files(resource_id=_resource.id)

                        try:
                            _resource.get_real_instance().styles.delete()
                            _resource.get_real_instance().default_style.delete()
                        except Exception as e:
                            logger.debug(f"Error occurred while trying to delete the Dataset Styles: {e}")
                        self.remove_permissions(_resource.get_real_instance().uuid, instance=_resource.get_real_instance())
                except Exception as e:
                    logger.exception(e)

                try:
                    from ..services.models import Service

                    if _resource.remote_typename and Service.objects.filter(name=_resource.remote_typename).exists():
                        _service = Service.objects.filter(name=_resource.remote_typename).get()
                        if _service.harvester:
                            _service.harvester.harvestable_resources.filter(
                                geonode_resource__uuid=_resource.get_real_instance().uuid).update(should_be_harvested=False)
                except Exception as e:
                    logger.exception(e)

                self._concrete_resource_manager.delete(uuid, instance=_resource)
                try:
                    _resource.get_real_instance().delete()
                except ResourceBase.DoesNotExist:
                    pass
                return 1
            except Exception as e:
                logger.exception(e)
            finally:
                ResourceBase.objects.filter(uuid=uuid).delete()
        return 0

    def create(self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}) -> ResourceBase:
        if resource_type.objects.filter(uuid=uuid).exists():
            return resource_type.objects.filter(uuid=uuid).get()
        uuid = uuid or str(uuid4())
        _resource, _created = resource_type.objects.get_or_create(
            uuid=uuid,
            defaults=defaults)
        if _resource and _created:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            try:
                with transaction.atomic():
                    _resource.set_missing_info()
                    _resource = self._concrete_resource_manager.create(uuid, resource_type=resource_type, defaults=defaults)
                _resource.save()
                resourcebase_post_save(_resource.get_real_instance())
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
            except Exception as e:
                logger.exception(e)
                self.delete(_resource.uuid, instance=_resource)
                raise e
        return _resource

    def update(self, uuid: str, /, instance: ResourceBase = None, xml_file: str = None, metadata_uploaded: bool = False,
               vals: dict = {}, regions: list = [], keywords: list = [], custom: dict = {}, notify: bool = True, extra_metadata: list = [],
               *args, **kwargs) -> ResourceBase:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            _resource.set_missing_info()
            _resource.metadata_uploaded = metadata_uploaded
            logger.debug(f'Look for xml and finalize Dataset metadata {_resource}')
            try:
                with transaction.atomic():
                    if metadata_uploaded and xml_file:
                        _md_file = None
                        try:
                            _md_file = storage_manager.open(xml_file, mode='r')
                        except Exception as e:
                            logger.exception(e)
                            if os.path.exists(xml_file) and os.path.isfile(xml_file):
                                _md_file = open(xml_file, mode='r')
                        if _md_file:
                            _md_file_content = _md_file.read()
                            _resource.metadata_xml = _md_file_content
                            _uuid, vals, regions, keywords, custom = parse_metadata(_md_file_content)
                            if uuid and uuid != _uuid:
                                raise ValidationError("The UUID identifier from the XML Metadata is different from the {_resource} one.")
                            else:
                                uuid = _uuid

                    logger.debug(f'Update Dataset with information coming from XML File if available {_resource}')

                    if not kwargs.get("store_spatial_files", True) and vals.get('files', []):
                        vals.update({"files": []})

                    _resource.save()
                    _resource = update_resource(
                        instance=_resource.get_real_instance(),
                        regions=regions,
                        keywords=keywords,
                        vals=vals,
                        extra_metadata=extra_metadata
                    )
                    _resource = self._concrete_resource_manager.update(uuid, instance=_resource, notify=notify)
                    _resource = metadata_storers(_resource.get_real_instance(), custom)

                    # The following is only a demo proof of concept for a pluggable WF subsystem
                    from geonode.resource.processing.models import ProcessingWorkflow
                    _p = ProcessingWorkflow.objects.first()
                    if _p and _p.is_enabled:
                        for _task in _p.get_tasks():
                            _task.execute(_resource)
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
                raise
            finally:
                try:
                    _resource.save(notify=notify)
                    resourcebase_post_save(_resource.get_real_instance())
                    _resource.set_permissions(
                        created=False,
                        approval_status_changed=(vals is not None and any([x in vals for x in ['is_approved', 'is_published']])),
                        group_status_changed=(vals is not None and 'group' in vals)
                    )
                    if kwargs.get('sld_file', False) and kwargs.get('sld_uploaded', False):
                        self._concrete_resource_manager.set_style(
                            method="",
                            uuid=_resource.uuid,
                            resource=_resource,
                            sld_file=kwargs.get('sld_file', False),
                            sld_uploaded=kwargs.get('sld_uploaded', False)
                        )
                        _resource.set_permissions()
                    if _resource.state != enumerations.STATE_INVALID:
                        _resource.set_processing_state(enumerations.STATE_PROCESSED)
                except Exception as e:
                    logger.exception(e)
                finally:
                    _resource.clear_dirty_state()
        return _resource

    def ingest(self, files: typing.List[str], /, uuid: str = None, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs) -> ResourceBase:
        instance = None
        to_update = defaults.copy()
        if 'files' in to_update:
            to_update.pop('files')
        try:
            with transaction.atomic():
                if resource_type == Document:
                    if 'name' in to_update:
                        to_update.pop("name")
                    if files:
                        to_update['files'] = storage_manager.copy_files_list(files)
                    instance = self.create(
                        uuid,
                        resource_type=Document,
                        defaults=to_update
                    )
                elif resource_type == Dataset:
                    if files:
                        instance = self.create(
                            uuid,
                            resource_type=Dataset,
                            defaults=to_update)
                if instance:
                    instance = self._concrete_resource_manager.ingest(
                        storage_manager.copy_files_list(files),
                        uuid=instance.uuid,
                        resource_type=resource_type,
                        defaults=to_update,
                        **kwargs)
                    instance.set_processing_state(enumerations.STATE_PROCESSED)
                    instance.save(notify=False)
        except Exception as e:
            logger.exception(e)
            if instance:
                instance.set_processing_state(enumerations.STATE_INVALID)
        if instance:
            try:
                resourcebase_post_save(instance.get_real_instance())
                # Finalize Upload
                if 'user' in to_update:
                    to_update.pop('user')
                instance = self.update(instance.uuid, instance=instance, vals=to_update)
                self.set_thumbnail(instance.uuid, instance=instance)
            except Exception as e:
                logger.exception(e)
            finally:
                instance.clear_dirty_state()
        return instance

    def copy(self, instance: ResourceBase, /, uuid: str = None, owner: settings.AUTH_USER_MODEL = None, defaults: dict = {}) -> ResourceBase:
        _resource = None
        if instance:
            try:
                instance.set_processing_state(enumerations.STATE_RUNNING)
                with transaction.atomic():
                    _owner = owner or instance.get_real_instance().owner
                    _perms = copy.copy(instance.get_real_instance().get_all_level_info())
                    _resource = copy.copy(instance.get_real_instance())
                    _resource.pk = _resource.id = None
                    _resource.uuid = uuid or str(uuid4())
                    try:
                        # Avoid Integrity errors...
                        _resource.get_real_instance()._meta.get_field('name')
                        _name = defaults.get('name', _resource.get_real_instance().name)
                        _resource.get_real_instance().name = defaults['name'] = f'{_name}_{uuid1().hex[:8]}'
                    except FieldDoesNotExist:
                        if 'name' in defaults:
                            defaults.pop('name')
                    _resource.save()
                    if isinstance(instance.get_real_instance(), Document):
                        for resource_link in DocumentResourceLink.objects.filter(document=instance.get_real_instance()):
                            _resource_link = copy.copy(resource_link)
                            _resource_link.pk = _resource_link.id = None
                            _resource_link.document = _resource.get_real_instance()
                            _resource_link.save()
                    if isinstance(instance.get_real_instance(), Dataset):
                        for attribute in Attribute.objects.filter(dataset=instance.get_real_instance()):
                            _attribute = copy.copy(attribute)
                            _attribute.pk = _attribute.id = None
                            _attribute.dataset = _resource.get_real_instance()
                            _attribute.save()
                    if isinstance(instance.get_real_instance(), Map):
                        for maplayer in instance.get_real_instance().maplayers.iterator():
                            _maplayer = copy.copy(maplayer)
                            _maplayer.pk = _maplayer.id = None
                            _maplayer.map = _resource.get_real_instance()
                            _maplayer.save()
                    to_update = {}
                    try:
                        to_update = storage_manager.copy(_resource).copy()
                    except Exception as e:
                        logger.exception(e)

                    _resource = self._concrete_resource_manager.copy(instance, uuid=_resource.uuid, defaults=to_update)

            except Exception as e:
                logger.exception(e)
                _resource = None
            finally:
                instance.set_processing_state(enumerations.STATE_PROCESSED)
                instance.save(notify=False)
            if _resource:
                try:
                    to_update.update(defaults)
                    if 'user' in to_update:
                        to_update.pop('user')
                    # We need to remove any public access to the cloned dataset here
                    if 'users' in _perms and ("AnonymousUser" in _perms['users'] or get_anonymous_user() in _perms['users']):
                        anonymous_user = "AnonymousUser" if "AnonymousUser" in _perms['users'] else get_anonymous_user()
                        _perms['users'].pop(anonymous_user)
                    if 'groups' in _perms and ("anonymous" in _perms['groups'] or Group.objects.get(name='anonymous') in _perms['groups']):
                        anonymous_group = 'anonymous' if 'anonymous' in _perms['groups'] else Group.objects.get(name='anonymous')
                        _perms['groups'].pop(anonymous_group)
                    self.set_permissions(_resource.uuid, instance=_resource, owner=_owner, permissions=_perms)
                    # Refresh from DB
                    _resource.refresh_from_db()
                    return self.update(_resource.uuid, _resource, vals=to_update)
                except Exception as e:
                    logger.exception(e)
                finally:
                    _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return _resource

    def append(self, instance: ResourceBase, vals: dict = {}, *args, **kwargs):
        if self._validate_resource(instance.get_real_instance(), 'append'):
            self._concrete_resource_manager.append(instance.get_real_instance(), vals=vals)
            to_update = vals.copy()
            if instance:
                if 'user' in to_update:
                    to_update.pop('user')
                return self.update(instance.uuid, instance.get_real_instance(), vals=to_update, *args, **kwargs)
        return instance

    def replace(self, instance: ResourceBase, vals: dict = {}, *args, **kwargs):
        if self._validate_resource(instance.get_real_instance(), 'replace'):
            if vals.get('files', None) and kwargs.get('store_spatial_files', True):
                vals.update(storage_manager.replace(instance.get_real_instance(), vals.get('files')))
            self._concrete_resource_manager.replace(instance.get_real_instance(), vals=vals, *args, **kwargs)
            to_update = vals.copy()
            if instance:
                if 'user' in to_update:
                    to_update.pop('user')
                return self.update(instance.uuid, instance.get_real_instance(), vals=to_update, *args, **kwargs)
        return instance

    def _validate_resource(self, instance: ResourceBase, action_type: str) -> bool:
        if not isinstance(instance, Dataset) and action_type == 'append':
            raise Exception("Append data is available only for Layers")

        if isinstance(instance, Document) and action_type == "replace":
            return True

        exists = self._concrete_resource_manager.exists(instance.uuid, instance)

        if exists and action_type == "append":
            if isinstance(instance, Dataset):
                if instance.is_vector():
                    is_valid = True
        elif exists and action_type == "replace":
            is_valid = True
        else:
            raise ObjectDoesNotExist("Resource does not exists")
        return is_valid

    @transaction.atomic
    def exec(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            if hasattr(self._concrete_resource_manager, method):
                _method = getattr(self._concrete_resource_manager, method)
                return _method(method, uuid, instance=_resource, **kwargs)
        return instance

    def remove_permissions(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        """Remove object permissions on given resource.
        If is a layer removes the layer specific permissions then the
        resourcebase permissions.
        """
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            try:
                with transaction.atomic():
                    logger.debug(f'Removing all permissions on {_resource}')
                    from geonode.layers.models import Dataset
                    _dataset = _resource.get_real_instance() if isinstance(_resource.get_real_instance(), Dataset) else None
                    if not _dataset:
                        try:
                            _dataset = _resource.dataset if hasattr(_resource, "dataset") else None
                        except Exception:
                            _dataset = None
                    if _dataset:
                        UserObjectPermission.objects.filter(
                            content_type=ContentType.objects.get_for_model(_dataset),
                            object_pk=_resource.id
                        ).delete()
                        GroupObjectPermission.objects.filter(
                            content_type=ContentType.objects.get_for_model(_dataset),
                            object_pk=_resource.id
                        ).delete()
                    UserObjectPermission.objects.filter(
                        content_type=ContentType.objects.get_for_model(_resource.get_self_resource()),
                        object_pk=_resource.id).delete()
                    GroupObjectPermission.objects.filter(
                        content_type=ContentType.objects.get_for_model(_resource.get_self_resource()),
                        object_pk=_resource.id).delete()
                    if not self._concrete_resource_manager.remove_permissions(uuid, instance=_resource):
                        raise Exception("Could not complete concrete manager operation successfully!")
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
                return True
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
            finally:
                _resource.clear_dirty_state()
        return False

    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner: settings.AUTH_USER_MODEL = None, permissions: dict = {}, created: bool = False,
                        approval_status_changed: bool = False, group_status_changed: bool = False) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource = _resource.get_real_instance()
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            logger.debug(f'Finalizing (permissions and notifications) on resource {instance}')
            try:
                with transaction.atomic():
                    logger.debug(f'Setting permissions {permissions} on {_resource}')

                    # default permissions for owner
                    if owner and owner != _resource.owner:
                        _resource.owner = owner
                        ResourceBase.objects.filter(uuid=_resource.uuid).update(owner=owner)
                    _owner = _resource.owner
                    _resource_type = getattr(_resource, 'resource_type', None) or _resource.polymorphic_ctype.name
                    _resource_subtype = (getattr(_resource, 'subtype', None) or '').lower()

                    # default permissions for anonymous users
                    anonymous_group, _ = Group.objects.get_or_create(name='anonymous')

                    if not anonymous_group:
                        raise Exception("Could not acquire 'anonymous' Group.")

                    # Gathering and validating the current permissions (if any has been passed)
                    if not created and permissions is None:
                        permissions = _resource.get_all_level_info()

                    if permissions:
                        if PermSpecCompact.validate(permissions):
                            _permissions = PermSpecCompact(copy.deepcopy(permissions), _resource).extended
                        else:
                            _permissions = copy.deepcopy(permissions)
                    else:
                        _permissions = None

                    # Fixup Advanced Workflow permissions
                    _perm_spec = AdvancedSecurityWorkflowManager.get_permissions(
                        _resource.uuid, instance=_resource, permissions=_permissions, created=created,
                        approval_status_changed=approval_status_changed, group_status_changed=group_status_changed)

                    """
                    Cleanup the Guardian tables
                    """
                    self.remove_permissions(uuid, instance=_resource)

                    def _safe_assign_perm(perm, user_or_group, obj=None):
                        try:
                            assign_perm(perm, user_or_group, obj)
                        except Permission.DoesNotExist as e:
                            logger.warn(e)

                    if permissions is not None and len(permissions):
                        """
                        Sets an object's the permission levels based on the perm_spec JSON.

                        the mapping looks like:
                        {
                            'users': {
                                'AnonymousUser': ['view'],
                                <username>: ['perm1','perm2','perm3'],
                                <username2>: ['perm1','perm2','perm3']
                                ...
                            },
                            'groups': [
                                <groupname>: ['perm1','perm2','perm3'],
                                <groupname2>: ['perm1','perm2','perm3'],
                                ...
                            ]
                        }
                        """
                        # Anonymous User group
                        if 'users' in _perm_spec and ("AnonymousUser" in _perm_spec['users'] or get_anonymous_user() in _perm_spec['users']):
                            anonymous_user = "AnonymousUser" if "AnonymousUser" in _perm_spec['users'] else get_anonymous_user()
                            perms = copy.deepcopy(_perm_spec['users'][anonymous_user])
                            _perm_spec['users'].pop(anonymous_user)
                            _prev_perm = _perm_spec["groups"].get(anonymous_group, []) if "groups" in _perm_spec else []
                            _perm_spec["groups"][anonymous_group] = set.union(perms_as_set(_prev_perm), perms_as_set(perms))
                            for perm in _perm_spec["groups"][anonymous_group]:
                                if _resource_type == 'dataset' and perm in (
                                        'change_dataset_data', 'change_dataset_style',
                                        'add_dataset', 'change_dataset', 'delete_dataset'):
                                    if perm == 'change_dataset_style' and _resource_subtype not in DATA_STYLABLE_RESOURCES_SUBTYPES:
                                        pass
                                    else:
                                        _safe_assign_perm(perm, anonymous_group, _resource.dataset)
                                elif AdvancedSecurityWorkflowManager.assignable_perm_condition(perm, _resource_type):
                                    _safe_assign_perm(perm, anonymous_group, _resource.get_self_resource())

                        # All the other users
                        if 'users' in _perm_spec and len(_perm_spec['users']) > 0:
                            for user, perms in _perm_spec['users'].items():
                                _user = get_user_model().objects.get(username=user)
                                if user != "AnonymousUser" and user != get_anonymous_user():
                                    for perm in perms:
                                        if _resource_type == 'dataset' and perm in (
                                                'change_dataset_data', 'change_dataset_style',
                                                'add_dataset', 'change_dataset', 'delete_dataset'):
                                            if perm == 'change_dataset_style' and _resource_subtype not in DATA_STYLABLE_RESOURCES_SUBTYPES:
                                                pass
                                            else:
                                                _safe_assign_perm(perm, _user, _resource.dataset)
                                        elif AdvancedSecurityWorkflowManager.assignable_perm_condition(perm, _resource_type):
                                            _safe_assign_perm(perm, _user, _resource.get_self_resource())

                        # All the other groups
                        if 'groups' in _perm_spec and len(_perm_spec['groups']) > 0:
                            for group, perms in _perm_spec['groups'].items():
                                _group = Group.objects.get(name=group)
                                for perm in perms:
                                    if _resource_type == 'dataset' and perm in (
                                            'change_dataset_data', 'change_dataset_style',
                                            'add_dataset', 'change_dataset', 'delete_dataset'):
                                        if perm == 'change_dataset_style' and _resource_subtype not in DATA_STYLABLE_RESOURCES_SUBTYPES:
                                            pass
                                        else:
                                            _safe_assign_perm(perm, _group, _resource.dataset)
                                    elif AdvancedSecurityWorkflowManager.assignable_perm_condition(perm, _resource_type):
                                        _safe_assign_perm(perm, _group, _resource.get_self_resource())

                        # AnonymousUser
                        if 'users' in _perm_spec and len(_perm_spec['users']) > 0:
                            if "AnonymousUser" in _perm_spec['users'] or get_anonymous_user() in _perm_spec['users']:
                                _user = get_anonymous_user()
                                anonymous_user = "AnonymousUser" if "AnonymousUser" in _perm_spec['users'] else get_anonymous_user()
                                perms = _perm_spec['users'][anonymous_user]
                                for perm in perms:
                                    if _resource_type == 'dataset' and perm in (
                                            'change_dataset_data', 'change_dataset_style',
                                            'add_dataset', 'change_dataset', 'delete_dataset'):
                                        if perm == 'change_dataset_style' and _resource_subtype not in DATA_STYLABLE_RESOURCES_SUBTYPES:
                                            pass
                                        else:
                                            _safe_assign_perm(perm, _user, _resource.dataset)
                                    elif AdvancedSecurityWorkflowManager.assignable_perm_condition(perm, _resource_type):
                                        _safe_assign_perm(perm, _user, _resource.get_self_resource())
                    else:
                        # Anonymous
                        if AdvancedSecurityWorkflowManager.is_anonymous_can_view():
                            _safe_assign_perm('view_resourcebase', anonymous_group, _resource.get_self_resource())
                            _prev_perm = _perm_spec["groups"].get(anonymous_group, []) if "groups" in _perm_spec else []
                            _perm_spec["groups"][anonymous_group] = set.union(perms_as_set(_prev_perm), perms_as_set('view_resourcebase'))
                        else:
                            for user_group in get_user_groups(_owner):
                                if not skip_registered_members_common_group(user_group):
                                    _safe_assign_perm('view_resourcebase', user_group, _resource.get_self_resource())
                                    _prev_perm = _perm_spec["groups"].get(user_group, []) if "groups" in _perm_spec else []
                                    _perm_spec["groups"][user_group] = set.union(perms_as_set(_prev_perm), perms_as_set('view_resourcebase'))

                        if AdvancedSecurityWorkflowManager.assignable_perm_condition('download_resourcebase', _resource_type):
                            if AdvancedSecurityWorkflowManager.is_anonymous_can_download():
                                _safe_assign_perm('download_resourcebase', anonymous_group, _resource.get_self_resource())
                                _prev_perm = _perm_spec["groups"].get(anonymous_group, []) if "groups" in _perm_spec else []
                                _perm_spec["groups"][anonymous_group] = set.union(perms_as_set(_prev_perm), perms_as_set('download_resourcebase'))
                            else:
                                for user_group in get_user_groups(_owner):
                                    if not skip_registered_members_common_group(user_group):
                                        _safe_assign_perm('download_resourcebase', user_group, _resource.get_self_resource())
                                        _prev_perm = _perm_spec["groups"].get(user_group, []) if "groups" in _perm_spec else []
                                        _perm_spec["groups"][user_group] = set.union(perms_as_set(_prev_perm), perms_as_set('download_resourcebase'))

                        if _resource_type == 'dataset':
                            # only for layer owner
                            _safe_assign_perm('change_dataset_data', _owner, _resource)
                            _safe_assign_perm('change_dataset_style', _owner, _resource)
                            _prev_perm = _perm_spec["users"].get(_owner, []) if "users" in _perm_spec else []
                            _perm_spec["users"][_owner] = set.union(perms_as_set(_prev_perm), perms_as_set(['change_dataset_data', 'change_dataset_style']))

                        _resource = AdvancedSecurityWorkflowManager.handle_moderated_uploads(_resource.uuid, instance=_resource)

                    # Fixup GIS Backend Security Rules Accordingly
                    if not self._concrete_resource_manager.set_permissions(
                            uuid, instance=_resource, owner=owner, permissions=_resource.get_all_level_info(), created=created):
                        # This might not be a severe error. E.g. for datasets outside of local GeoServer
                        logger.error(Exception("Could not complete concrete manager operation successfully!"))
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
                return True
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
            finally:
                _resource.clear_dirty_state()
        return False

    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True, thumbnail=None) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            try:
                with transaction.atomic():
                    if thumbnail:
                        file_name = _generate_thumbnail_name(_resource.get_real_instance())
                        _resource.save_thumbnail(file_name, thumbnail)
                    else:
                        if instance and instance.files and isinstance(instance.get_real_instance(), Document):
                            if overwrite or not instance.thumbnail_url:
                                create_document_thumbnail.apply((instance.id,))
                        self._concrete_resource_manager.set_thumbnail(uuid, instance=_resource, overwrite=overwrite, check_bbox=check_bbox)
                return True
            except Exception as e:
                logger.exception(e)
        return False


resource_manager = ResourceManager()
