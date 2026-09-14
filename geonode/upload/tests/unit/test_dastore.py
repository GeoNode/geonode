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
from django.test import TestCase
from geonode.upload import project_dir
from geonode.upload.orchestrator import orchestrator
from geonode.upload.datastore import DataStoreManager
from django.contrib.auth import get_user_model

from unittest.mock import patch

from geonode.base.populate_test_data import create_single_dataset
from geonode.resource.models import ExecutionRequest
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.utils import UploadLimitValidator


class TestDataStoreManager(TestCase):
    """ """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.files = {"base_file": f"{project_dir}/tests/fixture/valid.gpkg"}
        cls.raster_files = {"base_file": f"{project_dir}/tests/fixture/test_raster.tif"}

    def setUp(self):
        self.user = get_user_model().objects.first()
        execution_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="create",
            step="create",
            action="upload",
            input_params={
                **{"handler_module_path": "geonode.upload.handlers.gpkg.handler.GPKGFileHandler"},
            },
        )
        self.datastore = DataStoreManager(
            self.files, "geonode.upload.handlers.gpkg.handler.GPKGFileHandler", self.user, execution_id
        )

        execution_id_url = orchestrator.create_execution_request(
            user=self.user,
            func_name="create",
            step="create",
            action="upload",
            input_params={"url": "https://geosolutionsgroup.com"},
        )
        self.datastore_url = DataStoreManager(
            self.files, "geonode.upload.handlers.common.remote.BaseRemoteResourceHandler", self.user, execution_id_url
        )
        self.gpkg_path = f"{project_dir}/tests/fixture/valid.gpkg"

    def _create_datastore(self, files, handler_module_path, **input_params):
        execution_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="create",
            step="geonode.upload.import_resource",
            action="upload",
            input_params={
                "files": files,
                "handler_module_path": handler_module_path,
                **input_params,
            },
        )
        datastore = DataStoreManager(files, handler_module_path, self.user, execution_id)
        return execution_id, datastore

    def test_input_is_valid_with_files(self):
        self.assertTrue(self.datastore.input_is_valid())

    def test_input_is_valid_with_urls(self):
        self.assertTrue(self.datastore_url.input_is_valid())

    @patch("geonode.upload.handlers.common.raster.import_orchestrator.apply_async")
    def test_skip_existing_raster_finishes_execution_and_releases_parallel_slot(self, schedule_import):
        create_single_dataset(name="test_raster", owner=self.user)
        handler_module_path = "geonode.upload.handlers.common.raster.BaseRasterFileHandler"
        execution_id, datastore = self._create_datastore(
            self.raster_files,
            handler_module_path,
            skip_existing_layer=True,
        )

        datastore._import_and_register(str(execution_id), "geonode.upload.import_resource")

        execution = ExecutionRequest.objects.get(exec_id=execution_id)
        self.assertEqual(ExecutionRequest.STATUS_FINISHED, execution.status)
        self.assertIsNotNone(execution.finished)
        self.assertEqual(0, execution.input_params["total_layers"])
        self.assertEqual(0, UploadLimitValidator(self.user)._get_parallel_uploads_count())
        schedule_import.assert_not_called()

    @patch("geonode.upload.handlers.common.vector.chord")
    def test_skip_existing_geojson_finishes_execution(self, celery_chord):
        files = {"base_file": f"{project_dir}/tests/fixture/valid.geojson"}
        create_single_dataset(name="valid", owner=self.user)
        handler_module_path = "geonode.upload.handlers.geojson.handler.GeoJsonFileHandler"
        execution_id, datastore = self._create_datastore(
            files,
            handler_module_path,
            skip_existing_layer=True,
        )

        datastore._import_and_register(str(execution_id), "geonode.upload.import_resource")

        execution = ExecutionRequest.objects.get(exec_id=execution_id)
        self.assertEqual(ExecutionRequest.STATUS_FINISHED, execution.status)
        self.assertIsNotNone(execution.finished)
        self.assertEqual(0, execution.input_params["total_layers"])
        celery_chord.assert_not_called()

    def test_partial_skip_uses_imported_layer_count_for_progress(self):
        handler_module_path = "geonode.upload.handlers.gpkg.handler.GPKGFileHandler"
        execution_id, datastore = self._create_datastore(
            self.files,
            handler_module_path,
            skip_existing_layer=True,
            total_layers=2,
        )

        with patch(
            "geonode.upload.handlers.gpkg.handler.GPKGFileHandler.import_resource",
            return_value=(["imported_layer"], ["imported_layer"], str(execution_id)),
        ):
            datastore._import_and_register(str(execution_id), "geonode.upload.import_resource")

        execution = ExecutionRequest.objects.get(exec_id=execution_id)
        self.assertEqual(1, execution.input_params["total_layers"])

        resource = create_single_dataset(name="partial_skip_imported", owner=self.user)
        ResourceHandlerInfo.objects.create(
            execution_request=execution,
            handler_module_path=handler_module_path,
            resource=resource,
        )

        tasks = execution.tasks
        for status_by_task in tasks.values():
            for task_name in status_by_task:
                status_by_task[task_name] = "SUCCESS"
        execution.tasks = tasks
        execution.save(update_fields=["tasks"])

        orchestrator.evaluate_execution_progress(str(execution_id), handler_module_path=handler_module_path)

        execution.refresh_from_db()
        self.assertEqual(ExecutionRequest.STATUS_FINISHED, execution.status)
        self.assertIsNotNone(execution.finished)
