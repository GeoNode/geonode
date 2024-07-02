import os
from dynamic_models.models import ModelSchema, FieldSchema
import mock
from geonode.base.populate_test_data import create_single_dataset
from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.tests.utils import TransactionImporterBaseTestSupport
import uuid


class TestModelSchemaSignal(TransactionImporterBaseTestSupport):
    databases = ("default", "datastore")

    def setUp(self):
        self.resource = create_single_dataset(name=f"test_dataset_{uuid.uuid4()}")
        ResourceHandlerInfo.objects.create(
            resource=self.resource,
            handler_module_path="importer.handlers.shapefile.handler.ShapeFileHandler",
        )
        self.dynamic_model = ModelSchema.objects.create(name=self.resource.name, db_name="datastore")
        self.dynamic_model_field = FieldSchema.objects.create(
            name="field",
            class_name="django.db.models.IntegerField",
            model_schema=self.dynamic_model,
        )

    @mock.patch.dict(os.environ, {"IMPORTER_ENABLE_DYN_MODELS": "True"})
    def test_delete_dynamic_model(self):
        """
        Ensure that the dynamic model is deleted
        """
        # create needed resource handler info

        ResourceHandlerInfo.objects.create(
            resource=self.resource,
            handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
        )
        self.resource.delete()
        self.assertFalse(ModelSchema.objects.filter(name="test_dataset").exists())
        self.assertFalse(FieldSchema.objects.filter(model_schema=self.dynamic_model, name="field").exists())
