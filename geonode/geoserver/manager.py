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

import typing
import logging
import tempfile


from django.conf import settings
from django.db.models.query import QuerySet
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from geonode.maps.models import Map
from geonode.layers.models import Dataset
from geonode.base.models import ResourceBase
from geonode.utils import get_dataset_workspace
from geonode.services.enumerations import CASCADED
from geonode.security.utils import skip_registered_members_common_group
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    OWNER_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    DATASET_ADMIN_PERMISSIONS,
)
from geonode.resource.manager import ResourceManager, ResourceManagerInterface
from geonode.geoserver.signals import geofence_rule_assign
from .geofence import AutoPriorityBatch
from .tasks import geoserver_set_style, geoserver_delete_map, geoserver_create_style, geoserver_cascading_delete
from .helpers import (
    gs_catalog,
    set_time_info,
    ogc_server_settings,
    sync_instance_with_geoserver,
    create_gs_thumbnail,
    geofence,
    gf_utils,
)
from .security import (
    _get_gwc_filters_and_formats,
    toggle_dataset_cache,
    invalidate_geofence_cache,
    has_geolimits,
    create_geofence_rules,
)

logger = logging.getLogger(__name__)


class GeoServerResourceManager(ResourceManagerInterface):
    def search(self, filter: dict, /, resource_type: typing.Optional[object]) -> QuerySet:
        return resource_type.objects.none()

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        if instance:
            _real_instance = instance.get_real_instance()
            if hasattr(_real_instance, "subtype") and _real_instance.subtype not in ["tileStore", "remote"]:
                try:
                    logger.debug(f"Searching GeoServer for layer '{_real_instance.alternate}'")
                    # Let's reset the connections first
                    gs_catalog._cache.clear()
                    gs_catalog.reset()
                    if gs_catalog.get_layer(_real_instance.alternate):
                        return True
                except Exception as e:
                    logger.debug(e)
                    return False
            return True
        return False

    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        """Removes the layer from GeoServer"""
        # cascading_delete should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if instance and getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            try:
                _real_instance = instance.get_real_instance()
                if (
                    isinstance(_real_instance, Dataset)
                    and hasattr(_real_instance, "alternate")
                    and _real_instance.alternate
                ):
                    if (
                        not hasattr(_real_instance, "remote_service")
                        or _real_instance.remote_service is None
                        or _real_instance.remote_service.method == CASCADED
                    ):
                        geoserver_cascading_delete.apply_async(args=(_real_instance.alternate,), expiration=30)
                elif isinstance(_real_instance, Map):
                    geoserver_delete_map.apply_async(args=(_real_instance.id,), expiration=30)
            except Exception as e:
                logger.exception(e)

    def create(self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}) -> ResourceBase:
        _resource = resource_type.objects.get(uuid=uuid)
        if resource_type == Dataset:
            _synced_resource = sync_instance_with_geoserver(_resource.id)
            _resource = _synced_resource or _resource
        return _resource

    def update(
        self,
        uuid: str,
        /,
        instance: ResourceBase = None,
        xml_file: str = None,
        metadata_uploaded: bool = False,
        vals: dict = {},
        regions: dict = {},
        keywords: dict = {},
        custom: dict = {},
        notify: bool = True,
        **kwargs,
    ) -> ResourceBase:
        if instance:
            if isinstance(instance.get_real_instance(), Dataset):
                _synced_resource = sync_instance_with_geoserver(instance.id)
                instance = _synced_resource or instance
        return instance

    def remove_permissions(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        instance = instance or ResourceManager._get_instance(uuid)

        try:
            if instance and isinstance(instance.get_real_instance(), Dataset):
                if settings.OGC_SERVER["default"]["GEOFENCE_SECURITY_ENABLED"]:
                    if not getattr(settings, "DELAYED_SECURITY_SIGNALS", False):
                        workspace = get_dataset_workspace(instance)
                        removed = gf_utils.delete_layer_rules(workspace, instance.name)
                        if removed:
                            invalidate_geofence_cache()
                    else:
                        instance.set_dirty_state()
        except Exception as e:
            logger.exception(e)
            return False
        return True

    def set_permissions(
        self,
        uuid: str,
        /,
        instance: ResourceBase = None,
        owner: settings.AUTH_USER_MODEL = None,
        permissions: dict = {},
        created: bool = False,
        approval_status_changed: bool = False,
        group_status_changed: bool = False,
    ) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)

        try:
            if _resource:
                _resource = _resource.get_real_instance()
                logger.info(f'Requesting GeoFence rules on resource "{_resource}" :: {type(_resource).__name__}')
                if isinstance(_resource, Dataset):
                    if settings.OGC_SERVER["default"].get("GEOFENCE_SECURITY_ENABLED", False) or getattr(
                        settings, "GEOFENCE_SECURITY_ENABLED", False
                    ):
                        if not getattr(settings, "DELAYED_SECURITY_SIGNALS", False):
                            batch = AutoPriorityBatch(
                                gf_utils.get_first_available_priority(), f"Set permission for resource {_resource}"
                            )

                            workspace = get_dataset_workspace(_resource)

                            if not created:
                                gf_utils.collect_delete_layer_rules(workspace, _resource.name, batch)

                            exist_geolimits = None
                            _owner = owner or _resource.owner

                            if permissions is not None and len(permissions):
                                # Owner
                                perms = (
                                    OWNER_PERMISSIONS.copy()
                                    + DATASET_ADMIN_PERMISSIONS.copy()
                                    + DOWNLOAD_PERMISSIONS.copy()
                                )
                                create_geofence_rules(_resource, perms, _owner, None, batch)
                                exist_geolimits = exist_geolimits or has_geolimits(_resource, _owner, None)

                                deferred_anon_perms = []

                                # All the other users
                                if "users" in permissions and len(permissions["users"]) > 0:
                                    for user, user_perms in permissions["users"].items():
                                        _user = get_user_model().objects.get(username=user)
                                        if _user != _owner:
                                            if user == "AnonymousUser":
                                                _user = None
                                                deferred_anon_perms.append(user_perms)
                                            else:
                                                create_geofence_rules(_resource, user_perms, _user, None, batch)
                                            exist_geolimits = exist_geolimits or has_geolimits(_resource, _user, None)

                                # All the other groups
                                if "groups" in permissions and len(permissions["groups"]) > 0:
                                    for group, perms in permissions["groups"].items():
                                        _group = Group.objects.get(name=group)
                                        if _group and _group.name and _group.name == "anonymous":
                                            _group = None
                                            deferred_anon_perms.append(perms)
                                        else:
                                            create_geofence_rules(_resource, perms, None, _group, batch)
                                        exist_geolimits = exist_geolimits or has_geolimits(_resource, None, _group)

                                for perm in deferred_anon_perms:
                                    create_geofence_rules(_resource, perm, None, None, batch)

                            else:
                                # Owner & Managers
                                perms = (
                                    OWNER_PERMISSIONS.copy()
                                    + DATASET_ADMIN_PERMISSIONS.copy()
                                    + DOWNLOAD_PERMISSIONS.copy()
                                )
                                create_geofence_rules(_resource, perms, _owner, None, batch)
                                exist_geolimits = exist_geolimits or has_geolimits(_resource, _owner, None)

                                _resource_groups, _group_managers = _resource.get_group_managers(group=_resource.group)
                                for _group_manager in _group_managers:
                                    create_geofence_rules(_resource, perms, _group_manager, None, batch)
                                    exist_geolimits = exist_geolimits or has_geolimits(_resource, _group_manager, None)

                                for user_group in _resource_groups:
                                    if not skip_registered_members_common_group(user_group):
                                        create_geofence_rules(_resource, perms, None, user_group, batch)
                                        exist_geolimits = exist_geolimits or has_geolimits(_resource, None, user_group)

                                # Anonymous
                                if settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION:
                                    create_geofence_rules(_resource, VIEW_PERMISSIONS, None, None, batch)
                                    exist_geolimits = exist_geolimits or has_geolimits(_resource, None, None)

                                if settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION:
                                    create_geofence_rules(_resource, DOWNLOAD_PERMISSIONS, None, None, batch)
                                    exist_geolimits = exist_geolimits or has_geolimits(_resource, None, None)

                            if exist_geolimits is not None:
                                filters, formats = _get_gwc_filters_and_formats(exist_geolimits)
                                try:
                                    _dataset_workspace = get_dataset_workspace(_resource)
                                    toggle_dataset_cache(
                                        f"{_dataset_workspace}:{_resource.name}", filters=filters, formats=formats
                                    )
                                except Dataset.DoesNotExist:
                                    pass

                            try:
                                logger.info(
                                    f"Pushing {batch.length()} " f"changes into GeoFence for resource {_resource.name}"
                                )
                                executed = geofence.run_batch(batch)
                                if executed:
                                    geofence.invalidate_cache()
                            except Exception as e:
                                logger.warning(
                                    f"Could not sync GeoFence for resource {_resource}: {e}." " Retrying async."
                                )
                                _resource.set_dirty_state()
                        else:
                            _resource.set_dirty_state()
        except Exception as e:
            logger.exception(e)
            return False

        geofence_rule_assign.send_robust(sender=instance, instance=instance)

        return True

    def set_thumbnail(
        self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True
    ) -> bool:
        if instance and (
            isinstance(instance.get_real_instance(), Dataset) or isinstance(instance.get_real_instance(), Map)
        ):
            if overwrite or not instance.thumbnail_url:
                create_gs_thumbnail(instance.get_real_instance(), overwrite=overwrite, check_bbox=check_bbox)
            return True
        return False

    def exec(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        raise NotImplementedError

    def set_style(self, method: str, uuid: str, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        instance = instance or ResourceManager._get_instance(uuid)

        if instance and isinstance(instance.get_real_instance(), Dataset):
            try:
                logger.info(f"Creating style for Dataset {instance.get_real_instance()} / {kwargs}")
                _sld_file = kwargs.get("sld_file", None)
                _tempdir = kwargs.get("tempdir", tempfile.gettempdir())
                if _sld_file and kwargs.get("sld_uploaded", False):
                    geoserver_set_style(instance.get_real_instance().id, _sld_file)
                else:
                    geoserver_create_style(
                        instance.get_real_instance().id, instance.get_real_instance().name, _sld_file, _tempdir
                    )
            except Exception as e:
                logger.exception(e)
                return None
        return instance

    def set_time_info(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        instance = instance or ResourceManager._get_instance(uuid)

        if instance and isinstance(instance.get_real_instance(), Dataset):
            try:
                if kwargs.get("time_info", None):
                    set_time_info(instance.get_real_instance(), **kwargs["time_info"])
            except Exception as e:
                logger.exception(e)
                return None
        return instance
