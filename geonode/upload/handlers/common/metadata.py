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
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.utils import UploadSourcesEnum
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.handlers.xml.serializer import MetadataFileSerializer
from geonode.upload.utils import ImporterRequestAction as ira
from geonode.upload.orchestrator import orchestrator
from django.shortcuts import get_object_or_404
from geonode.layers.models import Dataset

logger = logging.getLogger("importer")


class MetadataFileHandler(BaseHandler):
    """
    Handler to import metadata files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    ACTIONS = {
        exa.IMPORT.value: ("start_import", "geonode.upload.import_resource"),
        ira.ROLLBACK.value: (),
    }

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        if _data.get("source", None) == UploadSourcesEnum.resource_file_upload.value:
            return True
        return False

    @staticmethod
    def has_serializer(data) -> bool:
        _base = data.get("base_file")
        if not _base:
            return False
        if (
            _base.endswith("xml") or _base.endswith("sld")
            if isinstance(_base, str)
            else _base.name.endswith("xml") or _base.name.endswith("sld")
        ):
            return MetadataFileSerializer
        return False

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        return {
            "dataset_title": _data.pop("dataset_title", None),
            "skip_existing_layers": _data.pop("skip_existing_layers", "False"),
            "overwrite_existing_layer": _data.pop("overwrite_existing_layer", "False"),
            "store_spatial_file": _data.pop("store_spatial_files", "True"),
            "source": _data.pop("source", "resource_file_upload"),
        }, _data

    @staticmethod
    def perform_last_step(execution_id):
        BaseHandler.perform_last_step(execution_id=execution_id)

    def import_resource(self, files: dict, execution_id: str, **kwargs):
        _exec = orchestrator.get_execution_object(execution_id)
        # getting the dataset
        alternate = _exec.input_params.get("dataset_title")
        resource_id = _exec.input_params.get("resource_id")
        if resource_id:
            dataset = get_object_or_404(Dataset, pk=resource_id)
        elif alternate:
            dataset = get_object_or_404(Dataset, alternate=alternate)

        # assign the resource to the execution_obj
        orchestrator.update_execution_request_obj(_exec, {"geonode_resource": dataset})

        # retrieving the handler used for the dataset
        original_handler = orchestrator.load_handler(dataset.resourcehandlerinfo_set.first().handler_module_path)()

        ResourceHandlerInfo.objects.create(
            handler_module_path=dataset.resourcehandlerinfo_set.first().handler_module_path,
            resource=dataset,
            execution_request=_exec,
            kwargs=kwargs.get("kwargs", {}) or kwargs,
        )

        self.handle_metadata_resource(_exec, dataset, original_handler)

        dataset.refresh_from_db()

        raise Exception("dajasdhjkhsadjkhasd")
        orchestrator.evaluate_execution_progress(execution_id, handler_module_path=str(self))
        return dataset

    def handle_metadata_resource(self, _exec, dataset, original_handler):
        raise NotImplementedError
