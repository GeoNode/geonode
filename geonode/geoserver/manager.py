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
import tempfile

from django.conf import settings
from django.db.models.query import QuerySet
from django.contrib.auth.models import Group
from django.templatetags.static import static
from django.contrib.auth import get_user_model

from geonode.maps.models import Map
from geonode.base import enumerations
from geonode.layers.models import Layer
from geonode.upload.models import Upload
from geonode.base.models import ResourceBase
from geonode.documents.models import Document
from geonode.utils import get_layer_workspace
from geonode.services.enumerations import CASCADED
from geonode.groups.conf import settings as groups_settings
from geonode.security.permissions import VIEW_PERMISSIONS
from geonode.security.utils import (
    get_user_groups,
    get_obj_group_managers,
    skip_registered_members_common_group)
from geonode.resource.manager import (
    ResourceManager,
    ResourceManagerInterface)

from geonode.storage.manager import storage_manager
from .tasks import (
    geoserver_set_style,
    geoserver_delete_map,
    geoserver_create_style,
    geoserver_cascading_delete,
    geoserver_create_thumbnail)
from .signals import geoserver_post_save_local
from .helpers import (
    gs_catalog,
    gs_uploader,
    set_styles,
    set_time_info,
    ogc_server_settings)
from .security import (
    _get_gf_services,
    get_user_geolimits,
    toggle_layer_cache,
    purge_geofence_layer_rules,
    sync_geofence_with_guardian,
    set_geofence_invalidate_cache
)
logger = logging.getLogger(__name__)


