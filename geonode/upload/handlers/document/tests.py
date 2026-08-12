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
import os
import shutil
import zipfile
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.urls import reverse

from geonode import documents
from geonode.assets.models import Asset
from geonode.assets.utils import get_default_asset
from geonode.base.enumerations import SOURCE_TYPE_LOCAL, SOURCE_TYPE_REMOTE
from geonode.base.models import Link
from geonode.base.populate_test_data import create_single_doc
from geonode.documents.models import Document
from geonode.resource.models import ExecutionRequest
from geonode.upload.api.exceptions import InvalidInputFileException
from geonode.upload.celery_tasks import create_geonode_resource, import_resource
from geonode.upload.handlers.document.exceptions import InvalidDocumentException
from geonode.upload.handlers.document.handler import DocumentFileHandler
from geonode.upload.handlers.document.serializer import DocumentImporterSerializer
from geonode.upload.models import ResourceHandlerInfo, UploadSizeLimit
from geonode.upload.orchestrator import orchestrator
from geonode.upload.tests.utils import ImporterBaseTestSupport
from geonode.upload.utils import ImporterRequestAction as ira
from geonode.utils import mkdtemp

DOCUMENT_FIXTURE = os.path.join(os.path.dirname(documents.__file__), "tests", "data", "img.gif")
PDF_FIXTURE = os.path.join(os.path.dirname(documents.__file__), "tests", "data", "pdf_doc.pdf")


