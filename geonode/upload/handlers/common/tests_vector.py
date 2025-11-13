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
import shutil
import uuid
from celery.canvas import Signature
from celery import group
from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from mock import MagicMock, patch
from geonode.upload.api.exceptions import UpsertException
from geonode.upload.handlers.common.vector import BaseVectorFileHandler, import_with_ogr2ogr
from django.contrib.auth import get_user_model
from geonode.upload import project_dir
from geonode.upload.handlers.geojson.handler import GeoJsonFileHandler
from geonode.upload.handlers.gpkg.handler import GPKGFileHandler
from geonode.upload.handlers.shapefile.handler import ShapeFileHandler
from geonode.upload.orchestrator import orchestrator
from geonode.base.populate_test_data import create_single_dataset
from geonode.resource.models import ExecutionRequest
from dynamic_models.models import ModelSchema
from osgeo import ogr
from django.test.utils import override_settings
from geoserver.catalog import Catalog

from geonode.upload.tests.utils import TransactionImporterBaseTestSupport
from geonode.utils import OGC_Servers_Handler
from geonode.upload.utils import create_vrt_file, has_incompatible_field_names


class TestBaseVectorFileHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = BaseVectorFileHandler()
        cls.valid_gpkg = f"{project_dir}/tests/fixture/valid.gpkg"
        cls.invalid_gpkg = f"{project_dir}/tests/fixture/invalid.gpkg"
        cls.no_crs_gpkg = f"{project_dir}/tests/fixture/noCrsTable.gpkg"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.invalid_files = {"base_file": cls.invalid_gpkg}
        cls.valid_files = {"base_file": "/tmp/valid.gpkg"}
        cls.owner = get_user_model().objects.first()
        cls.layer = create_single_dataset(name="stazioni_metropolitana", owner=cls.owner)

    def setUp(self) -> None:
        shutil.copy(self.valid_gpkg, "/tmp")
        super().setUp()

    def test_create_error_log(self):
        """
        Should return the formatted way for the log of the handler
        """
        actual = self.handler.create_error_log(
            Exception("my exception"),
            "foo_task_name",
            *["exec_id", "layer_name", "alternate"],
        )
        expected = "Task: foo_task_name raised an error during actions for layer: alternate: my exception"
        self.assertEqual(expected, actual)

    def test_create_vrt_file_with_special_chars(self):
        """
        Test that create_vrt_file correctly sanitizes layer and field names
        with spaces and special characters, and generates a valid VRT file.
        """
        source_filepath = "source file.shp"

        mock_layer = MagicMock(spec=ogr.Layer)
        mock_layer.GetName.return_value = "Layer With Spaces"
        mock_layer.GetGeomType.return_value = ogr.wkbPolygon

        mock_field_1 = MagicMock()
        mock_field_1.GetName.return_value = "Field 1 (m)"
        mock_field_1.GetTypeName.return_value = "String"

        mock_field_2 = MagicMock()
        mock_field_2.GetName.return_value = "another-field"
        mock_field_2.GetTypeName.return_value = "Real"

        mock_field_3 = MagicMock()
        mock_field_3.GetName.return_value = "field/with/slash"
        mock_field_3.GetTypeName.return_value = "Integer"

        mock_layer_defn = MagicMock()
        mock_layer_defn.GetFieldCount.return_value = 3
        mock_layer_defn.GetFieldDefn.side_effect = [mock_field_1, mock_field_2, mock_field_3].__getitem__

        mock_layer.GetLayerDefn.return_value = mock_layer_defn

        vrt_filename, vrt_layer_name = None, None
        try:
            vrt_filename, vrt_layer_name = create_vrt_file(mock_layer, source_filepath)

            self.assertIsNotNone(vrt_filename)
            self.assertTrue(os.path.exists(vrt_filename))
            self.assertEqual(vrt_layer_name, "layer_with_spaces")

            with open(vrt_filename, "r") as f:
                vrt_content = f.read()

            self.assertIn('<OGRVRTLayer name="layer_with_spaces">', vrt_content)
            self.assertIn(f"<SrcDataSource>{source_filepath}</SrcDataSource>", vrt_content)
            self.assertIn("<SrcLayer>Layer With Spaces</SrcLayer>", vrt_content)

            self.assertIn('<Field name="field_1_m" src="Field 1 (m)" type="String" />', vrt_content)
            self.assertIn('<Field name="another_field" src="another-field" type="Real" />', vrt_content)
            self.assertIn('<Field name="fieldwithslash" src="field/with/slash" type="Integer" />', vrt_content)

        finally:
            if vrt_filename and os.path.exists(vrt_filename):
                os.remove(vrt_filename)

    def test_has_incompatible_field_names(self):
        """
        Test that has_incompatible_field_names correctly identifies layers
        with field names that need sanitization.
        """

        # layer with incompatible field names
        mock_layer_incompatible = MagicMock(spec=ogr.Layer)
        mock_layer_incompatible.GetName.return_value = "Layer With Spaces"

        mock_field_1 = MagicMock()
        mock_field_1.GetName.return_value = "Field 1 (m)"

        mock_field_2 = MagicMock()
        mock_field_2.GetName.return_value = "another-#field"

        mock_layer_defn_incompatible = MagicMock()
        mock_layer_defn_incompatible.GetFieldCount.return_value = 2
        mock_layer_defn_incompatible.GetFieldDefn.side_effect = [mock_field_1, mock_field_2].__getitem__

        mock_layer_incompatible.GetLayerDefn.return_value = mock_layer_defn_incompatible

        self.assertTrue(has_incompatible_field_names(mock_layer_incompatible))

        # layer with compatible field names
        mock_layer_compatible = MagicMock(spec=ogr.Layer)
        mock_layer_compatible.GetName.return_value = "compatible_layer"

        mock_field_3 = MagicMock()
        mock_field_3.GetName.return_value = "field_one"

        mock_field_4 = MagicMock()
        mock_field_4.GetName.return_value = "field_two"

        mock_layer_defn_compatible = MagicMock()
        mock_layer_defn_compatible.GetFieldCount.return_value = 2
        mock_layer_defn_compatible.GetFieldDefn.side_effect = [mock_field_3, mock_field_4].__getitem__

        mock_layer_compatible.GetLayerDefn.return_value = mock_layer_defn_compatible

        self.assertFalse(has_incompatible_field_names(mock_layer_compatible))

    def test_create_dynamic_model_fields(self):
        try:
            # Prepare the test
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params={"files": self.valid_files, "skip_existing_layer": True},
            )
            schema, _ = ModelSchema.objects.get_or_create(name="test_handler", db_name="datastore")
            layers = ogr.Open(self.valid_gpkg)

            # starting the tests
            dynamic_model, celery_group = self.handler.create_dynamic_model_fields(
                layer=[x for x in layers][0],
                dynamic_model_schema=schema,
                overwrite=False,
                execution_id=str(exec_id),
                layer_name="stazioni_metropolitana",
            )

            self.assertIsNotNone(dynamic_model)
            self.assertIsInstance(celery_group, group)
            self.assertEqual(1, len(celery_group.tasks))
            self.assertEqual("geonode.upload.create_dynamic_structure", celery_group.tasks[0].name)
        finally:
            if schema:
                schema.delete()
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    def test_setup_dynamic_model_no_dataset_no_modelschema(self):
        self._assert_test_result()

    def test_setup_dynamic_model_no_dataset_no_modelschema_overwrite_true(self):
        self._assert_test_result(overwrite=True)

    def test_setup_dynamic_model_with_dataset_no_modelschema_overwrite_false(self):
        create_single_dataset(name="stazioni_metropolitana", owner=self.user)
        self._assert_test_result(overwrite=False)

    def test_setup_dynamic_model_with_dataset_no_modelschema_overwrite_True(self):
        create_single_dataset(name="stazioni_metropolitana", owner=self.user)
        self._assert_test_result(overwrite=True)

    def test_setup_dynamic_model_no_dataset_with_modelschema_overwrite_false(self):
        ModelSchema.objects.get_or_create(name="stazioni_metropolitana", db_name="datastore")
        self._assert_test_result(overwrite=False)

    def test_setup_dynamic_model_with_dataset_with_modelschema_overwrite_false(self):
        create_single_dataset(name="stazioni_metropolitana", owner=self.user)
        ModelSchema.objects.create(name="stazioni_metropolitana", db_name="datastore", managed=True)
        self._assert_test_result(overwrite=False)

    def _assert_test_result(self, overwrite=False):
        try:
            # Prepare the test
            exec_id = orchestrator.create_execution_request(
                user=self.user,
                func_name="funct1",
                step="step",
                input_params={"files": self.valid_files, "skip_existing_layer": True},
            )

            if overwrite:
                resource = self.handler.create_geonode_resource(
                    "layer_name",
                    "layer_alternate",
                    str(exec_id),
                )
                ExecutionRequest.objects.filter(exec_id=exec_id).update(
                    input_params={"files": self.valid_files, "skip_existing_layer": True, "resource_pk": resource.pk}
                )

            layers = ogr.Open(self.valid_gpkg)

            # starting the tests
            dynamic_model, layer_name, celery_group = self.handler.setup_dynamic_model(
                layer=[x for x in layers][0],
                execution_id=str(exec_id),
                should_be_overwritten=overwrite,
                username=self.user,
            )

            self.assertIsNotNone(dynamic_model)

            # check if the uuid has been added to the model name
            self.assertIsNotNone(layer_name)

            self.assertIsInstance(celery_group, group)
            self.assertEqual(1, len(celery_group.tasks))
            self.assertEqual("geonode.upload.create_dynamic_structure", celery_group.tasks[0].name)
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    @patch("geonode.upload.handlers.common.vector.BaseVectorFileHandler.get_ogr2ogr_driver")
    @patch("geonode.upload.handlers.common.vector.chord")
    def test_import_resource_should_not_be_imported(self, celery_chord, ogr2ogr_driver):
        """
        If the resource exists and should be skept, the celery task
        is not going to be called and the layer is skipped
        """
        exec_id = None
        try:
            # create the executionId
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params={"files": self.valid_files, "skip_existing_layer": True},
            )

            with self.assertRaises(Exception) as exception:
                # start the resource import
                self.handler.import_resource(files=self.valid_files, execution_id=str(exec_id))
            self.assertIn(
                "No valid layers found",
                exception.exception.args[0],
                "No valid layers found.",
            )

            celery_chord.assert_not_called()
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    @patch("geonode.upload.handlers.common.vector.BaseVectorFileHandler.get_ogr2ogr_driver")
    @patch("geonode.upload.handlers.common.vector.chord")
    def test_import_resource_should_work(self, celery_chord, ogr2ogr_driver):
        try:
            ogr2ogr_driver.return_value = ogr.GetDriverByName("GPKG")
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.first(),
                func_name="funct1",
                step="step",
                input_params={"files": self.valid_files},
            )

            # start the resource import
            self.handler.import_resource(files=self.valid_files, execution_id=str(exec_id))

            celery_chord.assert_called_once()
        finally:
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=exec_id).delete()

    def test_get_ogr2ogr_task_group(self):
        _uuid = uuid.uuid4()

        actual = self.handler.get_ogr2ogr_task_group(
            str(_uuid),
            files=self.valid_files,
            layer="dataset",
            should_be_overwritten=True,
            alternate="abc",
        )
        self.assertIsInstance(actual, (Signature,))
        self.assertEqual("geonode.upload.import_with_ogr2ogr", actual.task)

    @patch("geonode.upload.handlers.common.vector.Popen")
    def test_import_with_ogr2ogr_without_errors_should_call_the_right_command(self, _open):
        _uuid = uuid.uuid4()

        comm = MagicMock()
        comm.communicate.return_value = b"", b""
        _open.return_value = comm

        _task, alternate, execution_id = import_with_ogr2ogr(
            execution_id=str(_uuid),
            files=self.valid_files,
            original_name="dataset",
            handler_module_path=str(self.handler),
            ovverwrite_layer=False,
            alternate="alternate",
        )

        self.assertEqual("ogr2ogr", _task)
        self.assertEqual(alternate, "alternate")
        self.assertEqual(str(_uuid), execution_id)

        _datastore = settings.DATABASES["datastore"]
        _open.assert_called_once()
        _open.assert_called_with(
            "/usr/bin/ogr2ogr --config PG_USE_COPY YES -f PostgreSQL PG:\" dbname='test_geonode_data' host="
            + os.getenv("DATABASE_HOST", "localhost")
            + " port=5432 user='"
            + _datastore["USER"]
            + "' password='"
            + _datastore["PASSWORD"]
            + '\' " "'
            + self.valid_files.get("base_file")
            + '" -lco FID=fid'
            + ' -nln alternate "dataset"',
            stdout=-1,
            stderr=-1,
            shell=True,  # noqa
        )

    @patch("geonode.upload.handlers.common.vector.Popen")
    def test_import_with_ogr2ogr_with_errors_should_raise_exception(self, _open):
        _uuid = uuid.uuid4()

        comm = MagicMock()
        comm.communicate.return_value = b"", b"ERROR: some error here"
        _open.return_value = comm

        with self.assertRaises(Exception):
            import_with_ogr2ogr(
                execution_id=str(_uuid),
                files=self.valid_files,
                original_name="dataset",
                handler_module_path=str(self.handler),
                ovverwrite_layer=False,
                alternate="alternate",
            )

        _datastore = settings.DATABASES["datastore"]

        _open.assert_called_once()
        _open.assert_called_with(
            "/usr/bin/ogr2ogr --config PG_USE_COPY YES -f PostgreSQL PG:\" dbname='test_geonode_data' host="
            + os.getenv("DATABASE_HOST", "localhost")
            + " port=5432 user='"
            + _datastore["USER"]
            + "' password='"
            + _datastore["PASSWORD"]
            + '\' " "'
            + self.valid_files.get("base_file")
            + '" -lco FID=fid'
            + ' -nln alternate "dataset"',
            stdout=-1,
            stderr=-1,
            shell=True,  # noqa
        )

    @patch.dict(os.environ, {"OGR2OGR_COPY_WITH_DUMP": "True"}, clear=True)
    @patch("geonode.upload.handlers.common.vector.Popen")
    def test_import_with_ogr2ogr_without_errors_should_call_the_right_command_if_dump_is_enabled(self, _open):
        _uuid = uuid.uuid4()

        comm = MagicMock()
        comm.communicate.return_value = b"", b""
        _open.return_value = comm

        _task, alternate, execution_id = import_with_ogr2ogr(
            execution_id=str(_uuid),
            files=self.valid_files,
            original_name="dataset",
            handler_module_path=str(self.handler),
            ovverwrite_layer=False,
            alternate="alternate",
        )

        self.assertEqual("ogr2ogr", _task)
        self.assertEqual(alternate, "alternate")
        self.assertEqual(str(_uuid), execution_id)

        _open.assert_called_once()
        _call_as_string = _open.mock_calls[0][1][0]

        self.assertTrue("-f PGDump /vsistdout/" in _call_as_string)
        self.assertTrue("psql -d" in _call_as_string)
        self.assertFalse("-f PostgreSQL PG" in _call_as_string)

    def test_select_valid_layers(self):
        """
        The function should return only the datasets with a geometry
        The other one are discarded
        """
        all_layers = GPKGFileHandler().get_ogr2ogr_driver().Open(self.no_crs_gpkg)

        with self.assertLogs(level="ERROR") as _log:
            valid_layer = GPKGFileHandler()._select_valid_layers(all_layers)

        self.assertIn(
            "The following layer layer_styles does not have a Coordinate Reference System (CRS) and will be skipped.",
            [x.message for x in _log.records],
        )
        self.assertEqual(1, len(valid_layer))
        self.assertEqual("mattia_test", valid_layer[0].GetName())

    @override_settings(MEDIA_ROOT="/tmp")
    def test_perform_last_step(self):
        """
        Output params in perform_last_step should return the detail_url and the ID
        of the resource created
        """
        handler = GPKGFileHandler()
        # creating exec_id for the import
        exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="funct1",
            step="step",
            input_params={"files": self.valid_files, "store_spatial_file": True},
        )

        # create_geonode_resource
        resource = handler.create_geonode_resource(
            "layer_name",
            "layer_alternate",
            str(exec_id),
        )
        exec_obj = orchestrator.get_execution_object(str(exec_id))
        handler.create_resourcehandlerinfo(str(handler), resource, exec_obj)
        # calling the last_step
        handler.perform_last_step(str(exec_id))
        expected_output = {"resources": [{"id": resource.pk, "detail_url": resource.detail_url}]}
        exec_obj.refresh_from_db()
        self.assertDictEqual(expected_output, exec_obj.output_params)

    @override_settings(IMPORTER_ENABLE_DYN_MODELS=False)
    def test_upsert_validation_should_fail(self):
        """
        The test should fail since the dynamic model generation is not enabled
        """
        handler = ShapeFileHandler()
        with self.assertRaises(Exception) as exept:
            handler.upsert_validation(["files"], 123)

        self.assertIsNotNone(exept)
        self.assertEqual(
            str(exept.exception),
            "The Dynamic model generation must be enabled to perform the upsert IMPORTER_ENABLE_DYN_MODELS=True",
        )

    @override_settings(IMPORTER_ENABLE_DYN_MODELS=True)
    @patch("geonode.upload.handlers.common.vector.ModelSchema")
    @patch("geonode.upload.handlers.common.vector.BaseVectorFileHandler.extract_upsert_key")
    def test_upsert_data_should_fail_if_upsertkey_is_not_provided(self, upsert_function, schema):
        """
        The test should fail since the upsert key provided is empty/Null and
        was not possible to extract the key from the DB schema
        """
        schema.return_value = MagicMock()
        data = create_single_dataset("example_upsert_dataset")
        exec_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="funct1",
            step="step",
            input_params={"files": self.valid_files, "skip_existing_layer": True, "resource_pk": data.pk},
        )

        upsert_function.return_value = None
        handler = ShapeFileHandler()
        with self.assertRaises(Exception) as exept:
            handler.upsert_data(["files"], exec_id)

        self.assertIsNotNone(exept)
        self.assertEqual(
            str(exept.exception),
            "Was not possible to find the upsert key, upsert is aborted",
        )

    def test_get_error_file_csv_headers(self):
        handler = BaseVectorFileHandler()
        mock_validator = MagicMock()
        mock_validator.restrictions = {"type": {"restrictions": {"enumeration": ["type1"]}}}
        with patch("geonode.upload.handlers.common.vector.feature_validators_registry.HANDLERS", [mock_validator]):
            headers = handler._BaseVectorFileHandler__get_csv_headers()
            self.assertEqual(headers, ["fid", "type", "error"])

    @patch("geonode.upload.handlers.common.vector.Popen")
    def test_copy_table_with_ogr2ogr(self, mock_popen):
        comm = MagicMock()
        comm.communicate.return_value = b"", b""
        mock_popen.return_value = comm

        BaseVectorFileHandler.copy_table_with_ogr2ogr("original_table", "new_table", "datastore")

        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]

        self.assertIn("ogr2ogr", call_args[0])
        self.assertIn("-nln", call_args)
        self.assertIn("new_table", call_args)
        self.assertIn("original_table", call_args)


