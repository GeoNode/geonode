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
import os
import uuid
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from geonode.tests.base import GeoNodeBaseTestSupport
from unittest.mock import patch
from geonode.upload.api.exceptions import ImportException
from geonode.upload.api.serializer import ImporterSerializer
from geonode.upload.handlers.base import BaseHandler
from geonode.upload.handlers.shapefile.serializer import ShapeFileSerializer
from geonode.upload.orchestrator import ImportOrchestrator
from django.utils import timezone
from django_celery_results.models import TaskResult
from geonode.assets.handlers import asset_handler_registry

from geonode.resource.models import ExecutionRequest

# Create your tests here.


class TestsImporterOrchestrator(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.orchestrator = ImportOrchestrator()

    def test_get_handler(self):
        _data = {"base_file": "file.gpkg", "action": "upload"}
        actual = self.orchestrator.get_handler(_data)
        self.assertIsNotNone(actual)
        self.assertEqual("geonode.upload.handlers.gpkg.handler.GPKGFileHandler", str(actual))

    def test_get_handler_should_return_none_if_is_not_available(self):
        _data = {"base_file": "file.not_supported"}
        actual = self.orchestrator.get_handler(_data)
        self.assertIsNone(actual)

    def test_get_serializer_should_return_the_default_one_for_if_not_specified(self):
        actual = self.orchestrator.get_serializer({"base_file": "file.gpkg"})
        self.assertEqual(type(ImporterSerializer), type(actual))

    def test_get_serializer_should_return_the_specific_one(self):
        actual = self.orchestrator.get_serializer({"base_file": "file.shp"})
        self.assertEqual(type(ShapeFileSerializer), type(actual))

    def test_load_handler_raise_error_if_not_exists(self):
        with self.assertRaises(ImportException) as _exc:
            self.orchestrator.load_handler("invalid_type")
        self.assertEqual(
            str(_exc.exception.detail),
            "The handler is not available: invalid_type",
        )

    def test_load_handler(self):
        actual = self.orchestrator.load_handler("geonode.upload.handlers.gpkg.handler.GPKGFileHandler")
        self.assertIsInstance(actual(), BaseHandler)

    def test_load_handler_by_id(self):
        actual = self.orchestrator.load_handler_by_id("gpkg")
        self.assertIsInstance(actual(), BaseHandler)

    def test_get_execution_object_raise_exp_if_not_exists(self):
        with self.assertRaises(ImportException) as _exc:
            self.orchestrator.get_execution_object(str(uuid.uuid4()))

        self.assertEqual(str(_exc.exception.detail), "The selected UUID does not exists")

    def test_get_execution_object_retrun_exp(self):
        _uuid = str(uuid.uuid4())
        ExecutionRequest.objects.create(exec_id=_uuid, func_name="test")
        try:
            _exec = self.orchestrator.get_execution_object(_uuid)
            self.assertIsNotNone(_exec)
        finally:
            ExecutionRequest.objects.filter(exec_id=_uuid).delete()

    def test_create_execution_request(self):
        handler = self.orchestrator.load_handler("geonode.upload.handlers.gpkg.handler.GPKGFileHandler")
        count = ExecutionRequest.objects.count()
        input_files = {
            "files": {"base_file": "/tmp/file.txt"},
            "store_spatial_files": True,
        }
        exec_id = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name=next(iter(handler.get_task_list(action="upload"))),
            step=next(iter(handler.get_task_list(action="upload"))),
            input_params={
                "files": {"base_file": "/tmp/file.txt"},
                "store_spatial_files": True,
            },
            action="upload",
        )
        exec_obj = ExecutionRequest.objects.filter(exec_id=exec_id).first()
        self.assertEqual(count + 1, ExecutionRequest.objects.count())
        self.assertDictEqual(input_files, exec_obj.input_params)
        self.assertEqual(exec_obj.STATUS_READY, exec_obj.status)

    @patch("geonode.upload.orchestrator.importer_app.tasks.get")
    def test_perform_next_step(self, mock_celery):
        # setup test
        handler = self.orchestrator.load_handler("geonode.upload.handlers.gpkg.handler.GPKGFileHandler")
        _id = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name=next(iter(handler.get_task_list(action="upload"))),
            step="start_import",  # adding the first step for the GPKG file
            input_params={
                "files": {"base_file": "/tmp/file.txt"},
                "store_spatial_files": True,
            },
        )
        # test under tests
        self.orchestrator.perform_next_step(
            _id,
            "upload",
            step="start_import",
            handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
        )
        mock_celery.assert_called_once()
        mock_celery.assert_called_with("geonode.upload.import_resource")

    @override_settings(MEDIA_ROOT="/tmp/")
    @patch("geonode.upload.orchestrator.importer_app.tasks.get")
    def test_perform_last_import_step(self, mock_celery):
        # setup test
        handler = self.orchestrator.load_handler("geonode.upload.handlers.gpkg.handler.GPKGFileHandler")
        _id = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name=next(iter(handler.get_task_list(action="upload"))),
            step="geonode.upload.create_geonode_resource",  # adding the first step for the GPKG file
            input_params={
                "files": {"base_file": "/tmp/file.txt"},
                "store_spatial_files": True,
            },
            action="upload",
        )
        # test under tests
        self.orchestrator.perform_next_step(
            _id,
            "upload",
            step="geonode.upload.create_geonode_resource",
            handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
        )
        mock_celery.assert_not_called()

    @patch("geonode.upload.orchestrator.importer_app.tasks.get")
    def test_perform_with_error_set_invalid_status(self, mock_celery):
        mock_celery.side_effect = Exception("test exception")
        # setup test
        handler = self.orchestrator.load_handler("geonode.upload.handlers.gpkg.handler.GPKGFileHandler")
        _id = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name=next(iter(handler.get_task_list(action="upload"))),
            step="start_import",  # adding the first step for the GPKG file
            input_params={
                "files": {"base_file": "/tmp/file.txt"},
                "store_spatial_files": True,
            },
        )
        # test under tests
        with self.assertRaises(Exception):
            self.orchestrator.perform_next_step(
                _id,
                "upload",
                step="start_import",
                handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
            )

        _excec = ExecutionRequest.objects.filter(exec_id=_id).first()
        self.assertIsNotNone(_excec)
        self.assertEqual(ExecutionRequest.STATUS_FAILED, _excec.status)

    def test_set_as_failed(self):
        # creating the temporary file that will be deleted
        os.makedirs(settings.ASSETS_ROOT, exist_ok=True)

        fake_path = f"{settings.ASSETS_ROOT}to_be_deleted_file.txt"
        with open(fake_path, "w"):
            pass

        user = get_user_model().objects.first()
        asset_handler = asset_handler_registry.get_default_handler()

        asset = asset_handler.create(
            title="Original",
            owner=user,
            description=None,
            type="gpkg",
            files=[fake_path],
            clone_files=False,
        )

        self.assertTrue(os.path.exists(fake_path))
        # we need to create first the execution
        _uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="name",
            step="geonode.upload.create_geonode_resource",  # adding the first step for the GPKG file
            input_params={
                "files": {"base_file": fake_path},
                "store_spatial_files": True,
                "asset_id": asset.id,
                "asset_module_path": f"{asset.__module__}.{asset.__class__.__name__}",
            },
        )
        _uuid = str(_uuid)
        self.orchestrator.set_as_failed(_uuid, reason="automatic test")

        # check normal execution status
        req = ExecutionRequest.objects.get(exec_id=_uuid)
        self.assertTrue(req.status, ExecutionRequest.STATUS_FAILED)
        self.assertTrue(req.log, "automatic test")
        # cleanup
        req.delete()

    def test_set_as_completed(self):
        # we need to create first the execution
        _uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="name",
            step="geonode.upload.create_geonode_resource",  # adding the first step for the GPKG file
            input_params={
                "files": {"base_file": "/tmp/file.txt"},
                "store_spatial_files": True,
            },
        )

        # calling the function
        self.orchestrator.set_as_completed(_uuid)

        req = ExecutionRequest.objects.get(exec_id=_uuid)
        self.assertTrue(req.status, ExecutionRequest.STATUS_FINISHED)

        # cleanup
        req.delete()

    def test_update_execution_request_status(self):
        # we need to create first the execution
        _uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="name",
            step="geonode.upload.create_geonode_resource",  # adding the first step for the GPKG file
            input_params={
                "files": {"base_file": "/tmp/file.txt"},
                "store_spatial_files": True,
            },
        )

        self.orchestrator.update_execution_request_status(
            execution_id=_uuid,
            status=ExecutionRequest.STATUS_RUNNING,
            last_updated=timezone.now(),
            func_name="function_name",
            step="step_here",
        )
        req = ExecutionRequest.objects.get(exec_id=_uuid)
        self.assertTrue(req.status, ExecutionRequest.STATUS_RUNNING)
        self.assertTrue(req.func_name, "function_name")
        self.assertTrue(req.step, "step_here")

        # cleanup
        req.delete()

    def test_evaluate_execution_progress_should_continue_if_some_task_is_not_finished(
        self,
    ):
        # create the celery task result entry
        try:
            exec_id = str(
                self.orchestrator.create_execution_request(
                    user=get_user_model().objects.first(),
                    func_name="test",
                    step="test",
                )
            )

            started_entry = TaskResult.objects.create(task_id="task_id_started", status="STARTED", task_args=exec_id)
            success_entry = TaskResult.objects.create(task_id="task_id_success", status="SUCCESS", task_args=exec_id)
            with self.assertLogs(level="INFO") as _log:
                result = self.orchestrator.evaluate_execution_progress(exec_id)

            self.assertIsNone(result)
            self.assertEqual(
                f"INFO:importer:Execution with ID {exec_id} is completed. All tasks are done",
                _log.output[0],
            )

        finally:
            if started_entry:
                started_entry.delete()
            if success_entry:
                success_entry.delete()

    def test_evaluate_execution_progress_should_fail_if_one_task_is_failed(self):
        """
        Should set it fail if all the execution are done and at least 1 is failed
        """
        # create the celery task result entry
        os.makedirs(settings.ASSETS_ROOT, exist_ok=True)

        fake_path = f"{settings.ASSETS_ROOT}/file.txt"
        with open(fake_path, "w"):
            pass

        user = get_user_model().objects.first()
        asset_handler = asset_handler_registry.get_default_handler()

        asset = asset_handler.create(
            title="Original",
            owner=user,
            description=None,
            type="gpkg",
            files=[fake_path],
            clone_files=False,
        )

        try:
            exec_id = str(
                self.orchestrator.create_execution_request(
                    user=get_user_model().objects.first(),
                    func_name="test",
                    step="test",
                    input_params={
                        "asset_id": asset.id,
                        "asset_module_path": f"{asset.__module__}.{asset.__class__.__name__}",
                    },
                )
            )

            FAILED_entry = TaskResult.objects.create(task_id="task_id_FAILED", status="FAILURE", task_args=exec_id)
            success_entry = TaskResult.objects.create(task_id="task_id_success", status="SUCCESS", task_args=exec_id)
            self.orchestrator.evaluate_execution_progress(exec_id)

        finally:
            if FAILED_entry:
                FAILED_entry.delete()
            if success_entry:
                success_entry.delete()

    def test_evaluate_execution_progress_should_set_as_completed(self):
        try:
            exec_id = str(
                self.orchestrator.create_execution_request(
                    user=get_user_model().objects.first(),
                    func_name="test",
                    step="test",
                )
            )

            success_entry = TaskResult.objects.create(task_id="task_id_success", status="SUCCESS", task_args=exec_id)

            self.orchestrator.evaluate_execution_progress(exec_id)

        finally:
            if success_entry:
                success_entry.delete()
