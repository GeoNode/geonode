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
import typing
import logging
import tempfile
import dataclasses

from gsimporter.api import Session

from django.conf import settings
from django.db.models.query import QuerySet
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model

from geonode.maps.models import Map
from geonode.base import enumerations
from geonode.layers.models import Dataset
from geonode.upload.models import Upload
from geonode.base.models import ResourceBase
from geonode.utils import get_dataset_workspace
from geonode.services.enumerations import CASCADED
from geonode.security.utils import skip_registered_members_common_group
from geonode.security.permissions import (
    VIEW_PERMISSIONS,
    OWNER_PERMISSIONS,
    DOWNLOAD_PERMISSIONS,
    DATASET_ADMIN_PERMISSIONS)
from geonode.resource.manager import (
    ResourceManager,
    ResourceManagerInterface)

from .tasks import (
    geoserver_set_style,
    geoserver_delete_map,
    geoserver_create_style,
    geoserver_cascading_delete)
from .helpers import (
    SpatialFilesLayerType,
    gs_catalog,
    gs_uploader,
    set_styles,
    set_time_info,
    ogc_server_settings,
    get_spatial_files_dataset_type,
    sync_instance_with_geoserver,
    set_attributes_from_geoserver,
    create_gs_thumbnail,
    create_geoserver_db_featurestore)
from .security import (
    _get_gwc_filters_and_formats,
    toggle_dataset_cache,
    purge_geofence_dataset_rules,
    set_geofence_invalidate_cache,
    sync_permissions_and_disable_cache)

logger = logging.getLogger(__name__)


@dataclasses.dataclass()
class GeoServerImporterSessionInfo:
    upload_session: Upload
    import_session: Session
    spatial_files_type: SpatialFilesLayerType
    dataset_name: typing.AnyStr
    workspace: typing.AnyStr
    target_store: typing.AnyStr


