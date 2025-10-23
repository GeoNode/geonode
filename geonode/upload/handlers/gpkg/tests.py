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
import shutil

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from geonode.upload.handlers.gpkg.handler import GPKGFileHandler
from geonode.upload import project_dir
from geonode.upload.orchestrator import orchestrator
from geonode.upload.models import UploadParallelismLimit
from geonode.upload.api.exceptions import UploadParallelismLimitException
from geonode.base.populate_test_data import create_single_dataset
from geonode.resource.models import ExecutionRequest
from osgeo import ogr

from geonode.upload.celery_tasks import UpdateTaskClass


class TestGPKGHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = GPKGFileHandler()
        cls.valid_gpkg = f"{project_dir}/tests/fixture/valid.gpkg"
        cls.invalid_gpkg = f"{project_dir}/tests/fixture/invalid.gpkg"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_files = {"base_file": cls.invalid_gpkg}
        cls.valid_files = {"base_file": cls.valid_gpkg, "action": "upload"}
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="stazioni_metropolitana", owner=cls.owner)

    def test_task_list_is_the_expected_one(self):
        expected = (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["upload"]), 4)
        self.assertTupleEqual(expected, self.handler.TASKS["upload"])

    def test_task_list_is_the_expected_one_geojson(self):
        expected = (
            "start_copy",
            "geonode.upload.copy_dynamic_model",
            "geonode.upload.copy_geonode_data_table",
            "geonode.upload.publish_resource",
            "geonode.upload.copy_geonode_resource",
        )
        self.assertEqual(len(self.handler.TASKS["copy"]), 5)
        self.assertTupleEqual(expected, self.handler.TASKS["copy"])

    def test_is_valid_should_raise_exception_if_the_parallelism_is_met(self):
        parallelism, created = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(slug="default_max_parallel_uploads").update(max_number=0)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_files, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_raise_exception_if_layer_are_greater_than_max_parallel_upload(
        self,
    ):
        parallelism, created = UploadParallelismLimit.objects.get_or_create(slug="default_max_parallel_uploads")
        old_value = parallelism.max_number
        try:
            UploadParallelismLimit.objects.filter(slug="default_max_parallel_uploads").update(max_number=1)

            with self.assertRaises(UploadParallelismLimitException):
                self.handler.is_valid(files=self.valid_files, user=self.user)

        finally:
            parallelism.max_number = old_value
            parallelism.save()

    def test_is_valid_should_pass_with_valid_gpkg(self):
        self.handler.is_valid(files=self.valid_files, user=self.user)

    def test_get_ogr2ogr_driver_should_return_the_expected_driver(self):
        expected = ogr.GetDriverByName("GPKG")
        actual = self.handler.get_ogr2ogr_driver()
        self.assertEqual(type(expected), type(actual))

    def test_can_handle_should_return_true_for_geopackage(self):
        actual = self.handler.can_handle(self.valid_files)
        self.assertTrue(actual)

    def test_can_handle_should_return_false_for_other_files(self):
        actual = self.handler.can_handle({"base_file": "random.file"})
        self.assertFalse(actual)

    @override_settings(MEDIA_ROOT="/tmp/")
    def test_single_message_error_handler(self):
        # Copy the file to the temporary folder
        shutil.copy(self.valid_gpkg, "/tmp")

        exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="funct1",
            step="step",
            input_params={
                "files": {"base_file": "/tmp/valid.gpkg"},
                "skip_existing_layer": True,
                "store_spatial_file": False,
                "handler_module_path": str(self.handler),
            },
        )

        celery_task_handler = UpdateTaskClass()
        celery_task_handler.name = "funct1"

        """
        The progress evaluation will raise and exception
        """
        # Simulate layer creation for the test
        layer_key = "layer_1"
        kwargs = {"kwargs": {"layer_key": layer_key}}
        action = "test_action"
        handler_module_path = str(self.handler)
        fake_task_id = "test-task-id"  # simulate a Celery task ID

        # Simulate task failure
        celery_task_handler.on_failure(
            exc=Exception("exception raised"),
            task_id=fake_task_id,
            args=(str(exec_id), handler_module_path, action),
            kwargs=kwargs,
            einfo=None,
        )

        # Fetch the ExecutionRequest object from DB
        exec_request_obj = ExecutionRequest.objects.get(exec_id=exec_id)

        # Assert overall execution status
        assert exec_request_obj.status == "failed"

        # Assert task-level status
        tasks_status = exec_request_obj.tasks
        assert tasks_status[layer_key]["funct1"] == "FAILED"

        # Assert the error was recorded
        errors = exec_request_obj.output_params.get("errors", [])
        assert any("exception raised" in str(e) for e in errors)
