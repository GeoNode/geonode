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

from .manager import ResourceManagerInterface

from django.db.models.query import QuerySet

from geonode.base.models import ResourceBase
from geonode.services.enumerations import CASCADED
from geonode.geoserver.tasks import geoserver_cascading_delete
from geonode.geoserver.helpers import (
    gs_catalog,
    ogc_server_settings)

logger = logging.getLogger(__name__)


class GeoServerResourceManager(ResourceManagerInterface):

    def search(self, filter: dict, /, type: object = None) -> QuerySet:
        return type.objects.none()

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        if uuid and instance:
            if hasattr(instance.get_real_instance(), 'storeType') and instance.get_real_instance().storeType not in ['tileStore', 'remoteStore']:
                try:
                    logger.debug(f"Searching GeoServer for layer '{instance.alternate}'")
                    if gs_catalog.get_layer(instance.alternate):
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
            if _real_instance.remote_service is None or _real_instance.remote_service.method == CASCADED:
                if _real_instance.alternate:
                    geoserver_cascading_delete.apply_async((_real_instance.alternate,))

    def create(self, uuid: str, /, instance: ResourceBase = None) -> int:
        pass

    def update(self, uuid: str, /, instance: ResourceBase = None) -> int:
        pass
