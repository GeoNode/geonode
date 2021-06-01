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
import tempfile

from django.db.models.query import QuerySet

from geonode.layers.models import Layer
from geonode.base.models import ResourceBase
from geonode.services.enumerations import CASCADED
from geonode.resource.manager import ResourceManager, ResourceManagerInterface

from .tasks import (
    geoserver_set_style,
    geoserver_create_style,
    geoserver_cascading_delete,
    geoserver_create_thumbnail)
from .signals import geoserver_post_save_local
from .helpers import (
    gs_catalog,
    set_time_info,
    ogc_server_settings)

logger = logging.getLogger(__name__)


class GeoServerResourceManager(ResourceManagerInterface):

    def search(self, filter: dict, /, type: object = None) -> QuerySet:
        return type.objects.none()

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        if instance:
            _real_instance = instance.get_real_instance()
            if hasattr(_real_instance, 'storeType') and _real_instance.storeType not in ['tileStore', 'remoteStore']:
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
            if hasattr(_real_instance, 'alternate') and _real_instance.alternate:
                if _real_instance.remote_service is None or _real_instance.remote_service.method == CASCADED:
                    geoserver_cascading_delete.apply_async((_real_instance.alternate,))

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
            if type(instance.get_real_instance()) == Layer:
                geoserver_post_save_local(instance.get_real_instance())
        return instance

    def set_permissions(self, uuid: str, /, instance: ResourceBase = None, permissions: dict = {}, created: bool = False) -> bool:
        # TODO: move GeoFence set perms logic here
        return True

    def set_thumbnail(self, uuid: str, /, instance: ResourceBase = None, overwrite: bool = True, check_bbox: bool = True) -> bool:
        if instance:
            # TODO: missing thumb for documents
            geoserver_create_thumbnail.apply_async(((instance.id, overwrite, check_bbox, )))
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