class TestUpsertBaseVectorHandler(TransactionImporterBaseTestSupport):
    """
    Tests for the basic functionality of the upsert methods
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.handler = BaseVectorFileHandler()
        cls.json_handler = GeoJsonFileHandler()
        cls.user = get_user_model().objects.exclude(username="Anonymous").first()
        cls.original = {
            "base_file": f"{project_dir}/tests/fixture/upsert/original.json",
        }
        cls.upsert_geojson = {
            "base_file": f"{project_dir}/tests/fixture/upsert/upsert.json",
        }

        cls.url = reverse("importer_upload")
        ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]

        _user, _password = ogc_server_settings.credentials

        cls.cat = Catalog(service_url=ogc_server_settings.rest, username=_user, password=_password)

    def setUp(self) -> None:
        self.admin, _ = get_user_model().objects.get_or_create(username="admin")
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()

    def test_upsert_data_without_dynamic_model_schema(self):
        """
        Should raise error if the dynamic model schema is not present
        """
        data = create_single_dataset("example_upsert_dataset")
        exec_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="funct1",
            step="step",
            input_params={"files": self.original, "skip_existing_layer": True, "resource_pk": data.pk},
        )
        with self.assertRaises(UpsertException) as exp:
            self.handler.upsert_data(self.original, exec_id)

        self.assertEqual(
            str(exp.exception),
            "This dataset does't support updates. Please upload the dataset again to have the upsert operations enabled",
        )

    def test_upsert_data_raise_error_if_upsert_key_is_not_defined(self):
        """
        Should raise error if the dynamic model schema is not present
        """
        data = create_single_dataset("example_upsert_dataset")
        exec_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="funct1",
            step="step",
            input_params={
                "files": self.original,
                "skip_existing_layer": True,
                "resource_pk": data.pk,
                "upsert_key": None,
            },
        )
        ModelSchema.objects.create(name="example_upsert_dataset", db_name="datastore", managed=True)

        with self.assertRaises(UpsertException) as exp:
            self.handler.upsert_data(self.original, exec_id)

        self.assertEqual(str(exp.exception), "Was not possible to find the upsert key, upsert is aborted")

    def test_validate_single_feature_raise_error(self):
        """
        Should raise error if the dynamic model schema is not present
        """
        data = create_single_dataset("example_upsert_dataset")
        exec_id = orchestrator.create_execution_request(
            user=self.user,
            func_name="funct1",
            step="step",
            input_params={
                "files": self.original,
                "skip_existing_layer": True,
                "resource_pk": data.pk,
                "upsert_key": "id",
            },
        )
        ModelSchema.objects.create(name="example_upsert_dataset", db_name="datastore", managed=True)

        with self.assertRaises(Exception) as exp:
            self.json_handler.upsert_data(self.original, exec_id)
        self.assertEqual(
            str(exp.exception), "An internal error occurred during upsert save. All features are rolled back."
        )
