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
import json
import logging
import os
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils import timezone
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy

from geonode.assets.models import Asset
from geonode.base import enumerations
from geonode.base.bbox_utils import BBOXHelper
from geonode.base.models import Link
from geonode.documents.models import Document
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.resource.models import ExecutionRequest
from geonode.resource.registry import document_manager
from geonode.security.registry import permissions_registry
from geonode.upload.api.exceptions import CopyResourceException
from geonode.upload.celery_app import importer_app
from geonode.upload.celery_tasks import UpdateTaskClass, import_orchestrator
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.document.exceptions import InvalidDocumentException
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.orchestrator import orchestrator
from geonode.upload.settings import IMPORTER_RESOURCE_COPY_RATE_LIMIT
from geonode.upload.utils import (
    call_on_failure,
    call_rollback_function,
    get_max_upload_size,
    ImporterRequestAction as ira,
)
from geonode.upload.zip_validation import ZipValidationError, is_zip_extension, validate_safe_zip

logger = logging.getLogger("importer")


class BaseDocumentFileHandler(BaseHandler):
    """
    Handler to import documents into GeoNode
    It must provide the task_lists required to complete the upload
    A document does not need to be published, so no GeoServer step is defined
    """

    handler_type = "document"

    TASKS = {
        ira.DOCUMENT_UPLOAD.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        ),
        ira.DOCUMENT_REPLACE.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        ),
        ira.DOCUMENT_COPY.value: (
            "start_copy",
            "geonode.upload.copy_document_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
    }

    @property
    def have_table(self):
        return False

    @classmethod
    def get_task_list(cls, action) -> tuple:
        # the copy endpoint is shared with the other resources, for a document it means a clone
        if action == exa.COPY.value:
            action = ira.DOCUMENT_COPY.value
        return super().get_task_list(action)

    @staticmethod
    def can_do(action) -> bool:
        return action in BaseDocumentFileHandler.TASKS or action == exa.COPY.value

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        The file is validated as the document form does: allowed type and size limit
        """
        base_file = files.get("base_file") if files else None
        if not base_file:
            raise InvalidDocumentException("A document must have a file or a url")

        if Path(base_file).suffix.lower().replace(".", "") not in settings.ALLOWED_DOCUMENT_TYPES:
            raise InvalidDocumentException("This file type is not allowed")

        if is_zip_extension(base_file):
            # zip based documents (zip itself, but also the OOXML/ODF ones) are inspected
            # before being persisted, as the document form does
            try:
                validate_safe_zip(base_file)
            except ZipValidationError:
                logger.warning("ZIP validation failed for uploaded document.", exc_info=True)
                raise InvalidDocumentException("Invalid or unsafe ZIP archive.")

        max_size = get_max_upload_size("document_upload_size")
        if os.path.getsize(base_file) > max_size:
            raise InvalidDocumentException(
                f"File size exceeds {filesizeformat(max_size)}. Please try again with a smaller file."
            )
        return True

    @staticmethod
    def is_valid_url(url, **kwargs):
        """
        The url of a remote document is validated by the serializer and never fetched,
        as the document form does
        """
        return True

    @staticmethod
    def extract_params_from_data(_data, action=None):
        """
        Remove from the _data the params that needs to save into the executionRequest object
        all the other are returned
        """
        action = action or _data.get("action")

        if action in (exa.COPY.value, ira.DOCUMENT_COPY.value):
            # a clone carries no file: the title of the new document and the document to clone
            # (the resource_pk, or the pk in the path of the copy endpoint) are the only input
            defaults = _data.get("defaults") or {}
            if isinstance(defaults, str):
                defaults = json.loads(defaults)
            # the action is stringified: it can come from the enum, which is a lazy translation
            payload = {"title": _data.get("title") or defaults.get("title"), "action": str(action)}
            if _data.get("resource_pk"):
                payload["resource_pk"] = _data.get("resource_pk")
            return payload, _data

        payload = {
            "title": _data.pop("title", None) or BaseDocumentFileHandler.default_title(_data),
            "extension": _data.pop("extension", None),
            "resource_pk": _data.pop("resource_pk", None),
            "action": _data.pop("action"),
        }
        url = _data.pop("url", None)
        if url:
            # the url is set only for remote documents, is used to select the validation to perform
            payload["url"] = url
        return payload, _data

    @staticmethod
    def default_title(_data):
        """
        As the document form does, the title falls back to the name of the file or of the remote url
        """
        base_file = _data.get("base_file")
        if base_file:
            return Path(getattr(base_file, "name", base_file)).name
        url = _data.get("url") or ""
        return os.path.basename(urlparse(url).path) or url

    @staticmethod
    def get_extension(params):
        """
        The extension is provided by the payload, if missing is taken from the file/url name
        """
        source = (params.get("files") or {}).get("base_file") or urlparse(params.get("url") or "").path
        extension = params.get("extension") or Path(source).suffix
        return extension.replace(".", "").lower()

    def import_resource(self, files: dict, execution_id: str, **kwargs):
        """
        A document does not require any processing of the file,
        we can directly move to the creation of the resource
        """
        logger.info("Total number of resource available: 1")
        _exec = self._get_execution_request_object(execution_id)
        _input = {**_exec.input_params, **{"total_layers": 1}}
        orchestrator.update_execution_request_status(execution_id=str(execution_id), input_params=_input)

        document_name = self.fixup_name(_exec.input_params.get("title"))

        import_orchestrator.apply_async(
            (
                files,
                execution_id,
                str(self),
                "geonode.upload.import_resource",
                document_name,
                document_name,
                _exec.action,
            )
        )
        return document_name, document_name, execution_id

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Document = Document,
        asset=None,
        **kwargs,
    ):
        """
        Create the document (local or remote) as the document upload form does
        """
        _exec = self._get_execution_request_object(execution_id)

        resource = document_manager.create(
            None,
            resource_type=resource_type,
            defaults=self.generate_resource_payload(layer_name, _exec, **_exec.input_params.copy()),
        )
        return self.handle_metadata(resource)

    def generate_resource_payload(self, layer_name, _exec, **kwargs):
        title = kwargs.get("title") or layer_name
        extension = self.get_extension(kwargs)

        if kwargs.get("url"):
            return dict(
                owner=_exec.user,
                doc_url=kwargs.get("url"),
                title=title,
                extension=extension,
                sourcetype=enumerations.SOURCE_TYPE_REMOTE,
            )

        return dict(
            owner=_exec.user,
            title=title,
            extension=extension,
            link_type="uploaded",  # should be in geonode.base.enumerations.LINK_TYPES
            data_title=title,
            data_type=extension,
            files=[kwargs.get("files", {}).get("base_file")],
        )

    def handle_metadata(self, resource):
        """
        Enrich the document with the EXIF metadata, as the document upload form does
        """
        abstract, date, bbox = None, None, None
        keywords = []

        if getattr(settings, "EXIF_ENABLED", False):
            try:
                from geonode.documents.exif.utils import exif_extract_metadata_doc

                exif_metadata = exif_extract_metadata_doc(resource)
                if exif_metadata:
                    date = exif_metadata.get("date", None)
                    keywords.extend(exif_metadata.get("keywords", []))
                    bbox = exif_metadata.get("bbox", None)
                    abstract = exif_metadata.get("abstract", None)
            except Exception:
                logger.debug("Exif extraction failed.")

        vals = dict(abstract=abstract, date=date, date_type="Creation")
        if bbox:
            # the bbox is set only when the file provides it, on replace the existing one is preserved
            bbox_polygon = BBOXHelper.from_xy(bbox).as_polygon()
            vals.update(bbox_polygon=bbox_polygon, ll_bbox_polygon=bbox_polygon)

        document_manager.update(
            resource.uuid,
            instance=resource,
            keywords=keywords,
            regions=[],
            vals=vals,
            notify=True,
        )
        resource.refresh_from_db()
        return resource

    def overwrite_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Document = Document,
        asset=None,
        **kwargs,
    ):
        """
        Replace the file (or the url) of an existing document. The metadata are preserved,
        only the ones provided by the EXIF of the new file are updated
        """
        _exec = self._get_execution_request_object(execution_id)
        params = _exec.input_params.copy()

        document = resource_type.objects.filter(pk=params.get("resource_pk")).first()
        if not document:
            raise InvalidDocumentException("The document selected for the replace does not exists")

        if not permissions_registry.user_has_perm(_exec.user, perm="change_resourcebase", instance=document):
            raise InvalidDocumentException(
                f"User does not have permission to replace the document '{document.title}'. "
                f"'edit' or 'manage' permission is required."
            )

        url = params.get("url")
        # the asset must be swapped before the update: the document post_save takes the
        # extension and the subtype from the file that is linked to the resource
        self.swap_asset(document, params.get("files") or {})
        document = document_manager.update(
            document.uuid,
            instance=document,
            vals=dict(
                extension=self.get_extension(params),
                doc_url=url,
                sourcetype=enumerations.SOURCE_TYPE_REMOTE if url else enumerations.SOURCE_TYPE_LOCAL,
            ),
        )
        document = self.handle_metadata(document)
        document_manager.set_thumbnail(document.uuid, instance=document, overwrite=True)
        document.refresh_from_db()
        return document

    def swap_asset(self, resource, files):
        """
        Drop the asset of the document in favour of the new file, a remote document has no asset.
        The download link is dropped as well, the document post_save creates it again with the
        extension and the mime type of the new file
        """
        Link.objects.filter(resource=resource.resourcebase_ptr, link_type="data").delete()

        # the asset link is removed in cascade with the asset
        for asset in Asset.objects.filter(link__resource=resource):
            asset.delete()

        # the asset link is "uploaded" as the one created with the document, the "data" link_type
        # is reserved to the download link that the post_save creates
        return super().create_asset_and_link(resource, files, link_type="uploaded")

    def create_asset_and_link(self, resource, files, action=None, **kwargs):
        """
        The asset of a new document is created by the document manager, on replace it is
        swapped by the overwrite step, before the document is updated
        """
        return

    def copy_geonode_resource(self, document: Document, _exec: ExecutionRequest, **kwargs):
        """
        Clone the document, the file is cloned along with the asset
        """
        defaults = {"title": _exec.input_params["title"]} if _exec.input_params.get("title") else {}
        return document_manager.copy(document, owner=_exec.user, defaults=defaults)

    def create_resourcehandlerinfo(
        self,
        handler_module_path: str,
        resource: Document,
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

    @staticmethod
    def perform_last_step(execution_id):
        _exec = BaseHandler.perform_last_step(execution_id=execution_id)
        BaseHandler.remove_temporary_file(_exec)

    def _create_geonode_resource_rollback(self, exec_id, istance_name=None, *args, **kwargs):
        """
        A document has no alternate, the resource created is retrieved from the execution request
        """
        _exec = orchestrator.get_execution_object(exec_id)
        if _exec.action == ira.DOCUMENT_REPLACE.value:
            # the document already existed before the execution, must not be removed
            return
        logger.info(f"Rollback geonode step in progress for execid: {exec_id}")
        if _exec.geonode_resource:
            _exec.geonode_resource.delete()

    def _copy_document_resource_rollback(self, exec_id, istance_name=None, *args, **kwargs):
        """
        The cloned document is removed
        """
        logger.info(f"Rollback clone step in progress for execid: {exec_id}")
        _exec = orchestrator.get_execution_object(exec_id)
        uuid = (_exec.output_params or {}).get("output", {}).get("uuid")
        if uuid:
            Document.objects.filter(uuid=uuid).delete()


@importer_app.task(
    bind=True,
    base=UpdateTaskClass,
    name="geonode.upload.copy_document_resource",
    queue="geonode.upload.copy_document_resource",
    max_retries=1,
    rate_limit=IMPORTER_RESOURCE_COPY_RATE_LIMIT,
    ignore_result=False,
    task_track_started=True,
)
def copy_document_resource(self, execution_id, /, handler_module_path, action, **kwargs):
    """
    Clone the document assigned to the execution request.
    A document has no alternate, so the step is called by the orchestrator
    without the layer information, as it happens for the import_resource task
    """
    try:
        orchestrator.update_execution_request_status(
            execution_id=execution_id,
            last_updated=timezone.now(),
            func_name="copy_document_resource",
            step=gettext_lazy("geonode.upload.copy_document_resource"),
            celery_task_request=self.request,
        )
        _exec = orchestrator.get_execution_object(execution_id)

        if not _exec.geonode_resource:
            raise CopyResourceException("The resource requested does not exists")

        document = _exec.geonode_resource.get_real_instance()
        handler = import_string(handler_module_path)()

        new_document = handler.copy_geonode_resource(document, _exec)
        handler.create_resourcehandlerinfo(handler_module_path, new_document, _exec, **kwargs)

        orchestrator.update_execution_request_status(
            execution_id=str(execution_id),
            input_params={**_exec.input_params, **{"instance": document.pk, "uuid": document.uuid}},
            output_params={"output": {"uuid": str(new_document.uuid)}},
        )

        import_orchestrator.apply_async(
            (
                {},
                execution_id,
                handler_module_path,
                "geonode.upload.copy_document_resource",
                None,
                None,
                action,
            )
        )
        return self.name, execution_id

    except Exception as e:
        call_rollback_function(
            execution_id,
            handlers_module_path=handler_module_path,
            prev_action=action,
            error=e,
            **kwargs,
        )

        logger.exception(
            "Failed to copy document resource for execution_id=%s in copy_document_resource",
            execution_id,
        )

        # Explicitly call on_failure only if running in sync mode
        call_on_failure(self, e, execution_id, handler_module_path, action, kwargs)
        raise CopyResourceException(detail="An internal error occurred while copying the document resource.")
