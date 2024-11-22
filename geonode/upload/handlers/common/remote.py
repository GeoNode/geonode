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
import json
import logging
import os

import requests
from geonode.layers.models import Dataset
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.api.exceptions import ImportException
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.common.serializer import RemoteResourceSerializer
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.orchestrator import orchestrator
from geonode.upload.celery_tasks import import_orchestrator
from geonode.upload.handlers.utils import create_alternate
from geonode.upload.utils import ImporterRequestAction as ira
from geonode.base.models import ResourceBase, Link
from urllib.parse import urlparse
from geonode.base.enumerations import SOURCE_TYPE_REMOTE
from geonode.resource.manager import resource_manager
from geonode.resource.models import ExecutionRequest

logger = logging.getLogger("importer")


class BaseRemoteResourceHandler(BaseHandler):
    """
    Handler to import remote resources into GeoNode data db
    It must provide the task_lists required to comple the upload
    As first implementation only remote 3dtiles are supported
    """

    TASKS = {
        exa.UPLOAD.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        ),
        exa.COPY.value: (
            "start_copy",
            "geonode.upload.copy_geonode_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
    }

    @staticmethod
    def has_serializer(data) -> bool:
        if "url" in data:
            return RemoteResourceSerializer
        return False

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        if "url" in _data:
            return True
        return False

    @staticmethod
    def is_valid_url(url, **kwargs):
        """
        We mark it as valid if the urls is reachable
        and if the url is valid
        """
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
        except requests.exceptions.Timeout:
            raise ImportException("Timed out")
        except Exception:
            raise ImportException("The provided URL is not reachable")
        return True

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        if action == exa.COPY.value:
            title = json.loads(_data.get("defaults"))
            return {"title": title.pop("title"), "store_spatial_file": True}, _data

        return {
            "action": _data.pop("action", "upload"),
            "title": _data.pop("title", None),
            "url": _data.pop("url", None),
            "type": _data.pop("type", None),
            "overwrite_existing_layer": _data.pop("overwrite_existing_layer", False),
        }, _data

    def pre_validation(self, files, execution_id, **kwargs):
        """
        Hook for let the handler prepare the data before the validation.
        Maybe a file rename, assign the resource to the execution_id
        """

    def import_resource(self, files: dict, execution_id: str, **kwargs) -> str:
        """
        Main function to import the resource.
        Internally will call the steps required to import the
        data inside the geonode_data database
        """
        # for the moment we skip the dyanamic model creation
        logger.info("Total number of layers available: 1")
        _exec = self._get_execution_request_object(execution_id)
        _input = {**_exec.input_params, **{"total_layers": 1}}
        orchestrator.update_execution_request_status(execution_id=str(execution_id), input_params=_input)

        try:
            params = _exec.input_params.copy()
            url = params.get("url")
            title = params.get("title", None) or os.path.basename(urlparse(url).path)

            # start looping on the layers available
            layer_name = self.fixup_name(title)

            should_be_overwritten = _exec.input_params.get("overwrite_existing_layer")

            payload_alternate = params.get("remote_resource_id", None)

            user_datasets = ResourceBase.objects.filter(owner=_exec.user, alternate=payload_alternate or layer_name)

            dataset_exists = user_datasets.exists()

            layer_name, alternate = self.generate_alternate(
                layer_name,
                execution_id,
                should_be_overwritten,
                payload_alternate,
                user_datasets,
                dataset_exists,
            )

            import_orchestrator.apply_async(
                (
                    files,
                    execution_id,
                    str(self),
                    "geonode.upload.import_resource",
                    layer_name,
                    alternate,
                    exa.UPLOAD.value,
                )
            )
            return layer_name, alternate, execution_id

        except Exception as e:
            logger.error(e)
            raise e

    def generate_alternate(
        self,
        layer_name,
        execution_id,
        should_be_overwritten,
        payload_alternate,
        user_datasets,
        dataset_exists,
    ):
        if dataset_exists and should_be_overwritten:
            layer_name, alternate = (
                payload_alternate or layer_name,
                user_datasets.first().alternate.split(":")[-1],
            )
        elif not dataset_exists:
            alternate = payload_alternate or layer_name
        else:
            alternate = create_alternate(payload_alternate or layer_name, execution_id)
        return layer_name, alternate

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: ResourceBase = ResourceBase,
        asset=None,
    ):
        """
        Creating geonode base resource
        We ignore the params, we use the function as a interface to keep the same
        importer flow.
        We create a standard ResourceBase
        """
        _exec = orchestrator.get_execution_object(execution_id)
        params = _exec.input_params.copy()

        resource = resource_manager.create(
            None,
            resource_type=resource_type,
            defaults=self.generate_resource_payload(layer_name, alternate, asset, _exec, None, **params),
        )
        resource_manager.set_thumbnail(None, instance=resource)

        resource = self.create_link(resource, params, alternate)
        ResourceBase.objects.filter(alternate=alternate).update(dirty_state=False)

        return resource

    def create_link(self, resource, params: dict, name):
        link = Link(
            resource=resource,
            extension=params.get("type"),
            url=params.get("url"),
            link_type="data",
            name=name,
        )
        link.save()
        return resource

    def create_resourcehandlerinfo(
        self,
        handler_module_path: str,
        resource: Dataset,
        execution_id: ExecutionRequest,
        **kwargs,
    ):
        """
        Create relation between the GeonodeResource and the handler used
        to create/copy it
        """

        ResourceHandlerInfo.objects.create(
            handler_module_path=handler_module_path,
            resource=resource,
            execution_request=execution_id,
            kwargs=kwargs.get("kwargs", {}) or kwargs,
        )

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace, **kwargs):
        return dict(
            subtype=kwargs.get("type"),
            sourcetype=SOURCE_TYPE_REMOTE,
            alternate=alternate,
            dirty_state=True,
            title=kwargs.get("title", layer_name),
            owner=_exec.user,
        )

    def overwrite_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = ResourceBase,
        asset=None,
    ):
        _exec = self._get_execution_request_object(execution_id)
        resource = resource_type.objects.filter(alternate__icontains=alternate, owner=_exec.user)

        _overwrite = _exec.input_params.get("overwrite_existing_layer", False)
        # if the layer exists, we just update the information of the dataset by
        # let it recreate the catalogue
        if resource.exists() and _overwrite:
            resource = resource.first()

            resource = resource_manager.update(resource.uuid, instance=resource)
            resource_manager.set_thumbnail(resource.uuid, instance=resource, overwrite=True)
            resource.refresh_from_db()
            return resource
        elif not resource.exists() and _overwrite:
            logger.warning(
                f"The dataset required {alternate} does not exists, but an overwrite is required, the resource will be created"
            )
            return self.create_geonode_resource(layer_name, alternate, execution_id, resource_type, asset)
        elif not resource.exists() and not _overwrite:
            logger.warning("The resource does not exists, please use 'create_geonode_resource' to create one")
        return