class TestDocumentFileHandler(ImporterBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = DocumentFileHandler()
        cls.handler_module_path = str(cls.handler)
        cls.upload_url = reverse("importer_upload")
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.remote_url = "https://example.org/documents/report.pdf"

    def setUp(self):
        # the uploaded file always lives in a temporary directory, as the importer does
        self.tempdir = mkdtemp()
        self.base_file = shutil.copy(DOCUMENT_FIXTURE, self.tempdir)
        self.files = {"base_file": self.base_file}

    def tearDown(self):
        shutil.rmtree(self.tempdir, ignore_errors=True)

    def _create_execution_request(self, action=ira.DOCUMENT_UPLOAD.value, **input_params):
        action = str(action)
        return str(
            orchestrator.create_execution_request(
                user=self.user,
                func_name="start_import",
                step="start_import",
                action=action,
                input_params={
                    **{"handler_module_path": self.handler_module_path, "action": action},
                    **input_params,
                },
            )
        )

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS[ira.DOCUMENT_UPLOAD.value]), 3)
        self.assertTupleEqual(expected, self.handler.TASKS[ira.DOCUMENT_UPLOAD.value])

    def test_task_list_is_the_expected_one_replace(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS[ira.DOCUMENT_REPLACE.value]), 3)
        self.assertTupleEqual(expected, self.handler.TASKS[ira.DOCUMENT_REPLACE.value])

    def test_task_list_is_the_expected_one_clone(self):
        expected = (
            "start_copy",
            "geonode.upload.copy_document_resource",
        )
        self.assertEqual(len(self.handler.TASKS[ira.DOCUMENT_COPY.value]), 2)
        self.assertTupleEqual(expected, self.handler.TASKS[ira.DOCUMENT_COPY.value])

    def test_copy_action_should_be_handled_as_a_clone(self):
        """The clone endpoint is shared with the other resources, it must fallback on the document clone"""
        self.assertTrue(self.handler.can_do("copy"))
        self.assertTupleEqual(self.handler.TASKS[ira.DOCUMENT_COPY.value], self.handler.get_task_list("copy"))

    def test_can_handle_should_return_true_for_document_actions(self):
        for action in [ira.DOCUMENT_UPLOAD.value, ira.DOCUMENT_REPLACE.value]:
            self.assertTrue(self.handler.can_handle({"action": action}))

    def test_can_handle_should_return_false_for_document_copy(self):
        """A clone carries no file, it must go through the copy endpoint, never this generic upload one"""
        self.assertFalse(self.handler.can_handle({"action": ira.DOCUMENT_COPY.value}))

    def test_can_handle_should_return_false_for_a_dataset_upload(self):
        self.assertFalse(self.handler.can_handle({"base_file": "test.gpkg", "action": "upload"}))

    def test_should_get_the_specific_serializer(self):
        actual = self.handler.has_serializer({"action": str(ira.DOCUMENT_UPLOAD.value)})
        self.assertEqual(DocumentImporterSerializer, actual)

    def test_should_not_get_the_specific_serializer_for_a_dataset(self):
        self.assertFalse(self.handler.has_serializer({"base_file": "test.gpkg", "action": "upload"}))

    def test_is_valid_should_pass_with_a_supported_document(self):
        self.assertTrue(self.handler.is_valid(files=self.files, user=self.user))

    def test_is_valid_should_raise_exception_if_the_file_type_is_not_allowed(self):
        with self.assertRaises(InvalidDocumentException) as _exc:
            self.handler.is_valid(files={"base_file": "invalid.file.foo"}, user=self.user)

        self.assertIn("This file type is not allowed", str(_exc.exception.detail))

    def test_is_valid_should_raise_exception_if_the_file_is_bigger_than_the_limit(self):
        limit, _ = UploadSizeLimit.objects.get_or_create(slug="document_upload_size")
        old_value = limit.max_size
        try:
            UploadSizeLimit.objects.filter(slug="document_upload_size").update(max_size=1)

            with self.assertRaises(InvalidDocumentException) as _exc:
                self.handler.is_valid(files=self.files, user=self.user)

            self.assertIn("File size exceeds", str(_exc.exception.detail))
        finally:
            limit.max_size = old_value
            limit.save()

    def test_is_valid_should_raise_exception_if_the_file_is_missing(self):
        with self.assertRaises(InvalidDocumentException):
            self.handler.is_valid(files={}, user=self.user)

    def test_is_valid_should_raise_exception_for_an_unsafe_zip(self):
        unsafe_zip = os.path.join(self.tempdir, "unsafe.zip")
        with zipfile.ZipFile(unsafe_zip, "w") as _zip:
            _zip.writestr("../../evil.txt", "escaping the extraction folder")

        with self.assertRaises(InvalidDocumentException) as _exc:
            self.handler.is_valid(files={"base_file": unsafe_zip}, user=self.user)

        self.assertIn("Invalid or unsafe ZIP archive", str(_exc.exception.detail))

    def test_is_valid_url_should_pass_for_a_remote_document(self):
        self.assertTrue(self.handler.is_valid_url(url=self.remote_url))

    def test_extract_params_from_data_should_fallback_the_title_to_the_file_name(self):
        actual, _files = self.handler.extract_params_from_data(
            {"base_file": self.base_file, "action": str(ira.DOCUMENT_UPLOAD.value)}
        )

        self.assertEqual("img.gif", actual["title"])
        self.assertEqual(ira.DOCUMENT_UPLOAD.value, actual["action"])
        # the url is set only for remote documents
        self.assertNotIn("url", actual)
        self.assertEqual({"base_file": self.base_file}, _files)

    def test_extract_params_from_data_should_keep_the_url_of_a_remote_document(self):
        actual, _files = self.handler.extract_params_from_data(
            {"url": self.remote_url, "action": str(ira.DOCUMENT_UPLOAD.value)}
        )

        self.assertEqual(self.remote_url, actual["url"])
        self.assertEqual("report.pdf", actual["title"])

    def test_extract_params_from_data_should_get_the_title_from_the_clone_defaults(self):
        for defaults in ['{"title": "cloned document"}', {"title": "cloned document"}]:
            actual, _files = self.handler.extract_params_from_data(
                {"defaults": defaults}, action=ira.DOCUMENT_COPY.value
            )

            self.assertEqual("cloned document", actual["title"])
            self.assertEqual(ira.DOCUMENT_COPY.value, actual["action"])
            # the clone does not require any file
            self.assertNotIn("base_file", actual)

    def test_extract_params_from_data_should_get_the_clone_payload_from_the_action_of_the_data(self):
        """The upload endpoint does not provide the action, is taken from the payload"""
        actual, _files = self.handler.extract_params_from_data(
            {"title": "cloned document", "resource_pk": 1, "action": ira.DOCUMENT_COPY.value}
        )

        self.assertEqual({"title": "cloned document", "resource_pk": 1, "action": ira.DOCUMENT_COPY.value}, actual)

    def test_get_extension(self):
        self.assertEqual("gif", self.handler.get_extension({"files": self.files}))
        self.assertEqual("pdf", self.handler.get_extension({"url": self.remote_url}))
        self.assertEqual("jpg", self.handler.get_extension({"extension": ".JPG", "files": self.files}))

    @patch("geonode.upload.handlers.common.document.import_orchestrator")
    def test_import_resource_should_continue_with_the_resource_creation(self, patch_orchestrator):
        patch_orchestrator.apply_async.side_effect = MagicMock()
        exec_id = self._create_execution_request(title="img.gif", files=self.files)

        self.handler.import_resource(files=self.files, execution_id=exec_id)

        patch_orchestrator.apply_async.assert_called_once()
        _exec = orchestrator.get_execution_object(exec_id)
        self.assertEqual(1, _exec.input_params["total_layers"])

    def test_create_geonode_resource_should_create_the_document(self):
        exec_id = self._create_execution_request(title="my new document", files=self.files)

        document = self.handler.create_geonode_resource("my_new_document", "my_new_document", exec_id)

        self.assertEqual("my new document", document.title)
        self.assertEqual("gif", document.extension)
        self.assertEqual(self.user, document.owner)
        self.assertEqual(SOURCE_TYPE_LOCAL, document.sourcetype)
        self.assertTrue(document.files)

    def test_create_geonode_resource_should_create_a_remote_document(self):
        exec_id = self._create_execution_request(title="my remote document", url=self.remote_url, files={})

        document = self.handler.create_geonode_resource("my_remote_document", "my_remote_document", exec_id)

        self.assertEqual(self.remote_url, document.doc_url)
        self.assertEqual("pdf", document.extension)
        self.assertEqual(SOURCE_TYPE_REMOTE, document.sourcetype)
        self.assertFalse(document.is_local)

    def test_overwrite_geonode_resource_should_replace_the_document_with_a_local_file(self):
        document = create_single_doc("document to replace")
        exec_id = self._create_execution_request(
            action=ira.DOCUMENT_REPLACE.value,
            title=document.title,
            resource_pk=document.pk,
            files=self.files,
        )

        replaced = self.handler.overwrite_geonode_resource(document.title, document.title, exec_id)

        self.assertEqual(document.pk, replaced.pk)
        self.assertEqual("gif", replaced.extension)
        self.assertEqual(SOURCE_TYPE_LOCAL, replaced.sourcetype)

    def test_overwrite_geonode_resource_should_replace_the_document_with_a_remote_one(self):
        document = create_single_doc("document to replace with url")
        exec_id = self._create_execution_request(
            action=ira.DOCUMENT_REPLACE.value,
            title=document.title,
            resource_pk=document.pk,
            url=self.remote_url,
            files={},
        )

        replaced = self.handler.overwrite_geonode_resource(document.title, document.title, exec_id)

        self.assertEqual(document.pk, replaced.pk)
        self.assertEqual(self.remote_url, replaced.doc_url)
        self.assertEqual(SOURCE_TYPE_REMOTE, replaced.sourcetype)
        # the file of the document is dropped, a remote document has no asset
        self.assertEqual(0, Asset.objects.filter(link__resource=replaced).count())

    @override_settings(EXIF_ENABLED=True)
    @patch("geonode.documents.exif.utils.exif_extract_metadata_doc")
    def test_overwrite_geonode_resource_should_evaluate_the_exif_of_the_new_file(self, exif_extract_metadata_doc):
        exif_extract_metadata_doc.return_value = {
            "abstract": "abstract from the exif",
            "keywords": ["exif_keyword"],
            "bbox": [0, 1, 0, 1],
        }
        document = create_single_doc("document to replace with an image with exif")
        exec_id = self._create_execution_request(
            action=ira.DOCUMENT_REPLACE.value,
            title=document.title,
            resource_pk=document.pk,
            files=self.files,
        )

        replaced = self.handler.overwrite_geonode_resource(document.title, document.title, exec_id)

        self.assertEqual("abstract from the exif", replaced.abstract)
        self.assertIn("exif_keyword", replaced.keywords.values_list("name", flat=True))
        self.assertEqual((0.0, 0.0, 1.0, 1.0), replaced.bbox_polygon.extent)

    def test_overwrite_geonode_resource_should_raise_exception_if_the_document_does_not_exists(self):
        exec_id = self._create_execution_request(
            action=ira.DOCUMENT_REPLACE.value, title="missing", resource_pk=99999999, files=self.files
        )

        with self.assertRaises(InvalidDocumentException) as _exc:
            self.handler.overwrite_geonode_resource("missing", "missing", exec_id)

        self.assertIn("does not exists", str(_exc.exception.detail))

    def test_overwrite_geonode_resource_should_raise_exception_if_the_user_cannot_edit_it(self):
        document = create_single_doc("document not editable")
        not_owner = get_user_model().objects.create_user(username="not_owner", password="notowner")
        exec_id = str(
            orchestrator.create_execution_request(
                user=not_owner,
                func_name="start_import",
                step="start_import",
                action=ira.DOCUMENT_REPLACE.value,
                input_params={"resource_pk": document.pk, "title": document.title, "files": self.files},
            )
        )

        with self.assertRaises(InvalidDocumentException) as _exc:
            self.handler.overwrite_geonode_resource(document.title, document.title, exec_id)

        self.assertIn("does not have permission", str(_exc.exception.detail))

    def test_create_asset_and_link_should_be_skipped_for_a_new_document(self):
        """The asset of a new document is created by the document manager"""
        exec_id = self._create_execution_request(title="my new document with asset", files=self.files)
        document = self.handler.create_geonode_resource("my_new_document", "my_new_document", exec_id)
        expected_asset = get_default_asset(document)

        self.assertIsNone(self.handler.create_asset_and_link(document, self.files, action=ira.DOCUMENT_UPLOAD.value))
        self.assertEqual(expected_asset.pk, get_default_asset(document).pk)

    def test_overwrite_geonode_resource_should_swap_the_asset_and_the_extension(self):
        """The extension is taken from the new file, the document post_save reads it from the linked asset"""
        document = create_single_doc("document with a gif to replace with a pdf")
        old_asset = get_default_asset(document)
        pdf_file = shutil.copy(PDF_FIXTURE, self.tempdir)
        exec_id = self._create_execution_request(
            action=ira.DOCUMENT_REPLACE.value,
            title=document.title,
            resource_pk=document.pk,
            files={"base_file": pdf_file},
        )

        replaced = self.handler.overwrite_geonode_resource(document.title, document.title, exec_id)

        self.assertEqual("pdf", replaced.extension)
        self.assertFalse(Asset.objects.filter(pk=old_asset.pk).exists())
        self.assertEqual(1, Asset.objects.filter(link__resource=replaced).count())
        self.assertTrue(replaced.files[0].endswith("pdf_doc.pdf"))
        # the download link must follow the new file
        download_link = Link.objects.filter(resource=replaced.resourcebase_ptr, link_type="data").first()
        self.assertEqual("pdf", download_link.extension)
        self.assertEqual("application/pdf", download_link.mime)

    def test_copy_geonode_resource_should_clone_the_document(self):
        document = create_single_doc("document to clone")
        exec_id = self._create_execution_request(action=ira.DOCUMENT_COPY.value, title="cloned document")
        _exec = orchestrator.get_execution_object(exec_id)

        cloned = self.handler.copy_geonode_resource(document, _exec)

        self.assertNotEqual(document.pk, cloned.pk)
        self.assertEqual("cloned document", cloned.title)
        self.assertTrue(cloned.files)

    def test_copy_geonode_resource_should_clone_a_remote_document(self):
        document = create_single_doc("remote document to clone")
        document.doc_url = self.remote_url
        document.sourcetype = SOURCE_TYPE_REMOTE
        document.save()
        exec_id = self._create_execution_request(action=ira.DOCUMENT_COPY.value, title="cloned remote document")
        _exec = orchestrator.get_execution_object(exec_id)

        cloned = self.handler.copy_geonode_resource(document, _exec)

        self.assertNotEqual(document.pk, cloned.pk)
        self.assertEqual(self.remote_url, cloned.doc_url)
        self.assertEqual(SOURCE_TYPE_REMOTE, cloned.sourcetype)

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    def test_replace_should_not_duplicate_the_resource_handler_info(self, _):
        document = create_single_doc("document to replace once")
        exec_id = self._create_execution_request(
            action=ira.DOCUMENT_REPLACE.value,
            title=document.title,
            resource_pk=document.pk,
            files=self.files,
        )
        self.handler.create_resourcehandlerinfo(
            self.handler_module_path, document, orchestrator.get_execution_object(exec_id)
        )

        create_geonode_resource(
            exec_id,
            step_name="geonode.upload.create_geonode_resource",
            layer_name=document.title,
            alternate=document.title,
            handler_module_path=self.handler_module_path,
            action=ira.DOCUMENT_REPLACE.value,
        )

        document.refresh_from_db()
        self.assertEqual("gif", document.extension)
        self.assertEqual(1, ResourceHandlerInfo.objects.filter(resource=document).count())

    @patch("geonode.upload.celery_tasks.call_rollback_function")
    def test_import_resource_failure_should_rollback_with_the_document_action(self, call_rollback):
        """The rollback must be called with the document action, the generic upload one is not in the task list"""
        exec_id = self._create_execution_request(title="invalid document", files={})

        with self.assertRaises(InvalidInputFileException):
            import_resource(exec_id, handler_module_path=self.handler_module_path, action=ira.DOCUMENT_UPLOAD.value)

        self.assertEqual(ira.DOCUMENT_UPLOAD.value, call_rollback.call_args.kwargs["prev_action"])

    def test_create_geonode_resource_rollback_should_delete_the_document(self):
        exec_id = self._create_execution_request(title="document to rollback", files=self.files)
        document = self.handler.create_geonode_resource("document_to_rollback", "document_to_rollback", exec_id)
        orchestrator.update_execution_request_obj(
            orchestrator.get_execution_object(exec_id), {"geonode_resource": document}
        )

        self.handler._create_geonode_resource_rollback(exec_id)

        self.assertFalse(Document.objects.filter(pk=document.pk).exists())

    def test_create_geonode_resource_rollback_should_keep_the_replaced_document(self):
        document = create_single_doc("replaced document to rollback")
        exec_id = self._create_execution_request(
            action=ira.DOCUMENT_REPLACE.value, title=document.title, resource_pk=document.pk, files=self.files
        )
        orchestrator.update_execution_request_obj(
            orchestrator.get_execution_object(exec_id), {"geonode_resource": document}
        )

        self.handler._create_geonode_resource_rollback(exec_id)

        self.assertTrue(Document.objects.filter(pk=document.pk).exists())

    def test_copy_document_resource_rollback_should_delete_the_clone(self):
        document = create_single_doc("cloned document to rollback")
        exec_id = self._create_execution_request(action=ira.DOCUMENT_COPY.value)
        orchestrator.update_execution_request_status(
            execution_id=exec_id, output_params={"output": {"uuid": str(document.uuid)}}
        )

        self.handler._copy_document_resource_rollback(exec_id)

        self.assertFalse(Document.objects.filter(pk=document.pk).exists())

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_document_upload_should_create_the_execution_request(self, patch_orchestrator):
        patch_orchestrator.s.return_value = MagicMock()
        self.client.force_login(self.user)

        with open(self.base_file, "rb") as _file:
            response = self.client.post(
                self.upload_url, data={"base_file": _file, "action": str(ira.DOCUMENT_UPLOAD.value)}
            )

        self.assertEqual(201, response.status_code)
        _exec = orchestrator.get_execution_object(response.json()["execution_id"])
        self.assertEqual(ira.DOCUMENT_UPLOAD.value, _exec.action)
        self.assertEqual(self.handler_module_path, _exec.input_params["handler_module_path"])
        self.assertEqual("img.gif", _exec.input_params["title"])

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_remote_document_upload_should_create_the_execution_request(self, patch_orchestrator):
        patch_orchestrator.s.return_value = MagicMock()
        self.client.force_login(self.user)
        document = create_single_doc("cloned document to rollback")

        exec_id = self._create_execution_request(action=ira.DOCUMENT_COPY.value, title="cloned document")
        self.handler.create_resourcehandlerinfo(
            self.handler_module_path, document, orchestrator.get_execution_object(exec_id)
        )
        _url = reverse("importer_resource_copy", args=[document.id])

        response = self.client.put(
            _url,
            data=json.dumps(
                {"action": str(ira.DOCUMENT_CLONE.value), "title": "cloned document", "resource_pk": document.pk}
            ),
            content_type="application/json",
        )

        self.assertEqual(200, response.status_code)

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_document_clone_should_not_require_any_file(self, patch_orchestrator):
        document = create_single_doc("document to clone from the upload endpoint")
        self.client.force_login(self.user)
        exec_id = self._create_execution_request(action=ira.DOCUMENT_COPY.value, title="cloned document")
        self.handler.create_resourcehandlerinfo(
            self.handler_module_path, document, orchestrator.get_execution_object(exec_id)
        )
        _url = reverse("importer_resource_copy", args=[document.id])

        response = self.client.put(
            _url,
            data=json.dumps(
                {"action": str(ira.DOCUMENT_COPY.value), "title": "cloned document", "resource_pk": document.pk}
            ),
            content_type="application/json",
        )

        self.assertEqual(200, response.status_code)
        _exec = orchestrator.get_execution_object(response.json()["execution_id"])
        # the clone starts from the copy step, there is nothing to import
        self.assertEqual("start_copy", _exec.func_name)
        self.assertEqual(document.pk, _exec.geonode_resource.pk)
        self.assertEqual("cloned document", _exec.input_params["title"])

    @override_settings(ASYNC_SIGNALS=False)
    @patch.dict(os.environ, {"ASYNC_SIGNALS": "False"})
    def test_document_clone_should_fail_without_the_title_or_the_document_to_clone(self):
        self.client.force_login(self.user)
        document = create_single_doc("document to clone from the upload endpoint")
        self.client.force_login(self.user)
        exec_id = self._create_execution_request(action=ira.DOCUMENT_COPY.value, title="cloned document")
        self.handler.create_resourcehandlerinfo(

        self.assertEqual(500, response.status_code)

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_document_clone_from_the_copy_endpoint_should_create_the_execution_request(self, patch_orchestrator):
        patch_orchestrator.s.return_value = MagicMock()
        document = create_single_doc("document to clone from the api")
        exec_id = self._create_execution_request(action=ira.DOCUMENT_COPY.value, title="cloned document")
        self.handler.create_resourcehandlerinfo(
            self.handler_module_path, document, orchestrator.get_execution_object(exec_id)
        )
        self.client.force_login(self.user)

        response = self.client.put(
            reverse("importer_resource_copy", kwargs={"pk": document.pk}),
            data=json.dumps({"action": str(ira.DOCUMENT_COPY.value), "title": "cloned document"}),
            content_type="application/json",
        )

        self.assertEqual(200, response.status_code)
        _exec = orchestrator.get_execution_object(response.json()["execution_id"])
        self.assertEqual("cloned document", _exec.input_params["title"])
        self.assertEqual(document.pk, _exec.geonode_resource.pk)

    def test_document_upload_should_fail_without_a_file_or_a_url(self):
        self.client.force_login(self.user)

        response = self.client.post(self.upload_url, data={"action": str(ira.DOCUMENT_UPLOAD.value)})

        self.assertEqual(400, response.status_code)
        self.assertFalse(ExecutionRequest.objects.filter(action=ira.DOCUMENT_UPLOAD.value).exists())

    def test_document_replace_should_fail_without_the_resource_pk(self):
        self.client.force_login(self.user)

        with open(self.base_file, "rb") as _file:
            response = self.client.post(
                self.upload_url, data={"base_file": _file, "action": str(ira.DOCUMENT_REPLACE.value)}
            )

        self.assertEqual(500, response.status_code)
