#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from pathlib import Path

from django.conf import settings

from geonode.base.models import ResourceBase
from geonode.documents.api.serializers import DocumentSerializer
from geonode.documents.models import Document
from geonode.upload.api.views import import_orchestrator
from geonode.upload.celery_tasks import BaseHandler
from geonode.upload.handlers.base import ImportException
from geonode.upload.handlers.utils import create_alternate
from geonode.upload.utils import ImporterRequestAction as ira
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.orchestrator import orchestrator
from geonode.resource.registry import resource_manager_registry

logger = logging.getLogger("importer")


class DocumentFileHandler(BaseHandler):
    """
    Handler to import any document files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    TASKS = {
        exa.UPLOAD.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
    }

    @property
    def supported_file_extension_config(self):
        return {}

    @property
    def can_handle_xml_file(self) -> bool:
        """
        True or false if the handler is able to handle XML file
        By default a common workflow is always defined
        To be override if some expection are needed
        """
        return False

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        base = _data.get("base_file")
        if not base:
            return False
        # if base and _data.get("action", exa.UPLOAD.value) == ira.DOCUMENT_UPLOAD.value:
        ext = base.split(".")[-1].lower()
        if ext in settings.ALLOWED_DOCUMENT_TYPES and base:
            return True
        return False

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Define basic validation steps:
        Upload limit:
            - raise exception if the layer number of the gpkg is greater than the max upload per user
            - raise exception if the actual upload + the gpgk layer is greater than the max upload limit
        """
        return True

    @staticmethod
    def can_do(action):
        return action in DocumentFileHandler.TASKS

    def extract_params_from_data(self, _data, action=None):
        """
        Extract the params from the data and return a dict with the params
        to be used in the task list
        """
        return {
            "action": _data.pop("action", exa.UPLOAD.value),
            "store_spatial_files": _data.pop("store_spatial_files", None),
            "skip_existing_layers": _data.pop("skip_existing_layers", None),
            "resource_pk": _data.pop("resource_pk", None),
        }, _data

    def import_resource(self, files: dict, execution_id: str, **kwargs):
        # for the moment we skip the dyanamic model creation
        logger.info("Total number of file available: 1")
        _exec = self._get_execution_request_object(execution_id)
        _input = {**_exec.input_params, **{"total_layers": 1}}
        orchestrator.update_execution_request_status(execution_id=str(execution_id), input_params=_input)

        try:
            filename = Path(files.get("base_file")).stem
            # start looping on the layers available
            doc_name = self.fixup_name(filename)

            should_be_overwritten = _exec.input_params.get("overwrite_existing_layer")
            # should_be_imported check if the user+layername already exists or not

            if _exec.input_params.get("resource_pk"):
                doc = Document.objects.filter(pk=_exec.input_params.get("resource_pk")).first()
                if not doc:
                    raise ImportException("The dataset selected for the ovewrite does not exists")
                if doc.is_vector():
                    raise Exception("cannot override a vector dataset with a raster one")
                alternate = doc.alternate.split(":")[-1]
                orchestrator.update_execution_request_obj(_exec, {"geonode_resource": doc})
            else:
                user_documents = Document.objects.filter(alternate=doc_name, owner=_exec.user)

                doc_exists = user_documents.exists()

                if doc_exists and should_be_overwritten:
                    doc_name, alternate = (
                        doc_name,
                        user_documents.first().alternate.split(":")[-1],
                    )
                elif not doc_exists:
                    alternate = doc_name
                else:
                    alternate = create_alternate(doc_name, execution_id)

            import_orchestrator.apply_async(
                (
                    files,
                    execution_id,
                    str(self),
                    "geonode.upload.import_resource",
                    doc_name,
                    alternate,
                    _exec.action,
                )
            )
            return doc_name, alternate, execution_id

        except Exception as e:
            logger.error(e)
            raise e
        return

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Document = Document,
        asset=None,
    ):
        _exec = self._get_execution_request_object(execution_id)

        saved_doc = resource_manager_registry.get_for_model(resource_type).create(
            None,
            resource_type=resource_type,
            defaults=self.generate_resource_payload(layer_name, alternate, asset, _exec, None),
        )

        saved_doc.refresh_from_db()

        self.handle_xml_file(saved_doc, _exec)

        ResourceBase.objects.filter(alternate=alternate).update(dirty_state=False)

        saved_doc.refresh_from_db()

        return saved_doc

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace, **kwargs):
        return dict(
            subtype="document",
            alternate=alternate,
            dirty_state=True,
            title=kwargs.get("title", layer_name),
            owner=_exec.user,
        )

    def perform_last_steps(self, resource, execution_id):
        resource_manager_registry.get_for_instance(resource).set_thumbnail(None, instance=resource)