class GeoServerResourceManager(ResourceManagerInterface):

    def search(self, filter: dict, /, type: object = None) -> QuerySet:
        return type.objects.none()

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        if instance:
            _real_instance = instance.get_real_instance()
            if hasattr(_real_instance, 'storeType') and _real_instance.storeType not in ['tileStore', 'remote']:
                try:
                    logger.debug(f"Searching GeoServer for layer '{_real_instance.alternate}'")
                    if gs_catalog.get_layer(_real_instance.alternate):
                        return True
                except Exception as e:
                    logger.debug(e)
                    return False
            return True
        return False

    def delete(self, uuid: str, /, instance: ResourceBase = None) -> int:
        """Removes the layer from GeoServer
        """
        # cascading_delete should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if instance and getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            _real_instance = instance.get_real_instance()
            if isinstance(_real_instance, Layer) and hasattr(_real_instance, 'alternate') and _real_instance.alternate:
                if _real_instance.remote_service is None or _real_instance.remote_service.method == CASCADED:
                    geoserver_cascading_delete.apply_async((_real_instance.alternate,))
            elif isinstance(_real_instance, Map):
                geoserver_delete_map.apply_async((_real_instance.id, ))

    def create(self, uuid: str, /, resource_type: object = None, defaults: dict = {}) -> ResourceBase:
        if resource_type:
            _resource = resource_type.objects.get(uuid=uuid)
            if resource_type == Layer:
                geoserver_post_save_local(_resource)
            return _resource
        return None

    def update(self, uuid: str, /, instance: ResourceBase = None, xml_file: str = None, metadata_uploaded: bool = False,
               vals: dict = {}, regions: dict = {}, keywords: dict = {}, custom: dict = {}, notify: bool = True) -> ResourceBase:
        if instance:
            if isinstance(instance.get_real_instance(), Layer):
                geoserver_post_save_local(instance.get_real_instance())
        return instance

    def copy(self, instance: ResourceBase, /, uuid: str = None, defaults: dict = {}) -> ResourceBase:
        if instance and isinstance(instance.get_real_instance(), Layer):
            return self.import_layer(
                'import_layer',
                instance.uuid,
                instance=instance,
                files=defaults.get('files', None),
                user=defaults.get('user', instance.owner),
                defaults=defaults,
                action_type='create')
        return instance

    def append(self, instance: ResourceBase, vals: dict = {}) -> ResourceBase:
        if instance and isinstance(instance.get_real_instance(), Layer):
            return self.import_layer(
                'import_layer',
                instance.uuid,
                instance=instance,
                files=vals.get('files', None),
                user=vals.get('user', instance.owner),
                action_type='append')
        return instance

    def replace(self, instance: ResourceBase, vals: dict = {}) -> ResourceBase:
        if instance and isinstance(instance.get_real_instance(), Layer):
            return self.import_layer(
                'import_layer',
                instance.uuid,
                instance=instance,
                files=vals.get('files', None),
                user=vals.get('user', instance.owner),
                action_type='replace')
        return instance

    def import_layer(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        instance = instance or ResourceManager._get_instance(uuid)

        if instance and isinstance(instance.get_real_instance(), Layer):
            upload_session, import_session = self._revise_resource_value(
                instance,
                kwargs.get('files', None),
                kwargs.get('user', instance.owner),
                action_type=kwargs.get('action_type', 'create'))
            upload_session.save()
            if import_session and import_session.state == enumerations.STATE_COMPLETE:
                _alternate = f'{instance.workspace}:{import_session.tasks[0].layer.name}'
                instance.name = import_session.tasks[0].layer.name
                instance.alternate = _alternate
                if 'defaults' in kwargs:
                    kwargs['defaults']['name'] = import_session.tasks[0].layer.name
                    kwargs['defaults']['alternate'] = _alternate
                if kwargs.get('action_type', 'create') == 'create':
                    set_styles(instance.get_real_instance(), gs_catalog)
        return instance

    def _revise_resource_value(self, instance, files: list, user, action_type: str):
        upload_session, _ = Upload.objects.get_or_create(resource=instance.resourcebase_ptr, user=user)
        upload_session.resource = instance.resourcebase_ptr
        upload_session.processed = False
        upload_session.save()
        gs_layer = gs_catalog.get_layer(instance.name)
        #  opening Import session for the selected layer
        if not gs_layer:
            raise Exception("Layer is not available in GeoServer")

        _target_store = gs_layer.resource.store.name if instance.storeType == 'vector' else None
        import_session = gs_uploader.start_import(
            import_id=upload_session.id,
            name=instance.name,
            target_store=_target_store
        )

        import_session.upload_task(files)
        task = import_session.tasks[0]
        #  Changing layer name, mode and target
        task.layer.set_target_layer_name(instance.name)
        task.set_update_mode(action_type.upper())
        task.set_target(
            store_name=_target_store,
            workspace=gs_layer.resource.workspace.name
        )
        #  Starting import process
        import_session.commit()

        # Updating Resource with the files replaced
        if action_type.lower() == 'replace':
            updated_files_list = storage_manager.replace(instance, files)
            # Using update instead of save in order to avoid calling
            # side-effect function of the resource
            r = ResourceBase.objects.filter(id=instance.id)
            r.update(**updated_files_list)

        return upload_session, gs_uploader.get_session(import_session.id)

    def remove_permissions(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        instance = instance or ResourceManager._get_instance(uuid)

        try:
            if instance and isinstance(instance.get_real_instance(), Layer):
                if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
                    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
                        purge_geofence_layer_rules(instance.get_real_instance())
                        set_geofence_invalidate_cache()
                    else:
                        instance.set_dirty_state()
        except Exception as e:
            logger.exception(e)
            return False
        return True

    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner=None, permissions: dict = {}, created: bool = False) -> bool:
        instance = instance or ResourceManager._get_instance(uuid)

        try:
            _disable_cache = []
            _owner = owner or instance.owner
            if permissions is not None:
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if instance.polymorphic_ctype.name == 'layer':
                        # Owner
                        if not created:
                            purge_geofence_layer_rules(instance.get_self_resource())
                        perms = [
                            "view_resourcebase",
                            "change_layer_data",
                            "change_layer_style",
                            "change_resourcebase",
                            "change_resourcebase_permissions",
                            "download_resourcebase"]
                        sync_geofence_with_guardian(instance, perms, user=_owner)
                        gf_services = _get_gf_services(instance, perms)
                        _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, _owner, None, gf_services)
                        _disable_cache.append(_disable_layer_cache)

                        # All the other users
                        if 'users' in permissions and len(permissions['users']) > 0:
                            for user, perms in permissions['users'].items():
                                _user = get_user_model().objects.get(username=user)
                                if _user != _owner:
                                    # Set the GeoFence Rules
                                    group_perms = None
                                    if 'groups' in permissions and len(permissions['groups']) > 0:
                                        group_perms = permissions['groups']
                                    if user == "AnonymousUser":
                                        _user = None
                                    sync_geofence_with_guardian(instance, perms, user=_user, group_perms=group_perms)
                                    gf_services = _get_gf_services(instance, perms)
                                    _group = list(group_perms.keys())[0] if group_perms else None
                                    _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, _user, _group, gf_services)
                                    _disable_cache.append(_disable_layer_cache)

                        # All the other groups
                        if 'groups' in permissions and len(permissions['groups']) > 0:
                            for group, perms in permissions['groups'].items():
                                _group = Group.objects.get(name=group)
                                # Set the GeoFence Rules
                                if _group and _group.name and _group.name == 'anonymous':
                                    _group = None
                                sync_geofence_with_guardian(instance, perms, group=_group)
                                gf_services = _get_gf_services(instance, perms)
                                _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, None, _group, gf_services)
                                _disable_cache.append(_disable_layer_cache)
            else:
                anonymous_can_view = settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION
                anonymous_can_download = settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if instance.polymorphic_ctype.name == 'layer':
                        purge_geofence_layer_rules(instance.get_self_resource())

                        # Owner & Managers
                        perms = [
                            "view_resourcebase",
                            "change_layer_data",
                            "change_layer_style",
                            "change_resourcebase",
                            "change_resourcebase_permissions",
                            "download_resourcebase"]
                        sync_geofence_with_guardian(instance, perms, user=_owner)
                        gf_services = _get_gf_services(instance, perms)
                        _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, _owner, None, gf_services)
                        _disable_cache.append(_disable_layer_cache)

                        for _group_manager in get_obj_group_managers(_owner):
                            sync_geofence_with_guardian(instance, perms, user=_group_manager)
                            _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, _group_manager, None, gf_services)
                            _disable_cache.append(_disable_layer_cache)

                        for user_group in get_user_groups(_owner):
                            if not skip_registered_members_common_group(user_group):
                                sync_geofence_with_guardian(instance, perms, group=user_group)
                                _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, None, user_group, gf_services)
                                _disable_cache.append(_disable_layer_cache)

                        # Anonymous
                        perms = ["view_resourcebase"]
                        if anonymous_can_view:
                            sync_geofence_with_guardian(instance, perms, user=None, group=None)
                            gf_services = _get_gf_services(instance, perms)
                            _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, None, None, gf_services)
                            _disable_cache.append(_disable_layer_cache)

                        perms = ["download_resourcebase"]
                        if anonymous_can_download:
                            sync_geofence_with_guardian(instance, perms, user=None, group=None)
                            gf_services = _get_gf_services(instance, perms)
                            _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, None, None, gf_services)
                            _disable_cache.append(_disable_layer_cache)

            if _disable_cache and any(_disable_cache):
                filters = None
                formats = None
            else:
                filters = [{
                    "styleParameterFilter": {
                        "STYLES": ""
                    }
                }]
                formats = [
                    'application/json;type=utfgrid',
                    'image/gif',
                    'image/jpeg',
                    'image/png',
                    'image/png8',
                    'image/vnd.jpeg-png',
                    'image/vnd.jpeg-png8'
                ]
            try:
                toggle_layer_cache(f'{get_layer_workspace(instance)}:{instance.name}', enable=True, filters=filters, formats=formats)
            except Layer.DoesNotExist:
                pass
        except Exception as e:
            logger.exception(e)
            return False
        return True

    def set_workflow_permissions(self, uuid: str, /, instance: ResourceBase = None, approved: bool = False, published: bool = False) -> bool:
        instance = instance or ResourceManager._get_instance(uuid)

        try:
            _disable_cache = []
            gf_services = _get_gf_services(instance, VIEW_PERMISSIONS)
            if approved:
                # Set the GeoFence Rules (user = None)
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if instance.polymorphic_ctype.name == 'layer':
                        if groups_settings.AUTO_ASSIGN_REGISTERED_MEMBERS_TO_REGISTERED_MEMBERS_GROUP_NAME:
                            _members_group_name = groups_settings.REGISTERED_MEMBERS_GROUP_NAME
                            _members_group_group = Group.objects.get(name=_members_group_name)
                            sync_geofence_with_guardian(instance, VIEW_PERMISSIONS, group=_members_group_group)
                            _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, None, _members_group_group, gf_services)
                            _disable_cache.append(_disable_layer_cache)
                        else:
                            # Set the GeoFence Rules (user = None)
                            if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                                if instance.polymorphic_ctype.name == 'layer':
                                    sync_geofence_with_guardian(instance, VIEW_PERMISSIONS)
                                    _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, None, None, gf_services)
                                    _disable_cache.append(_disable_layer_cache)
            if published:
                # Set the GeoFence Rules (user = None)
                if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                    if instance.polymorphic_ctype.name == 'layer':
                        sync_geofence_with_guardian(instance, VIEW_PERMISSIONS)
                        _, _, _disable_layer_cache, _, _, _ = get_user_geolimits(instance, None, None, gf_services)
                        _disable_cache.append(_disable_layer_cache)

            if _disable_cache and any(_disable_cache):
                filters = None
                formats = None
            else:
                filters = [{
                    "styleParameterFilter": {
                        "STYLES": ""
                    }
                }]
                formats = [
                    'application/json;type=utfgrid',
                    'image/gif',
                    'image/jpeg',
                    'image/png',
                    'image/png8',
                    'image/vnd.jpeg-png',
                    'image/vnd.jpeg-png8'
                ]
            try:
                toggle_layer_cache(f'{get_layer_workspace(instance)}:{instance.name}', enable=True, filters=filters, formats=formats)
            except Layer.DoesNotExist:
                pass
        except Exception as e:
            logger.exception(e)
            return False
        return True

    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        if instance and not isinstance(instance.get_real_instance(), Document):
            if overwrite or instance.thumbnail_url == static(settings.MISSING_THUMBNAIL):
                geoserver_create_thumbnail.apply_async((instance.id, overwrite, check_bbox, ))
            return True
        return False

    def exec(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        raise NotImplementedError

    def set_style(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        instance = instance or ResourceManager._get_instance(uuid)

        if instance and isinstance(instance.get_real_instance(), Layer):
            try:
                logger.info(f'Creating style for Layer {instance.get_real_instance()} / {kwargs}')
                _sld_file = kwargs.get('sld_file', None)
                _tempdir = kwargs.get('tempdir', tempfile.gettempdir())
                if _sld_file and kwargs.get('sld_uploaded', False):
                    geoserver_set_style(instance.get_real_instance().id, _sld_file)
                else:
                    geoserver_create_style(instance.get_real_instance().id, instance.get_real_instance().name, _sld_file, _tempdir)
            except Exception as e:
                logger.exception(e)
                return None
        return instance

    def set_time_info(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        instance = instance or ResourceManager._get_instance(uuid)

        if instance and isinstance(instance.get_real_instance(), Layer):
            try:
                if kwargs.get('time_info', None):
                    set_time_info(instance.get_real_instance(), kwargs['time_info'])
            except Exception as e:
                logger.exception(e)
                return None
        return instance
