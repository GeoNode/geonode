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

from geonode.base.models import ResourceBase
from geonode.geoserver.helpers import gs_catalog

logger = logging.getLogger(__name__)


class GeoServerResourceManager(ResourceManagerInterface):

    def search(self, filter: dict) -> list:
        pass

    def exists(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        if uuid and instance:
            if hasattr(instance.get_real_instance(), 'storeType') and instance.get_real_instance().storeType != 'remoteStore':
                try:
                    logger.debug(f"Searching GeoServer for layer '{instance.alternate}'")
                    if gs_catalog.get_layer(instance.alternate):
                        return True
                except Exception as e:
                    logger.debug(e)
                    return False
            return True
        return False

    def delete(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass

    def create(self, uuid: str, /, instance: ResourceBase = None) -> bool:
        pass
