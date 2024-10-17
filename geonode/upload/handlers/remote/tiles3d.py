#########################################################################
#
# Copyright (C) 2024 OSGeo
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

import requests
from geonode.layers.models import Dataset
from geonode.upload.handlers.common.remote import BaseRemoteResourceHandler
from geonode.upload.handlers.common.serializer import RemoteResourceSerializer
from geonode.upload.handlers.tiles3d.handler import Tiles3DFileHandler
from geonode.upload.orchestrator import orchestrator
from geonode.upload.handlers.tiles3d.exceptions import Invalid3DTilesException
from geonode.base.enumerations import SOURCE_TYPE_REMOTE
from geonode.base.models import ResourceBase

logger = logging.getLogger("importer")


class RemoteTiles3DResourceHandler(BaseRemoteResourceHandler, Tiles3DFileHandler):

    @property
    def supported_file_extension_config(self):
        return {}

    @staticmethod
    def has_serializer(data) -> bool:
        if "url" in data and "3dtiles" in data.get("type", "").lower():
            return RemoteResourceSerializer
        return False

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        if "url" in _data and "3dtiles" in _data.get("type"):
            return True
        return False

    @staticmethod
    def is_valid_url(url, **kwargs):
        BaseRemoteResourceHandler.is_valid_url(url)
        try:
            payload = requests.get(url, timeout=10).json()
            # required key described in the specification of 3dtiles
            # https://docs.ogc.org/cs/22-025r4/22-025r4.html#toc92
            is_valid = all(key in payload.keys() for key in ("asset", "geometricError", "root"))

            if not is_valid:
                raise Invalid3DTilesException(
                    "The provided 3DTiles is not valid, some of the mandatory keys are missing. Mandatory keys are: 'asset', 'geometricError', 'root'"
                )

            Tiles3DFileHandler.validate_3dtile_payload(payload=payload)

        except Exception as e:
            raise Invalid3DTilesException(e)

        return True

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = ResourceBase,
        asset=None,
    ):
        resource = super().create_geonode_resource(layer_name, alternate, execution_id, resource_type, asset)
        _exec = orchestrator.get_execution_object(exec_id=execution_id)
        try:
            js_file = requests.get(_exec.input_params.get("url"), timeout=10).json()
        except Exception as e:
            raise Invalid3DTilesException(e)

        if not js_file:
            raise Invalid3DTilesException("The JSON file returned by the URL is empty")

        if self._has_region(js_file):
            resource = self.set_bbox_from_region(js_file, resource=resource)
        elif self._has_sphere(js_file):
            resource = self.set_bbox_from_boundingVolume_sphere(js_file, resource=resource)
        else:
            resource = self.set_bbox_from_boundingVolume(js_file, resource=resource)

        return resource

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace, **kwargs):
        return dict(
            resource_type="dataset",
            subtype=kwargs.get("type"),
            sourcetype=SOURCE_TYPE_REMOTE,
            alternate=alternate,
            dirty_state=True,
            title=kwargs.get("title", layer_name),
            owner=_exec.user,
        )