class GeoServerResourceManager(ResourceManagerInterface):

    def search(self, filter: dict, /, resource_type: typing.Optional[object]) -> QuerySet:
        return resource_type.objects.none()

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        if instance:
            _real_instance = instance.get_real_instance()
            if hasattr(_real_instance, 'subtype') and _real_instance.subtype not in ['tileStore', 'remote']:
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
        """Removes the layer from GeoServer
        """
        # cascading_delete should only be called if
        # ogc_server_settings.BACKEND_WRITE_ENABLED == True
        if instance and getattr(ogc_server_settings, "BACKEND_WRITE_ENABLED", True):
            try:
                _real_instance = instance.get_real_instance()
                if isinstance(_real_instance, Dataset) and hasattr(_real_instance, 'alternate') and _real_instance.alternate:
                    if not hasattr(_real_instance, 'remote_service') or _real_instance.remote_service is None or _real_instance.remote_service.method == CASCADED:
                        geoserver_cascading_delete.apply_async((_real_instance.alternate,))
                elif isinstance(_real_instance, Map):
                    geoserver_delete_map.apply_async((_real_instance.id, ))
            except Exception as e:
                logger.exception(e)

    def create(self, uuid: str, /, resource_type: typing.Optional[object] = None, defaults: dict = {}) -> ResourceBase:
        _resource = resource_type.objects.get(uuid=uuid)
        if resource_type == Dataset:
            _synced_resource = sync_instance_with_geoserver(_resource.id)
            _resource = _synced_resource or _resource
        return _resource

    def update(self, uuid: str, /, instance: ResourceBase = None, xml_file: str = None, metadata_uploaded: bool = False,
               vals: dict = {}, regions: dict = {}, keywords: dict = {}, custom: dict = {}, notify: bool = True, **kwargs) -> ResourceBase:
        if instance:
            if isinstance(instance.get_real_instance(), Dataset):
                _synced_resource = sync_instance_with_geoserver(instance.id)
                instance = _synced_resource or instance
        return instance

    def ingest(self, files: typing.List[str], /, uuid: str = None, resource_type: typing.Optional[object] = None, defaults: dict = {}, **kwargs) -> ResourceBase:
        instance = ResourceManager._get_instance(uuid)
        if instance and isinstance(instance.get_real_instance(), Dataset):
            instance = self.import_dataset(
                'import_dataset',
                instance.uuid,
                instance=instance,
                files=files,
                user=defaults.get('user', instance.owner),
                defaults=defaults,
                action_type='create',
                **kwargs)
        return instance

    def copy(self, instance: ResourceBase, /, uuid: str = None, owner: settings.AUTH_USER_MODEL = None, defaults: dict = {}) -> ResourceBase:
        if uuid and instance:
            _resource = ResourceManager._get_instance(uuid)
            if _resource and isinstance(_resource.get_real_instance(), Dataset):
                importer_session_opts = defaults.get('importer_session_opts', {})
                if not importer_session_opts:
                    _src_upload_session = Upload.objects.filter(resource=instance.get_real_instance().resourcebase_ptr)
                    if _src_upload_session.exists():
                        _src_upload_session = _src_upload_session.get()
                        if _src_upload_session and _src_upload_session.get_session:
                            try:
                                _src_importer_session = _src_upload_session.get_session.import_session.reload()
                                importer_session_opts.update({'transforms': _src_importer_session.tasks[0].transforms})
                            except Exception as e:
                                logger.exception(e)
                return self.import_dataset(
                    'import_dataset',
                    uuid,
                    instance=_resource,
                    files=defaults.get('files', None),
                    user=defaults.get('user', _resource.owner),
                    defaults=defaults,
                    action_type='create',
                    importer_session_opts=importer_session_opts)
        return _resource

    def append(self, instance: ResourceBase, vals: dict = {}, *args, **kwargs) -> ResourceBase:
        if instance and isinstance(instance.get_real_instance(), Dataset):
            return self.import_dataset(
                'import_dataset',
                instance.uuid,
                instance=instance,
                files=vals.get('files', None),
                user=vals.get('user', instance.owner),
                action_type='append',
                importer_session_opts=vals.get('importer_session_opts', None),
                **kwargs
            )
        return instance

    def replace(self, instance: ResourceBase, vals: dict = {}, *args, **kwargs) -> ResourceBase:
        if instance and isinstance(instance.get_real_instance(), Dataset):
            return self.import_dataset(
                'import_dataset',
                instance.uuid,
                instance=instance,
                files=vals.get('files', None),
                user=vals.get('user', instance.owner),
                action_type='replace',
                importer_session_opts=vals.get('importer_session_opts', None),
                **kwargs
            )
        return instance

    def import_dataset(self, method: str, uuid: str, /, instance: ResourceBase = None, **kwargs) -> ResourceBase:
        instance = instance or ResourceManager._get_instance(uuid)

        if instance and isinstance(instance.get_real_instance(), Dataset):
            try:
                _gs_import_session_info = self._execute_resource_import(
                    instance,
                    kwargs.get('files', None),
                    kwargs.get('user', instance.owner),
                    action_type=kwargs.get('action_type', 'create'),
                    importer_session_opts=kwargs.get('importer_session_opts', None))
                import_session = _gs_import_session_info.import_session
                if import_session:
                    if import_session.state == enumerations.STATE_PENDING:
                        task = None
                        native_crs = None
                        target_crs = 'EPSG:4326'
                        for _task in import_session.tasks:
                            # CRS missing/unknown
                            if _task.state == 'NO_CRS':
                                task = _task
                                native_crs = _task.layer.srs
                                break
                        if not native_crs:
                            native_crs = 'EPSG:4326'
                        if task:
                            task.set_srs(native_crs)

                        transform = {
                            'type': 'ReprojectTransform',
                            'source': native_crs,
                            'target': target_crs,
                        }
                        task.remove_transforms([transform], by_field='type', save=False)
                        task.add_transforms([transform], save=False)
                        task.save_transforms()
                        #  Starting import process
                        import_session.commit()
                        import_session = import_session.reload()
                        _gs_import_session_info.import_session = import_session
                        _gs_import_session_info.dataset_name = import_session.tasks[0].layer.name
                    _name = _gs_import_session_info.dataset_name if import_session.state == enumerations.STATE_COMPLETE else ''
                    _alternate = f'{_gs_import_session_info.workspace}:{_gs_import_session_info.dataset_name}' if import_session.state == enumerations.STATE_COMPLETE else ''
                    _to_update = {
                        'name': _name,
                        'title': instance.title or _gs_import_session_info.dataset_name,
                        'files': kwargs.get('files', None),
                        'workspace': _gs_import_session_info.workspace,
                        'alternate': _alternate,
                        'typename': _alternate,
                        'store': _gs_import_session_info.target_store or _gs_import_session_info.dataset_name,
                        'subtype': _gs_import_session_info.spatial_files_type.dataset_type
                    }
                    if 'defaults' in kwargs:
                        kwargs['defaults'].update(_to_update)
                    Dataset.objects.filter(uuid=instance.uuid).update(**_to_update)
                    instance.get_real_instance_class().objects.filter(uuid=instance.uuid).update(**_to_update)
                    # Refresh from DB
                    instance.refresh_from_db()
                    if kwargs.get('action_type', 'create') == 'create':
                        set_styles(instance.get_real_instance(), gs_catalog)
                        set_attributes_from_geoserver(instance.get_real_instance(), overwrite=True)
                elif kwargs.get('action_type', 'create') == 'create':
                    logger.exception(Exception(f"Importer Session not valid - STATE: {import_session.state}"))
                if import_session.state == enumerations.STATE_COMPLETE:
                    instance.set_processing_state(enumerations.STATE_PROCESSED)
                else:
                    instance.set_processing_state(import_session.state)
                    instance.set_dirty_state()
                instance.save(notify=False)
            except Exception as e:
                logger.exception(e)
                if kwargs.get('action_type', 'create') == 'create':
                    instance.delete()
                    instance = None
        return instance

    def _execute_resource_import(self, instance, files: list, user, action_type: str, importer_session_opts: typing.Optional[typing.Dict] = None):
        from geonode.utils import get_allowed_extensions

        ALLOWED_EXTENSIONS = get_allowed_extensions()

        session_opts = dict(importer_session_opts) if importer_session_opts is not None else {}

        spatial_files_type = get_spatial_files_dataset_type(ALLOWED_EXTENSIONS, files)

        if not spatial_files_type:
            raise Exception(f"No suitable Spatial Files avaialable for 'ALLOWED_EXTENSIONS' = {ALLOWED_EXTENSIONS}.")

        upload_session, _ = Upload.objects.get_or_create(resource=instance.get_real_instance().resourcebase_ptr, user=user)
        upload_session.resource = instance.get_real_instance().resourcebase_ptr
        upload_session.save()

        _name = instance.get_real_instance().name
        if not _name:
            _name = session_opts.get('name', None) or os.path.splitext(os.path.basename(spatial_files_type.base_file))[0]
        instance.get_real_instance().name = _name

        gs_dataset = None
        try:
            gs_dataset = gs_catalog.get_layer(_name)
        except Exception as e:
            logger.debug(e)

        _workspace = None
        _target_store = None
        if gs_dataset:
            _target_store = gs_dataset.resource.store.name if instance.get_real_instance().subtype == 'vector' else None
            _workspace = gs_dataset.resource.workspace.name if gs_dataset.resource.workspace else None

        if not _workspace:
            _workspace = session_opts.get('workspace', instance.get_real_instance().workspace)
            if not _workspace:
                _workspace = instance.get_real_instance().workspace or settings.DEFAULT_WORKSPACE

        if not _target_store:
            if instance.get_real_instance().subtype == 'vector' or spatial_files_type.dataset_type == 'vector':
                _dsname = ogc_server_settings.datastore_db['NAME']
                _ds = create_geoserver_db_featurestore(store_name=_dsname, workspace=_workspace)
                if _ds:
                    _target_store = session_opts.get('target_store', None) or _dsname

        #  opening Import session for the selected layer
        # Let's reset the connections first
        gs_catalog._cache.clear()
        gs_catalog.reset()
        # Let's now try the new ingestion
        import_session = gs_uploader.start_import(
            import_id=upload_session.id,
            name=_name,
            target_store=_target_store
        )

        upload_session.set_processing_state(enumerations.STATE_PROCESSED)
        upload_session.import_id = import_session.id
        upload_session.name = _name
        upload_session.complete = True
        upload_session.processed = True
        upload_session.save()

        _gs_import_session_info = GeoServerImporterSessionInfo(
            upload_session=upload_session,
            import_session=import_session,
            spatial_files_type=spatial_files_type,
            dataset_name=None,
            workspace=_workspace,
            target_store=_target_store
        )

        import_session.upload_task(files)
        task = import_session.tasks[0]
        #  Changing layer name, mode and target
        task.layer.set_target_layer_name(_name)
        task.set_update_mode(action_type.upper())
        task.set_target(
            store_name=_target_store,
            workspace=_workspace
        )
        transforms = session_opts.get('transforms', None)
        if transforms:
            task.set_transforms(transforms)
        #  Starting import process
        import_session.commit()
        import_session = import_session.reload()

        _gs_import_session_info.import_session = import_session
        _gs_import_session_info.dataset_name = import_session.tasks[0].layer.name

        return _gs_import_session_info

    def remove_permissions(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        instance = instance or ResourceManager._get_instance(uuid)

        try:
            if instance and isinstance(instance.get_real_instance(), Dataset):
                if settings.OGC_SERVER['default']['GEOFENCE_SECURITY_ENABLED']:
                    if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
                        purge_geofence_dataset_rules(instance.get_real_instance())
                        set_geofence_invalidate_cache()
                    else:
                        instance.set_dirty_state()
        except Exception as e:
            logger.exception(e)
            return False
        return True

    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, owner: settings.AUTH_USER_MODEL = None, permissions: dict = {}, created: bool = False,
                        approval_status_changed: bool = False, group_status_changed: bool = False) -> bool:
        _resource = instance or ResourceManager._get_instance(uuid)

        try:
            if _resource:
                _resource = _resource.get_real_instance()
                logger.error(f'Fixup GIS Backend Security Rules Accordingly on resource {instance} {isinstance(_resource, Dataset)}')
                if isinstance(_resource, Dataset):
                    if settings.OGC_SERVER['default'].get("GEOFENCE_SECURITY_ENABLED", False):
                        if not getattr(settings, 'DELAYED_SECURITY_SIGNALS', False):
                            _disable_cache = []
                            _owner = owner or _resource.owner
                            if permissions is not None and len(permissions):
                                if not created:
                                    purge_geofence_dataset_rules(_resource)

                                # Owner
                                perms = OWNER_PERMISSIONS.copy() + DATASET_ADMIN_PERMISSIONS.copy() + DOWNLOAD_PERMISSIONS.copy()
                                _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, perms, _owner, None, None)

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
                                            _group = list(group_perms.keys())[0] if group_perms else None
                                            _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, perms, _user, _group, group_perms)

                                # All the other groups
                                if 'groups' in permissions and len(permissions['groups']) > 0:
                                    for group, perms in permissions['groups'].items():
                                        _group = Group.objects.get(name=group)
                                        # Set the GeoFence Rules
                                        if _group and _group.name and _group.name == 'anonymous':
                                            _group = None
                                        _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, perms, None, _group, None)
                            else:
                                anonymous_can_view = settings.DEFAULT_ANONYMOUS_VIEW_PERMISSION
                                anonymous_can_download = settings.DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION

                                if not created:
                                    purge_geofence_dataset_rules(_resource.get_self_resource())

                                # Owner & Managers
                                perms = OWNER_PERMISSIONS.copy() + DATASET_ADMIN_PERMISSIONS.copy() + DOWNLOAD_PERMISSIONS.copy()
                                _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, perms, _owner, None, None)

                                _resource_groups, _group_managers = _resource.get_group_managers(group=_resource.group)
                                for _group_manager in _group_managers:
                                    _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, perms, _group_manager, None, None)

                                for user_group in _resource_groups:
                                    if not skip_registered_members_common_group(user_group):
                                        _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, perms, None, user_group, None)

                                # Anonymous
                                if anonymous_can_view:
                                    _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, VIEW_PERMISSIONS, None, None, None)

                                if anonymous_can_download:
                                    _disable_cache = sync_permissions_and_disable_cache(_disable_cache, _resource, DOWNLOAD_PERMISSIONS, None, None, None)

                            if _disable_cache:
                                filters, formats = _get_gwc_filters_and_formats(_disable_cache)
                                try:
                                    _dataset_workspace = get_dataset_workspace(_resource)
                                    toggle_dataset_cache(f'{_dataset_workspace}:{_resource.name}', filters=filters, formats=formats)
                                except Dataset.DoesNotExist:
                                    pass
                        else:
                            _resource.set_dirty_state()
        except Exception as e:
            logger.exception(e)
            return False
        return True

    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        if instance and (isinstance(instance.get_real_instance(), Dataset) or isinstance(instance.get_real_instance(), Map)):
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
                logger.info(f'Creating style for Dataset {instance.get_real_instance()} / {kwargs}')
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

        if instance and isinstance(instance.get_real_instance(), Dataset):
            try:
                if kwargs.get('time_info', None):
                    set_time_info(instance.get_real_instance(), **kwargs['time_info'])
            except Exception as e:
                logger.exception(e)
                return None
        return instance
