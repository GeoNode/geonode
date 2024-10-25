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

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from unittest.mock import patch
from geonode.upload.api.exceptions import InvalidInputFileException

from geonode.upload.celery_tasks import (
    copy_dynamic_model,
    copy_geonode_data_table,
    copy_geonode_resource,
    create_dynamic_structure,
    create_geonode_resource,
    import_orchestrator,
    import_resource,
    orchestrator,
    publish_resource,
    rollback,
)
from geonode.resource.models import ExecutionRequest
from geonode.layers.models import Dataset
from geonode.resource.enumerator import ExecutionRequestAction
from geonode.base.models import ResourceBase
from geonode.base.populate_test_data import create_single_dataset
from geonode.assets.handlers import asset_handler_registry
from dynamic_models.models import ModelSchema, FieldSchema
from dynamic_models.exceptions import DynamicModelError, InvalidFieldNameError
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload import project_dir

from geonode.upload.tests.utils import (
    ImporterBaseTestSupport,
    TransactionImporterBaseTestSupport,
)

# Create your tests here.


class TestCeleryTasks(ImporterBaseTestSupport):
    def setUp(self):
        self.user = get_user_model().objects.first()
        self.existing_file = f"{project_dir}/tests/fixture/valid.gpkg"
        self.asset_handler = asset_handler_registry.get_default_handler()

        self.asset = self.asset_handler.create(
            title="Original",
            owner=self.user,
            description=None,
            type="gpkg",
            files=[self.existing_file],
            clone_files=False,
        )

        self.exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.get(username=self.user),
            func_name="dummy_func",
            step="dummy_step",
            input_params={
                "files": {"base_file": self.existing_file},
                # "overwrite_existing_layer": True,
                "store_spatial_files": True,
                "asset_id": self.asset.id,
                "asset_module_path": f"{self.asset.__module__}.{self.asset.__class__.__name__}",
            },
        )

    @patch("geonode.upload.celery_tasks.orchestrator.perform_next_step")
    def test_import_orchestrator_dont_create_exececution_request_if_not__none(self, importer):
        user = get_user_model().objects.first()
        count = ExecutionRequest.objects.count()

        import_orchestrator(
            files={"base_file": "/tmp/file.gpkg"},
            store_spatial_files=True,
            user=user.username,
            execution_id="some value",
        )

        self.assertEqual(count, ExecutionRequest.objects.count())
        importer.assert_called_once()

    @patch("geonode.upload.celery_tasks.orchestrator.perform_next_step")
    @patch("geonode.upload.celery_tasks.DataStoreManager.input_is_valid")
    def test_import_resource_should_rase_exp_if_is_invalid(
        self,
        is_valid,
        importer,
    ):
        user = get_user_model().objects.first()

        exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.get(username=user),
            func_name="dummy_func",
            step="dummy_step",
            input_params={"files": self.existing_file, "store_spatial_files": True},
        )

        is_valid.side_effect = Exception("Invalid format type")

        with self.assertRaises(InvalidInputFileException) as _exc:
            import_resource(
                str(exec_id),
                action=ExecutionRequestAction.UPLOAD.value,
                handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
            )
        expected_msg = f"Invalid format type. Request: {str(exec_id)}"
        self.assertEqual(expected_msg, str(_exc.exception.detail))
        ExecutionRequest.objects.filter(exec_id=str(exec_id)).delete()

    @patch("geonode.upload.celery_tasks.orchestrator.perform_next_step")
    @patch("geonode.upload.celery_tasks.DataStoreManager.input_is_valid")
    @patch("geonode.upload.celery_tasks.DataStoreManager.prepare_import")
    @patch("geonode.upload.celery_tasks.DataStoreManager.start_import")
    def test_import_resource_should_work(
        self,
        prepare_import,
        start_import,
        is_valid,
        importer,
    ):
        is_valid.return_value = True
        user = get_user_model().objects.first()

        exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.get(username=user),
            func_name="dummy_func",
            step="dummy_step",
            input_params={"files": self.existing_file, "store_spatial_files": True},
        )

        import_resource(
            str(exec_id),
            resource_type="gpkg",
            action=ExecutionRequestAction.UPLOAD.value,
            handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
        )

        prepare_import.assert_called_once()
        start_import.assert_called_once()
        ExecutionRequest.objects.filter(exec_id=str(exec_id)).delete()

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    @patch("geonode.upload.celery_tasks.DataPublisher.extract_resource_to_publish")
    @patch("geonode.upload.celery_tasks.DataPublisher.publish_resources")
    def test_publish_resource_should_work(
        self,
        publish_resources,
        extract_resource_to_publish,
        importer,
    ):
        try:
            publish_resources.return_value = True
            extract_resource_to_publish.return_value = [{"crs": 12345, "name": "dataset3"}]

            publish_resource(
                str(self.exec_id),
                resource_type="gpkg",
                step_name="publish_resource",
                layer_name="dataset3",
                alternate="alternate_dataset3",
                action=ExecutionRequestAction.UPLOAD.value,
                handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
            )

            # Evaluation
            req = ExecutionRequest.objects.get(exec_id=str(self.exec_id))
            self.assertEqual(publish_resources.call_count, 1)
            self.assertEqual("geonode.upload.publish_resource", req.step)
            importer.assert_called_once()
        finally:
            # cleanup
            if self.exec_id:
                ExecutionRequest.objects.filter(exec_id=str(self.exec_id)).delete()

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    @patch("geonode.upload.celery_tasks.DataPublisher.extract_resource_to_publish")
    @patch("geonode.upload.celery_tasks.DataPublisher.publish_resources")
    def test_publish_resource_if_overwrite_should_call_the_publishing(
        self,
        publish_resources,
        extract_resource_to_publish,
        importer,
    ):
        """
        Publish resource should be called since the resource does not exists in geoserver
        even if an overwrite is required
        """
        try:
            publish_resources.return_value = True
            extract_resource_to_publish.return_value = [{"crs": 12345, "name": "dataset3"}]
            exec_id = orchestrator.create_execution_request(
                user=get_user_model().objects.get(username=self.user),
                func_name="dummy_func",
                step="dummy_step",
                input_params={
                    "files": {"base_file": self.existing_file},
                    "overwrite_existing_layer": True,
                    "store_spatial_files": True,
                },
            )
            publish_resource(
                str(exec_id),
                resource_type="gpkg",
                step_name="publish_resource",
                layer_name="dataset3",
                alternate="alternate_dataset3",
                action=ExecutionRequestAction.UPLOAD.value,
                handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
            )

            # Evaluation
            req = ExecutionRequest.objects.get(exec_id=str(exec_id))
            self.assertEqual("geonode.upload.publish_resource", req.step)
            publish_resources.assert_called_once()
            importer.assert_called_once()

        finally:
            # cleanup
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=str(exec_id)).delete()

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    @patch("geonode.upload.celery_tasks.DataPublisher.extract_resource_to_publish")
    @patch("geonode.upload.celery_tasks.DataPublisher.publish_resources")
    @patch("geonode.upload.celery_tasks.DataPublisher.get_resource")
    def test_publish_resource_if_overwrite_should_not_call_the_publishing(
        self,
        get_resource,
        publish_resources,
        extract_resource_to_publish,
        importer,
    ):
        """
        Publish resource should be called since the resource does not exists in geoserver
        even if an overwrite is required.
        Should raise error if the crs is not found
        """
        try:
            with self.assertRaises(Exception):
                get_resource.return_value = True
                publish_resources.return_value = True
                extract_resource_to_publish.return_value = [{"crs": 4326, "name": "dataset3"}]
                exec_id = orchestrator.create_execution_request(
                    user=get_user_model().objects.get(username=self.user),
                    func_name="dummy_func",
                    step="dummy_step",
                    input_params={
                        "files": {"base_file": self.existing_file},
                        "overwrite_existing_layer": True,
                        "store_spatial_files": True,
                    },
                )
                publish_resource(
                    str(exec_id),
                    resource_type="gpkg",
                    step_name="publish_resource",
                    layer_name="dataset3",
                    alternate="alternate_dataset3",
                    action=ExecutionRequestAction.UPLOAD.value,
                    handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
                )

                # Evaluation
                req = ExecutionRequest.objects.get(exec_id=str(exec_id))
                self.assertEqual("geonode.upload.publish_resource", req.step)
                publish_resources.assert_not_called()
                importer.assert_called_once()

        finally:
            # cleanup
            if exec_id:
                ExecutionRequest.objects.filter(exec_id=str(exec_id)).delete()

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    def test_create_geonode_resource(self, import_orchestrator):
        try:
            alternate = "geonode:alternate_foo_dataset"
            self.assertFalse(Dataset.objects.filter(alternate=alternate).exists())

            create_geonode_resource(
                str(self.exec_id),
                resource_type="gpkg",
                step_name="create_geonode_resource",
                layer_name="foo_dataset",
                alternate="alternate_foo_dataset",
                handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
                action="upload",
            )

            # Evaluation
            req = ExecutionRequest.objects.get(exec_id=str(self.exec_id))
            self.assertEqual("geonode.upload.create_geonode_resource", req.step)

            self.assertTrue(Dataset.objects.filter(alternate=alternate).exists())

            import_orchestrator.assert_called_once()

        finally:
            # cleanup
            if Dataset.objects.filter(alternate=alternate).exists():
                Dataset.objects.filter(alternate=alternate).delete()

    @patch("geonode.upload.celery_tasks.call_rollback_function")
    def test_copy_geonode_resource_should_raise_exeption_if_the_alternate_not_exists(self, call_rollback_function):
        with self.assertRaises(Exception):
            copy_geonode_resource(
                str(self.exec_id),
                "geonode.upload.copy_geonode_resource",
                "cloning",
                "invalid_alternate",
                "geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
                "copy",
                kwargs={
                    "original_dataset_alternate": "geonode:example_dataset",
                    "new_dataset_alternate": "geonode:schema_copy_example_dataset",  # this alternate is generated dring the geonode resource copy
                },
            )
        call_rollback_function.assert_called_once()

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    def test_copy_geonode_resource(self, async_call):
        alternate = "geonode:cloning"
        new_alternate = None
        try:
            rasource = create_single_dataset(name="cloning")

            exec_id, new_alternate = copy_geonode_resource(
                str(self.exec_id),
                "geonode.upload.copy_geonode_resource",
                "cloning",
                rasource.alternate,
                "geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
                "copy",
                kwargs={
                    "original_dataset_alternate": "geonode:cloning",
                    "new_dataset_alternate": "geonode:schema_copy_cloning",  # this alternate is generated dring the geonode resource copy
                },
            )

            self.assertTrue(ResourceBase.objects.filter(alternate__icontains=new_alternate).exists())
            async_call.assert_called_once()

        finally:
            # cleanup
            if Dataset.objects.filter(alternate=alternate).exists():
                Dataset.objects.filter(alternate=alternate).delete()
            if new_alternate:
                Dataset.objects.filter(alternate=new_alternate).delete()

    @patch("geonode.upload.handlers.gpkg.handler.GPKGFileHandler._import_resource_rollback")
    @patch("geonode.upload.handlers.gpkg.handler.GPKGFileHandler._publish_resource_rollback")
    @patch("geonode.upload.handlers.gpkg.handler.GPKGFileHandler._create_geonode_resource_rollback")
    @override_settings(MEDIA_ROOT="/tmp/")
    def test_rollback_works_as_expected_vector_step(
        self,
        _create_geonode_resource_rollback,
        _publish_resource_rollback,
        _import_resource_rollback,
    ):
        """
        rollback should remove the resource based on the step it has reached
        """
        test_config = [
            ("geonode.upload.import_resource", [_import_resource_rollback]),
            (
                "geonode.upload.publish_resource",
                [_import_resource_rollback, _publish_resource_rollback],
            ),
            (
                "geonode.upload.create_geonode_resource",
                [
                    _import_resource_rollback,
                    _publish_resource_rollback,
                    _create_geonode_resource_rollback,
                ],
            ),
        ]
        for conf in test_config:
            try:
                exec_id = orchestrator.create_execution_request(
                    user=get_user_model().objects.get(username=self.user),
                    func_name="dummy_func",
                    step=conf[0],  # step name
                    action="upload",
                    input_params={
                        "files": {"base_file": self.existing_file},
                        "store_spatial_files": True,
                        "handler_module_path": "geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
                    },
                )
                rollback(str(exec_id))

                # Evaluation
                req = ExecutionRequest.objects.get(exec_id=str(exec_id))
                self.assertEqual("geonode.upload.rollback", req.step)
                self.assertTrue(req.status == "failed")
                for expected_function in conf[1]:
                    expected_function.assert_called_once()
                    expected_function.reset_mock()
            finally:
                # cleanup
                if exec_id:
                    ExecutionRequest.objects.filter(exec_id=str(exec_id)).delete()

    @patch("geonode.upload.handlers.geotiff.handler.GeoTiffFileHandler._import_resource_rollback")
    @patch("geonode.upload.handlers.geotiff.handler.GeoTiffFileHandler._publish_resource_rollback")
    @patch("geonode.upload.handlers.geotiff.handler.GeoTiffFileHandler._create_geonode_resource_rollback")
    @override_settings(MEDIA_ROOT="/tmp/")
    def test_rollback_works_as_expected_raster(
        self,
        _create_geonode_resource_rollback,
        _publish_resource_rollback,
        _import_resource_rollback,
    ):
        """
        rollback should remove the resource based on the step it has reached
        """
        test_config = [
            ("geonode.upload.import_resource", [_import_resource_rollback]),
            (
                "geonode.upload.publish_resource",
                [_import_resource_rollback, _publish_resource_rollback],
            ),
            (
                "geonode.upload.create_geonode_resource",
                [
                    _import_resource_rollback,
                    _publish_resource_rollback,
                    _create_geonode_resource_rollback,
                ],
            ),
        ]
        for conf in test_config:
            try:
                exec_id = orchestrator.create_execution_request(
                    user=get_user_model().objects.get(username=self.user),
                    func_name="dummy_func",
                    step=conf[0],  # step name
                    action="upload",
                    input_params={
                        "files": {"base_file": "/tmp/filepath"},
                        "store_spatial_files": True,
                        "handler_module_path": "geonode.upload.handlers.geotiff.handler.GeoTiffFileHandler",
                    },
                )
                rollback(str(exec_id))

                # Evaluation
                req = ExecutionRequest.objects.get(exec_id=str(exec_id))
                self.assertEqual("geonode.upload.rollback", req.step)
                self.assertTrue(req.status == "failed")
                for expected_function in conf[1]:
                    expected_function.assert_called_once()
                    expected_function.reset_mock()
            finally:
                # cleanup
                if exec_id:
                    ExecutionRequest.objects.filter(exec_id=str(exec_id)).delete()

    @override_settings(MEDIA_ROOT="/tmp/")
    def test_import_metadata_should_work_as_expected(self):
        handler = "geonode.upload.handlers.xml.handler.XMLFileHandler"
        # lets copy the file to the temporary folder
        # later will be removed
        valid_xml = f"{settings.PROJECT_ROOT}/base/fixtures/test_xml.xml"
        shutil.copy(valid_xml, "/tmp")
        xml_in_tmp = "/tmp/test_xml.xml"

        user, _ = get_user_model().objects.get_or_create(username="admin")
        valid_files = {"base_file": xml_in_tmp, "xml_file": xml_in_tmp}

        layer = create_single_dataset("test_dataset_importer")
        exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.first(),
            func_name="funct1",
            step="step",
            input_params={
                "files": valid_files,
                "resource_pk": layer.pk,
                "skip_existing_layer": True,
                "handler_module_path": str(handler),
            },
        )
        ResourceHandlerInfo.objects.create(
            resource=layer,
            handler_module_path="geonode.upload.handlers.shapefile.handler.ShapeFileHandler",
        )

        import_resource(str(exec_id), handler, "import")

        layer.refresh_from_db()
        self.assertEqual(layer.title, "test_dataset")


