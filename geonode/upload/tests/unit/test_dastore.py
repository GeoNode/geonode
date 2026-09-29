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
from django.test import TestCase, override_settings
from geonode.upload import project_dir
from geonode.upload.orchestrator import orchestrator
from geonode.upload.datastore import DataStoreManager
from django.contrib.auth import get_user_model

from unittest.mock import patch

from geonode.base.populate_test_data import create_single_dataset
from geonode.resource.models import ExecutionRequest
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.api.exceptions import ImportException
from geonode.upload.celery_tasks import UpdateTaskClass
from geonode.resource.api.serializer import ExecutionRequestSerializer
from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from geonode.upload.handlers.common.raster import BaseRasterFileHandler
from geonode.upload.handlers.shapefile.handler import ShapeFileHandler
from geonode.upload.handlers.tiles3d.handler import Tiles3DFileHandler
from geonode.base.models import ResourceBase


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

    def _assert_all_skipped(self, execution_id, datastore, resource):
        message = (
            "No new layers were detected in your upload. "
            "Existing layers were left unchanged, so no updates were made."
        )
        original = type(resource).objects.filter(pk=resource.pk).values().get()
        self.assertEqual(1, UploadLimitValidator(self.user)._get_parallel_uploads_count())
        task = UpdateTaskClass()
        task.name = "geonode.upload.import_resource"
        task.bulk = True
        args = (str(execution_id), str(datastore.handler()), "upload")
        task.before_start("test-skip", args, {})
        with self.assertRaisesMessage(ImportException, message) as error:
            datastore._import_and_register(str(execution_id), task.name)
        task.on_failure(error.exception, "test-skip", args, {}, None)
        execution = ExecutionRequest.objects.get(exec_id=execution_id)
        self.assertEqual(ExecutionRequest.STATUS_FAILED, execution.status)
        self.assertIsNotNone(execution.finished)
        self.assertEqual(message, execution.log)
        self.assertEqual(message, ExecutionRequestSerializer(execution).data["log"])
        self.assertEqual(0, UploadLimitValidator(self.user)._get_parallel_uploads_count())
        self.assertFalse(ResourceHandlerInfo.objects.filter(execution_request=execution).exists())
        self.assertEqual(original, type(resource).objects.filter(pk=resource.pk).values().get())

    def test_handlers_normalize_skip_existing_layers(self):
        for handler in (BaseVectorFileHandler, BaseRasterFileHandler, ShapeFileHandler, Tiles3DFileHandler):
            for flag in (True, False, None):
                with self.subTest(handler=handler.__name__, flag=flag):
                    data = {} if flag is None else {"skip_existing_layers": flag}
                    params, files = handler.extract_params_from_data(data)
                    self.assertIs(params["skip_existing_layer"], flag is True)
                    self.assertNotIn("skip_existing_layers", params)
                    self.assertNotIn("skip_existing_layers", files)

    def test_input_is_valid_with_files(self):
        self.assertTrue(self.datastore.input_is_valid())

    def test_input_is_valid_with_urls(self):
        self.assertTrue(self.datastore_url.input_is_valid())

    @patch("geonode.upload.handlers.common.raster.import_orchestrator.apply_async")
    def test_skip_existing_raster_fails_execution_and_releases_parallel_slot(self, schedule_import):
        resource = create_single_dataset(name="test_raster", owner=self.user)
        handler_module_path = "geonode.upload.handlers.common.raster.BaseRasterFileHandler"
        execution_id, datastore = self._create_datastore(
            self.raster_files,
            handler_module_path,
            skip_existing_layer=True,
            total_layers=1,
        )

        self._assert_all_skipped(execution_id, datastore, resource)

        schedule_import.assert_not_called()

    @patch("geonode.upload.handlers.common.vector.chord")
    def test_skip_existing_geojson_fails_execution(self, celery_chord):
        files = {"base_file": f"{project_dir}/tests/fixture/valid.geojson"}
        resource = create_single_dataset(name="valid", owner=self.user)
        handler_module_path = "geonode.upload.handlers.geojson.handler.GeoJsonFileHandler"
        execution_id, datastore = self._create_datastore(
            files,
            handler_module_path,
            skip_existing_layer=True,
            total_layers=1,
        )

        self._assert_all_skipped(execution_id, datastore, resource)

        celery_chord.assert_not_called()

    @patch("geonode.upload.handlers.tiles3d.handler.import_orchestrator.apply_async")
    def test_skip_existing_3dtiles_fails_execution(self, schedule_import):
        resource = ResourceBase.objects.create(
            title="valid_3dtiles",
            alternate="valid_3dtiles",
            owner=self.user,
            resource_type="dataset",
            subtype="3dtiles",
        )
        execution_id, datastore = self._create_datastore(
            {"base_file": f"{project_dir}/tests/fixture/3dtilesample/tileset.json"},
            "geonode.upload.handlers.tiles3d.handler.Tiles3DFileHandler",
            skip_existing_layer=True,
            original_zip_name="valid_3dtiles",
            total_layers=1,
        )
        self._assert_all_skipped(execution_id, datastore, resource)
        schedule_import.assert_not_called()

    @override_settings(IMPORTER_ENABLE_DYN_MODELS=False)
    @patch("geonode.upload.handlers.common.vector.chord")
    def test_partial_skip_uses_imported_layer_count_for_progress(self, celery_chord):
        handler_module_path = "geonode.upload.handlers.gpkg.handler.GPKGFileHandler"
        execution_id, datastore = self._create_datastore(
            {"base_file": f"{project_dir}/tests/fixture/multiple_layers.gpkg"},
            handler_module_path,
            skip_existing_layer=True,
        )

        handler = datastore.handler()
        layers = handler._select_valid_layers(handler.open_source_file(datastore.files))
        names = [handler.fixup_name(layer.GetName()) for layer in layers]
        self.assertGreater(len(names), 1)
        create_single_dataset(name=names[0], owner=self.user)
        datastore._import_and_register(str(execution_id), "geonode.upload.import_resource")

        execution = ExecutionRequest.objects.get(exec_id=execution_id)
        self.assertEqual(len(names) - 1, execution.input_params["total_layers"])
        self.assertEqual(len(names) - 1, celery_chord.call_count)
        scheduled_names = [call.args[0].args[3] for call in celery_chord.return_value.call_args_list]
        self.assertEqual(names[1:], scheduled_names)

        for name in names[1:]:
            resource = create_single_dataset(name=name, owner=self.user)
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
