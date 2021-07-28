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
import copy
import typing
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
from django.templatetags.static import static
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType

from geonode.documents.models import Document
from geonode.security.permissions import VIEW_PERMISSIONS
from geonode.groups.conf import settings as groups_settings
from geonode.security.utils import (
    get_user_groups,
    set_owner_permissions,
    get_obj_group_managers,
    skip_registered_members_common_group)

from . import settings as rm_settings
from .utils import (
    update_resource,
    metadata_storers,
    resourcebase_post_save)

from ..base import enumerations
from ..base.models import ResourceBase
from ..layers.metadata import parse_metadata
from ..layers.models import Dataset

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
    def copy(self, instance: ResourceBase, /, uuid: str = None, defaults: dict = {}) -> ResourceBase:
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
    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner: settings.AUTH_USER_MODEL = None, permissions: dict = {}, created: bool = False) -> bool:
        """Sets the permissions of a resource.

         - It optionally gets a JSON 'perm_spec' through the 'permissions' parameter
         - If no 'perm_spec' is provided, it will set the default permissions (owner only)
        """
        pass

    @abstractmethod
    def set_workflow_permissions(self, uuid: str, /, instance: ResourceBase = None, approved: bool = False, published: bool = False) -> bool:
        """Fix-up the permissions of a Resource accordingly to the currently active advanced workflow configuraiton"""
        pass

    @abstractmethod
    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        """Allows to generate or re-generate the Thumbnail of a Resource."""
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

    @transaction.atomic
    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource and ResourceBase.objects.filter(uuid=uuid).exists():
            try:
                self._concrete_resource_manager.delete(uuid, instance=_resource)
                if isinstance(_resource.get_real_instance(), Dataset):
                    """
                    - Remove any associated style to the layer, if it is not used by other layers.
                    - Default style will be deleted in post_delete_dataset.
                    - Remove the layer from any associated map, if any.
                    - Remove the layer default style.
                    """
                    try:
                        if _resource.get_real_instance().remote_service is not None:
                            from geonode.services.models import HarvestJob
                            _resource_id = _resource.get_real_instance().alternate
                            HarvestJob.objects.filter(
                                service=_resource.get_real_instance().remote_service, resource_id=_resource_id).delete()
                            _resource_id = _resource.get_real_instance().alternate.split(":")[-1] if len(_resource.get_real_instance().alternate.split(":")) else None
                            if _resource_id:
                                HarvestJob.objects.filter(
                                    service=_resource.get_real_instance().remote_service, resource_id=_resource_id).delete()
                    except Exception as e:
                        logger.exception(e)

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

                    try:
                        if 'geonode.upload' in settings.INSTALLED_APPS and \
                                settings.UPLOADER['BACKEND'] == 'geonode.importer':
                            from geonode.upload.models import Upload
                            # Need to call delete one by one in ordee to invoke the
                            #  'delete' overridden method
                            for upload in Upload.objects.filter(resource_id=_resource.get_real_instance().id):
                                upload.delete()
                    except Exception as e:
                        logger.exception(e)

                    try:
                        _resource.get_real_instance().styles.delete()
                        _resource.get_real_instance().default_style.delete()
                    except Exception as e:
                        logger.debug(f"Error occurred while trying to delete the Dataset Styles: {e}")

                self.remove_permissions(_resource.get_real_instance().uuid, instance=_resource.get_real_instance())
                try:
                    _resource.get_real_instance().delete()
                except ResourceBase.DoesNotExist:
                    pass
                return 1
            except Exception as e:
                logger.exception(e)
        return 0

    def create(self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}) -> ResourceBase:
        if resource_type.objects.filter(uuid=uuid).exists():
            raise ValidationError(f'Object of type {resource_type} with uuid [{uuid}] already exists.')
        uuid = uuid or str(uuid1())
        _resource, _created = resource_type.objects.get_or_create(
            uuid=uuid,
            defaults=defaults)
        if _resource and _created:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            try:
                with transaction.atomic():
                    _resource.set_missing_info()
                    _resource = self._concrete_resource_manager.create(uuid, resource_type=resource_type, defaults=defaults)
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
                _resource.delete()
                raise e
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
            resourcebase_post_save(_resource.get_real_instance())
        return _resource

    def update(self, uuid: str, /, instance: ResourceBase = None, xml_file: str = None, metadata_uploaded: bool = False,
               vals: dict = {}, regions: list = [], keywords: list = [], custom: dict = {}, notify: bool = True) -> ResourceBase:
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

                    logger.debug(f'Update Dataset with information coming from XML File if available {_resource}')
                    _resource.save()
                    _resource = update_resource(instance=_resource.get_real_instance(), regions=regions, keywords=keywords, vals=vals)
                    _resource = self._concrete_resource_manager.update(uuid, instance=_resource, notify=notify)
                    _resource = metadata_storers(_resource.get_real_instance(), custom)

                    # The following is only a demo proof of concept for a pluggable WF subsystem
                    from geonode.resource.processing.models import ProcessingWorkflow
                    _p = ProcessingWorkflow.objects.first()
                    if _p and _p.is_enabled:
                        for _task in _p.get_tasks():
                            _task.execute(_resource)
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
                _resource.save(notify=notify)
            resourcebase_post_save(_resource.get_real_instance())
        return _resource

    def ingest(self, files: typing.List[str], /, uuid: str = None, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs) -> ResourceBase:
        instance = None
        to_update = defaults.copy()
        if 'files' in to_update:
            to_update.pop('files')
        try:
            with transaction.atomic():
                if resource_type == Document:
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
                instance = self._concrete_resource_manager.ingest(
                    storage_manager.copy_files_list(files),
                    uuid=instance.uuid,
                    resource_type=resource_type,
                    defaults=to_update,
                    **kwargs)
        except Exception as e:
            logger.exception(e)
            instance.set_processing_state(enumerations.STATE_INVALID)
        finally:
            instance.set_processing_state(enumerations.STATE_PROCESSED)
            instance.save(notify=False)
        resourcebase_post_save(instance.get_real_instance())
        # Finalize Upload
        if 'user' in to_update:
            to_update.pop('user')
        instance = self.update(instance.uuid, instance=instance, vals=to_update)
        self.set_thumbnail(instance.uuid, instance=instance)
        return instance

    def copy(self, instance: ResourceBase, /, uuid: str = None, defaults: dict = {}) -> ResourceBase:
        if instance:
            try:
                with transaction.atomic():
                    _owner = instance.owner
                    _perms = instance.get_all_level_info()
                    _resource = copy.copy(instance)
                    _resource.pk = _resource.id = None
                    _resource.uuid = uuid or str(uuid1())
                    _resource.save()
                    to_update = defaults.copy()
                    to_update.update(storage_manager.copy(_resource))
                    self._concrete_resource_manager.copy(_resource, uuid=_resource.uuid, defaults=to_update)
                    if _resource:
                        if 'user' in to_update:
                            to_update.pop('user')
                        self.set_permissions(_resource.uuid, instance=_resource, owner=_owner, permissions=_perms)
                        return self.update(_resource.uuid, _resource, vals=to_update)
            except Exception as e:
                logger.exception(e)
                instance.set_processing_state(enumerations.STATE_INVALID)
            finally:
                instance.set_processing_state(enumerations.STATE_PROCESSED)
                instance.save(notify=False)
            resourcebase_post_save(instance.get_real_instance())
        return instance

    def append(self, instance: ResourceBase, vals: dict = {}):
        if self._validate_resource(instance, 'append'):
            self._concrete_resource_manager.append(instance, vals=vals)
            to_update = vals.copy()
            if instance:
                if 'user' in to_update:
                    to_update.pop('user')
                return self.update(instance.uuid, instance, vals=to_update)
        return instance

    def replace(self, instance: ResourceBase, vals: dict = {}):
        if self._validate_resource(instance, 'replace'):
            if vals.get('files', None):
                vals.update(storage_manager.replace(instance, vals.get('files')))
            self._concrete_resource_manager.replace(instance, vals=vals)
            to_update = vals.copy()
            if instance:
                if 'user' in to_update:
                    to_update.pop('user')
                return self.update(instance.uuid, instance, vals=to_update)
        return instance

    def _validate_resource(self, instance: ResourceBase, action_type: str) -> bool:
        if not isinstance(instance, Dataset) and action_type == 'append':
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
                            _dataset = _resource.dataset if hasattr(_resource, "layer") else None
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
                    return self._concrete_resource_manager.remove_permissions(uuid, instance=_resource)
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False

    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner: settings.AUTH_USER_MODEL = None, permissions: dict = {}, created: bool = False) -> bool:
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
                        set_owner_permissions(_resource, members=get_obj_group_managers(_owner))

                        # Anonymous User group
                        if 'users' in permissions and "AnonymousUser" in permissions['users']:
                            anonymous_group = Group.objects.get(name='anonymous')
                            for perm in permissions['users']['AnonymousUser']:
                                if _resource.polymorphic_ctype.name == 'dataset' and perm in (
                                        'change_dataset_data', 'change_dataset_style',
                                        'add_dataset', 'change_dataset', 'delete_dataset',):
                                    assign_perm(perm, anonymous_group, _resource.dataset)
                                else:
                                    assign_perm(perm, anonymous_group, _resource.get_self_resource())

                        # All the other users
                        if 'users' in permissions and len(permissions['users']) > 0:
                            for user, perms in permissions['users'].items():
                                _user = get_user_model().objects.get(username=user)
                                if _user != _resource.owner and user != "AnonymousUser":
                                    for perm in perms:
                                        if _resource.polymorphic_ctype.name == 'dataset' and perm in (
                                                'change_dataset_data', 'change_dataset_style',
                                                'add_dataset', 'change_dataset', 'delete_dataset',):
                                            assign_perm(perm, _user, _resource.dataset)
                                        else:
                                            assign_perm(perm, _user, _resource.get_self_resource())

                        # All the other groups
                        if 'groups' in permissions and len(permissions['groups']) > 0:
                            for group, perms in permissions['groups'].items():
                                _group = Group.objects.get(name=group)
                                for perm in perms:
                                    if _resource.polymorphic_ctype.name == 'dataset' and perm in (
                                            'change_dataset_data', 'change_dataset_style',
                                            'add_dataset', 'change_dataset', 'delete_dataset',):
                                        assign_perm(perm, _group, _resource.dataset)
                                    else:
                                        assign_perm(perm, _group, _resource.get_self_resource())

                        # AnonymousUser
                        if 'users' in permissions and len(permissions['users']) > 0:
                            if "AnonymousUser" in permissions['users']:
                                _user = get_anonymous_user()
                                perms = permissions['users']["AnonymousUser"]
                                for perm in perms:
                                    if _resource.polymorphic_ctype.name == 'dataset' and perm in (
                                            'change_dataset_data', 'change_dataset_style',
                                            'add_dataset', 'change_dataset', 'delete_dataset',):
                                        assign_perm(perm, _user, _resource.dataset)
                                    else:
                                        assign_perm(perm, _user, _resource.get_self_resource())
                    else:
                        # default permissions for anonymous users
                        anonymous_group, created = Group.objects.get_or_create(name='anonymous')

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

                        if _resource.__class__.__name__ == 'Dataset':
                            # only for layer owner
                            assign_perm('change_dataset_data', _owner, _resource)
                            assign_perm('change_dataset_style', _owner, _resource)

                    _resource.handle_moderated_uploads()
                    return self._concrete_resource_manager.set_permissions(uuid, instance=_resource, owner=owner, permissions=permissions, created=created)
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False

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
                with transaction.atomic():
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
                _resource.set_processing_state(enumerations.STATE_INVALID)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False

    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)
        if _resource:
            _resource.set_processing_state(enumerations.STATE_RUNNING)
            try:
                with transaction.atomic():
                    if instance and instance.files and isinstance(instance.get_real_instance(), Document):
                        if overwrite or instance.thumbnail_url == static(settings.MISSING_THUMBNAIL):
                            from geonode.documents.tasks import create_document_thumbnail
                            create_document_thumbnail.apply((instance.id,))
                    self._concrete_resource_manager.set_thumbnail(uuid, instance=_resource, overwrite=overwrite, check_bbox=check_bbox)
                    return True
            except Exception as e:
                logger.exception(e)
                _resource.set_processing_state(enumerations.STATE_INVALID)
            finally:
                _resource.set_processing_state(enumerations.STATE_PROCESSED)
        return False


resource_manager = ResourceManager()
