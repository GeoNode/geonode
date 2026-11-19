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

from geonode.resource.models import ExecutionRequest

# Create your tests here.

GPKG_HANDLER = "geonode.upload.handlers.gpkg.handler.GPKGFileHandler"


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

    def test_get_serializer_should_return_the_default_one_for_the_copy_action(self):
        """The copy action is handled by its own endpoint, never by the generic upload one"""
        actual = self.orchestrator.get_serializer({"action": "copy"})
        self.assertEqual(type(ImporterSerializer), type(actual))

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

        self.assertTrue(os.path.exists(fake_path))
        # we need to create first the execution
        _uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="name",
            step="geonode.upload.create_geonode_resource",  # adding the first step for the GPKG file
            input_params={
                "files": {"base_file": fake_path},
                "store_spatial_files": True,
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
        """
        Execution should stay READY or RUNNING if at least one task is still in progress.
        """

        # Create an execution request with expected datasets > 0
        exec_uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="test",
            step="test",
            input_params={"total_layers": 2},  # <-- ensures is_last_dataset=False
        )

        # Simulate tasks: one running, one success
        exec_request_obj = ExecutionRequest.objects.get(exec_id=exec_uuid)
        exec_request_obj.tasks = {
            "layer_1": {"test": "RUNNING"},
            "layer_2": {"test": "SUCCESS"},
        }
        exec_request_obj.save()

        # Call method under test
        result = self.orchestrator.evaluate_execution_progress(exec_uuid)

        # Assert method does not return anything
        assert result is None

        # Reload execution object
        exec_request_obj.refresh_from_db()

        # Assert execution is still in progress (READY or RUNNING)
        assert exec_request_obj.status in [
            ExecutionRequest.STATUS_READY,
            ExecutionRequest.STATUS_RUNNING,
        ]

    def test_evaluate_execution_progress_should_fail_if_one_task_is_failed(self):
        """
        Should set it to FAILURE if all the executions are done and at least 1 is failed
        """

        # Create execution request
        exec_uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="test",
            step="test",
            input_params={},
        )

        # Simulate tasks: one failed, one succeeded
        exec_request_obj = ExecutionRequest.objects.get(exec_id=exec_uuid)
        exec_request_obj.tasks = {
            "layer_1": {"test": "FAILED"},
            "layer_2": {"test": "SUCCESS"},
        }
        exec_request_obj.save()

        self.orchestrator.evaluate_execution_progress(exec_uuid, _log="Test failure")

        exec_request_obj.refresh_from_db()

        # Assert execution status is FAILED
        assert exec_request_obj.status == ExecutionRequest.STATUS_FAILED

        # Tasks dict should remain unchanged
        assert exec_request_obj.tasks["layer_1"]["test"] == "FAILED"
        assert exec_request_obj.tasks["layer_2"]["test"] == "SUCCESS"

    def test_evaluate_execution_progress_should_set_as_completed(self):
        """
        Should mark execution as FINISHED when all tasks are successful
        and the last dataset is reached.
        """

        # Create execution request with expected layers = 1
        exec_uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="test",
            step="test",
            input_params={"total_layers": 1},  # ensures last dataset check will pass
        )

        # Simulate a SUCCESS task
        exec_request_obj = ExecutionRequest.objects.get(exec_id=exec_uuid)
        exec_request_obj.tasks = {
            "layer_1": {"test": "SUCCESS"},
        }
        exec_request_obj.save()

        from geonode.base.models import ResourceBase
        from geonode.upload.models import ResourceHandlerInfo

        resource = ResourceBase.objects.create(
            title="Test resource",
            owner=get_user_model().objects.first(),
        )

        # Link ResourceHandlerInfo to both the execution and resource
        ResourceHandlerInfo.objects.create(
            execution_request=exec_request_obj,
            handler_module_path="dummy.handler",
            resource=resource,
        )

        # Call method under test
        self.orchestrator.evaluate_execution_progress(exec_uuid)

        exec_request_obj.refresh_from_db()

        # Assert execution is marked as FINISHED
        assert exec_request_obj.status == ExecutionRequest.STATUS_FINISHED

        # Tasks dict should remain SUCCESS
        assert exec_request_obj.tasks["layer_1"]["test"] == "SUCCESS"

    def _create_hooks_execution(self, step="start_import", status=ExecutionRequest.STATUS_READY):
        _uuid = self.orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="test",
            step=step,
            input_params={"handler_module_path": GPKG_HANDLER, "total_layers": 1},
            action="upload",
        )
        ExecutionRequest.objects.filter(exec_id=_uuid).update(status=status)
        return _uuid

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    @patch("geonode.upload.orchestrator.importer_app.tasks.get")
    def test_perform_next_step_should_fire_started_on_the_first_step(self, mock_celery, do_action):
        """The started event must fire when the execution becomes running"""
        _uuid = self._create_hooks_execution()

        self.orchestrator.perform_next_step(_uuid, "upload", step="start_import", handler_module_path=GPKG_HANDLER)

        do_action.assert_called_once()
        phase, execution = do_action.call_args.args
        self.assertEqual("started", phase)
        self.assertEqual(ExecutionRequest.STATUS_RUNNING, execution.status)

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    @patch("geonode.upload.orchestrator.importer_app.tasks.get")
    def test_perform_next_step_should_not_fire_started_after_the_first_step(self, mock_celery, do_action):
        """Only the first step starts the execution"""
        _uuid = self._create_hooks_execution(step="geonode.upload.import_resource")

        self.orchestrator.perform_next_step(
            _uuid, "upload", step="geonode.upload.import_resource", handler_module_path=GPKG_HANDLER
        )

        do_action.assert_not_called()

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    @patch("geonode.upload.orchestrator.importer_app.tasks.get")
    def test_perform_next_step_should_not_fire_started_on_rollback(self, mock_celery, do_action):
        """The rollback starts on a failed execution: it must not fire started or set it as running"""
        _uuid = self._create_hooks_execution(step="start_rollback", status=ExecutionRequest.STATUS_FAILED)

        self.orchestrator.perform_next_step(_uuid, "rollback", step="start_rollback", handler_module_path=GPKG_HANDLER)

        do_action.assert_not_called()
        self.assertEqual(ExecutionRequest.STATUS_FAILED, ExecutionRequest.objects.get(exec_id=_uuid).status)

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    def test_perform_next_step_should_not_complete_an_empty_rollback(self, do_action):
        """A handler without rollback steps must leave the execution failed, without firing completed"""
        _uuid = self._create_hooks_execution(step="start_rollback", status=ExecutionRequest.STATUS_FAILED)

        self.orchestrator.perform_next_step(
            _uuid, "rollback", step="start_rollback", handler_module_path="geonode.upload.handlers.base.BaseHandler"
        )

        do_action.assert_not_called()
        self.assertEqual(ExecutionRequest.STATUS_FAILED, ExecutionRequest.objects.get(exec_id=_uuid).status)

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    def test_set_as_completed_should_fire_completed_once(self, do_action):
        """A second completion of the same execution must not fire the event again"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)

        self.orchestrator.set_as_completed(_uuid)
        self.orchestrator.set_as_completed(_uuid)

        do_action.assert_called_once()
        self.assertEqual("completed", do_action.call_args.args[0])

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    def test_set_as_completed_should_fill_the_resources_before_firing(self, do_action):
        """Subscribers must receive a finished execution with its resources, without reading it again"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)
        _resource = self._link_resource(_uuid)

        self.orchestrator.set_as_completed(_uuid)

        execution = do_action.call_args.args[1]
        self.assertEqual(ExecutionRequest.STATUS_FINISHED, execution.status)
        expected = [{"detail_url": _resource.detail_url, "id": _resource.pk}]
        self.assertListEqual(expected, execution.output_params["resources"])

    def test_perform_last_step_should_lock_the_execution(self):
        """Concurrent workers must not overwrite each other: the execution is read under a row lock"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_FINISHED)

        with patch.object(
            ExecutionRequest.objects, "select_for_update", wraps=ExecutionRequest.objects.select_for_update
        ) as _select_for_update:
            BaseHandler.perform_last_step(str(_uuid))

        _select_for_update.assert_called_once()
        actual = ExecutionRequest.objects.get(exec_id=_uuid)
        self.assertEqual(ExecutionRequest.STATUS_FINISHED, actual.status)
        self.assertListEqual([], actual.output_params["resources"])

    def test_perform_last_step_should_raise_if_the_execution_does_not_exist(self):
        """The lock query must keep the error raised before by get_execution_object"""
        with self.assertRaises(ImportException):
            BaseHandler.perform_last_step(str(uuid.uuid4()))

    def _link_resource(self, _uuid):
        from geonode.base.models import ResourceBase
        from geonode.upload.models import ResourceHandlerInfo

        _resource = ResourceBase.objects.create(title="Test resource", owner=get_user_model().objects.first())
        ResourceHandlerInfo.objects.create(
            execution_request=ExecutionRequest.objects.get(exec_id=_uuid),
            handler_module_path=GPKG_HANDLER,
            resource=_resource,
        )
        return _resource

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    def test_set_as_partially_failed_should_fire_partially_failed_once(self, do_action):
        """A second partial failure of the same execution must not fire the event again"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)

        self.orchestrator.set_as_partially_failed(_uuid, reason=["layer_1"])
        self.orchestrator.set_as_partially_failed(_uuid, reason=["layer_1"])

        do_action.assert_called_once()
        self.assertEqual("partially_failed", do_action.call_args.args[0])
        self.assertDictEqual({"reason": ["layer_1"]}, do_action.call_args.kwargs)

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    def test_set_as_partially_failed_should_fill_the_resources_before_firing(self, do_action):
        """Subscribers must receive the resources of the imported layers, without reading the execution again"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)
        _resource = self._link_resource(_uuid)

        self.orchestrator.set_as_partially_failed(_uuid, reason=["layer_2"])

        execution = do_action.call_args.args[1]
        self.assertEqual(ExecutionRequest.STATUS_FAILED, execution.status)
        expected = [{"detail_url": _resource.detail_url, "id": _resource.pk}]
        self.assertListEqual(expected, execution.output_params["resources"])

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    def test_set_as_failed_should_fire_failed_once(self, do_action):
        """A second failure of the same execution must not fire the event again"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)

        self.orchestrator.set_as_failed(_uuid, reason="first error")
        self.orchestrator.set_as_failed(_uuid, reason="second error")

        do_action.assert_called_once()
        self.assertEqual("failed", do_action.call_args.args[0])
        self.assertDictEqual({"reason": "first error"}, do_action.call_args.kwargs)

    @patch("geonode.upload.orchestrator.importer_hooks.do_action")
    def test_set_as_failed_should_fire_failed_if_already_finished(self, do_action):
        """evaluate_error can fail a finished execution: failed fires after completed"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_FINISHED)

        self.orchestrator.set_as_failed(_uuid, reason="late error")

        do_action.assert_called_once()
        self.assertEqual("failed", do_action.call_args.args[0])

    def test_set_as_failed_should_append_the_reason_if_already_failed(self):
        """The first error must be kept and the following ones appended to the log"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)

        self.orchestrator.set_as_failed(_uuid, reason="first error")
        self.orchestrator.set_as_failed(_uuid, reason=Exception("second error"))

        actual = ExecutionRequest.objects.get(exec_id=_uuid)
        self.assertEqual(ExecutionRequest.STATUS_FAILED, actual.status)
        self.assertEqual("first error\nsecond error", actual.log)

    def test_set_as_failed_should_append_the_reason_if_the_log_is_empty(self):
        """A failure without reason leaves the log empty: the following reason must still be appended"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)

        self.orchestrator.set_as_failed(_uuid)
        self.orchestrator.set_as_failed(_uuid, reason="second error")

        self.assertEqual("\nsecond error", ExecutionRequest.objects.get(exec_id=_uuid).log)

    def test_set_as_failed_should_not_repeat_the_last_reason(self):
        """The rollback reports the same error already logged: the log must not contain it twice"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)

        self.orchestrator.set_as_failed(_uuid, reason="same error")
        self.orchestrator.set_as_failed(_uuid, reason="same error", delete_file=False)

        self.assertEqual("same error", ExecutionRequest.objects.get(exec_id=_uuid).log)

    def test_evaluate_execution_progress_should_run_the_last_step_once_on_partial_failure(self):
        """set_as_partially_failed runs the last step: evaluate_execution_progress must not run it again"""
        _uuid = self._create_hooks_execution(status=ExecutionRequest.STATUS_RUNNING)
        ExecutionRequest.objects.filter(exec_id=_uuid).update(
            tasks={"layer_1": {"test": "FAILED"}, "layer_2": {"test": "SUCCESS"}}
        )
        self._link_resource(_uuid)

        with patch.object(self.orchestrator, "_last_step") as _last_step:
            self.orchestrator.evaluate_execution_progress(_uuid)

        _last_step.assert_called_once_with(_uuid, GPKG_HANDLER)