class TestDynamicModelSchema(TransactionImporterBaseTestSupport):
    databases = ("default", "datastore")

    def setUp(self):
        self.user = get_user_model().objects.first()
        self.existing_file = f"{project_dir}/tests/fixture/valid.gpkg"
        self.exec_id = orchestrator.create_execution_request(
            user=get_user_model().objects.get(username=self.user),
            func_name="dummy_func",
            step="dummy_step",
            input_params={
                "files": {"base_file": self.existing_file},
                # "overwrite_existing_layer": True,
                "store_spatial_files": True,
            },
        )

    def test_create_dynamic_structure_should_raise_error_if_schema_is_not_available(
        self,
    ):
        with self.assertRaises(DynamicModelError) as _exc:
            create_dynamic_structure(
                execution_id=str(self.exec_id),
                fields=[],
                dynamic_model_schema_id=0,
                overwrite=False,
                layer_name="test_layer",
            )

        expected_msg = "The model with id 0 does not exists."
        self.assertEqual(expected_msg, str(_exc.exception))

    def test_create_dynamic_structure_should_raise_error_if_field_class_is_none(self):
        try:
            name = str(self.exec_id)

            schema = ModelSchema.objects.create(name=f"schema_{name}", db_name="datastore")
            dynamic_fields = [
                {"name": "field1", "class_name": None, "null": True},
            ]
            with self.assertRaises(InvalidFieldNameError) as _exc:
                create_dynamic_structure(
                    execution_id=str(self.exec_id),
                    fields=dynamic_fields,
                    dynamic_model_schema_id=schema.pk,
                    overwrite=False,
                    layer_name="test_layer",
                )

            expected_msg = (
                "Error during the field creation. The field or class_name is None {'name': 'field1', 'class_name': None, 'null': True} for test_layer "
                + f"for execution {name}"
            )
            self.assertEqual(expected_msg, str(_exc.exception))
        finally:
            ModelSchema.objects.filter(name=f"schema_{name}").delete()

    def test_create_dynamic_structure_should_work(self):
        try:
            name = str(self.exec_id)

            schema = ModelSchema.objects.create(name=f"schema_{name}", db_name="datastore")
            dynamic_fields = [
                {
                    "name": "field1",
                    "class_name": "django.contrib.gis.db.models.fields.LineStringField",
                    "null": True,
                },
            ]

            create_dynamic_structure(
                execution_id=str(self.exec_id),
                fields=dynamic_fields,
                dynamic_model_schema_id=schema.pk,
                overwrite=False,
                layer_name="test_layer",
            )

            self.assertTrue(FieldSchema.objects.filter(name="field1").exists())

        finally:
            ModelSchema.objects.filter(name=f"schema_{name}").delete()
            FieldSchema.objects.filter(name="field1").delete()

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    @patch.dict(os.environ, {"IMPORTER_ENABLE_DYN_MODELS": "True"})
    def test_copy_dynamic_model_should_work(self, async_call):
        try:
            name = str(self.exec_id)
            # setup model schema to be copied
            schema = ModelSchema.objects.create(
                name=f"schema_{name}",
                db_name="datastore",
                db_table_name=f"schema_{name}",
            )
            FieldSchema.objects.create(
                name=f"field_{name}",
                class_name="django.contrib.gis.db.models.fields.LineStringField",
                model_schema=schema,
            )

            layer = create_single_dataset(f"schema_{name}")
            layer.alternate = f"geonode:schema_{name}"
            layer.save()

            self.assertTrue(ModelSchema.objects.filter(name__icontains="schema_").count() == 1)

            copy_dynamic_model(
                exec_id=str(self.exec_id),
                actual_step="copy",
                layer_name=f"schema_{name}",
                alternate=f"geonode:schema_{name}",
                handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
                action=ExecutionRequestAction.COPY.value,
                kwargs={
                    "original_dataset_alternate": f"geonode:schema_{name}",
                },
            )
            # the alternate is generated internally
            self.assertTrue(ModelSchema.objects.filter(name=f"schema_{name}").exists())
            self.assertTrue(ModelSchema.objects.filter(name__icontains="schema_").count() == 2)

            schema = ModelSchema.objects.all()
            for val in schema:
                self.assertEqual(val.name, val.db_table_name)

            async_call.assert_called_once()

        finally:
            ModelSchema.objects.filter(name="schema_").delete()
            FieldSchema.objects.filter(name="field_").delete()

    @patch("geonode.upload.celery_tasks.import_orchestrator.apply_async")
    @patch("geonode.upload.celery_tasks.connections")
    def test_copy_geonode_data_table_should_work(self, mock_connection, async_call):
        mock_cursor = mock_connection.__getitem__("datastore").cursor.return_value.__enter__.return_value
        ModelSchema.objects.create(name=f"schema_copy_{str(self.exec_id)}", db_name="datastore")

        copy_geonode_data_table(
            exec_id=str(self.exec_id),
            actual_step="copy",
            layer_name=f"schema_{str(self.exec_id)}",
            alternate=f"geonode:schema_{str(self.exec_id)}",
            handlers_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
            action=ExecutionRequestAction.COPY.value,
            kwargs={
                "original_dataset_alternate": f"geonode:schema_{str(self.exec_id)}",
                "new_dataset_alternate": f"schema_copy_{str(self.exec_id)}",  # this alternate is generated dring the geonode resource copy
            },
        )
        mock_cursor.execute.assert_called_once()
        mock_cursor.execute.assert_called()
        async_call.assert_called_once()
