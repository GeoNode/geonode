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
from django.conf import settings
from geonode.layers.models import Dataset
from geonode.upload.handlers.common.remote import BaseRemoteResourceHandler
from geonode.services import enumerations
from geonode.base.enumerations import SOURCE_TYPE_REMOTE
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.handlers.remote.serializers.wms import RemoteWMSSerializer
from geonode.upload.orchestrator import orchestrator
from geonode.harvesting.harvesters.wms import WebMapService
from geonode.services.serviceprocessors.wms import WmsServiceHandler
from geonode.resource.manager import resource_manager

logger = logging.getLogger("importer")


class RemoteWMSResourceHandler(BaseRemoteResourceHandler):

    @staticmethod
    def has_serializer(data) -> bool:
        """
        Return the custom serializer for the WMS
        """
        if "url" in data and enumerations.WMS in data.get("type", "").upper():
            return RemoteWMSSerializer
        return False

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        if "url" in _data and enumerations.WMS.lower() in _data.get("type", "").lower():
            return True
        return False

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        payload, original_data = BaseRemoteResourceHandler.extract_params_from_data(_data, action=action)
        if action != exa.COPY.value:
            payload["lookup"] = original_data.pop("lookup", None)
            payload["bbox"] = original_data.pop("bbox", None)
            payload["parse_remote_metadata"] = original_data.pop("parse_remote_metadata", None)

        return payload, original_data

    def prepare_import(self, files, execution_id, **kwargs):
        """
        If the title and bbox must be retrieved from the remote resource
        we take them before starting the import, so we can keep the default
        workflow behaviour
        """
        _exec = orchestrator.get_execution_object(exec_id=execution_id)
        cleaned_url, _, _, _ = WmsServiceHandler.get_cleaned_url_params(_exec.input_params.get("url"))
        parsed_url = f"{cleaned_url.scheme}://{cleaned_url.netloc}{cleaned_url.path}"
        ows_url = f"{parsed_url}?{cleaned_url.query}"
        to_update = {
            "ows_url": ows_url,
            "parsed_url": parsed_url,
            "remote_resource_id": _exec.input_params.get("lookup", None),
        }
        if _exec.input_params.get("parse_remote_metadata", False):
            try:
                wms_resource = self.get_wms_resource(_exec)
                to_update.update(
                    {
                        "title": wms_resource.title,
                        "bbox": wms_resource.boundingBoxWGS84,
                    }
                )
            except Exception as e:
                logger.error(f"Error during the fetch of the WSM details, please check the log {e}")
                raise e

        _exec.input_params.update(to_update)
        _exec.save()

    def get_wms_resource(self, _exec):
        _, wms = WebMapService(_exec.input_params.get("url"))
        wms_resource = wms[_exec.input_params.get("lookup")]
        return wms_resource

    def generate_alternate(
        self,
        layer_name,
        execution_id,
        should_be_overwritten,
        payload_alternate,
        user_datasets,
        dataset_exists,
    ):
        """
        For WMS we dont want to generate an alternate, otherwise we cannot use
        the alternate to lookup the layer in the remote service
        """
        return layer_name, payload_alternate

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = ...,
        asset=None,
    ):
        """
        Use the default RemoteResourceHandler to create the geonode resource
        after that, we assign the bbox and re-generate the thumbnail
        """
        resource = super().create_geonode_resource(layer_name, alternate, execution_id, Dataset, asset)
        _exec = orchestrator.get_execution_object(execution_id)
        remote_bbox = _exec.input_params.get("bbox")
        if remote_bbox:
            resource.set_bbox_polygon(remote_bbox, "EPSG:4326")
            resource_manager.set_thumbnail(None, instance=resource)
        return resource

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace, **kwargs):
        """
        Here are returned all the information required to generate the geonode resource
        inclusing the OWS url
        """
        return dict(
            resource_type="dataset",
            subtype="remote",
            sourcetype=SOURCE_TYPE_REMOTE,
            alternate=alternate,
            dirty_state=True,
            title=kwargs.get("title", layer_name),
            name=alternate,
            owner=_exec.user,
            workspace=getattr(settings, "DEFAULT_WORKSPACE", "geonode"),
            store=_exec.input_params.get("parsed_url")
            .encode("utf-8", "ignore")
            .decode("utf-8")
            .replace(".", "")
            .replace("/", ""),
            ptype="gxp_wmscsource",
            ows_url=_exec.input_params.get("ows_url"),
        )
