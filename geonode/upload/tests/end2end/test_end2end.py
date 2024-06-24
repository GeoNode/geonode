import ast
import os
import time
from uuid import uuid4

import mock
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.urls import reverse
from dynamic_models.models import FieldSchema, ModelSchema
from geonode.layers.models import Dataset
from geonode.resource.models import ExecutionRequest
from geonode.utils import OGC_Servers_Handler
from geoserver.catalog import Catalog
from importer import project_dir
from geonode.upload.tests.utils import ImporterBaseTestSupport
import gisdata
from geonode.base.populate_test_data import create_single_dataset
from django.db.models import Q
from geonode.base.models import ResourceBase
from geonode.resource.manager import resource_manager

geourl = settings.GEODATABASE_URL


class BaseImporterEndToEndTest(ImporterBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = get_user_model().objects.exclude(username="Anonymous").first()
        cls.valid_gkpg = f"{project_dir}/tests/fixture/valid.gpkg"
        cls.valid_geojson = f"{project_dir}/tests/fixture/valid.geojson"
        cls.no_crs_gpkg = f"{project_dir}/tests/fixture/noCrsTable.gpkg"
        file_path = gisdata.VECTOR_DATA
        filename = os.path.join(file_path, "san_andres_y_providencia_highway.shp")
        cls.valid_shp = {
            "base_file": filename,
            "dbf_file": f"{file_path}/san_andres_y_providencia_highway.dbf",
            "prj_file": f"{file_path}/san_andres_y_providencia_highway.prj",
            "shx_file": f"{file_path}/san_andres_y_providencia_highway.shx",
        }
        cls.valid_kml = f"{project_dir}/tests/fixture/valid.kml"
        cls.valid_tif = f"{project_dir}/tests/fixture/test_grid.tif"
        cls.valid_csv = f"{project_dir}/tests/fixture/valid.csv"

        cls.url = reverse("importer_upload")
        ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]

        _user, _password = ogc_server_settings.credentials

        cls.cat = Catalog(service_url=ogc_server_settings.rest, username=_user, password=_password)

    def setUp(self) -> None:
        self.admin = get_user_model().objects.get(username="admin")
        for el in Dataset.objects.all():
            el.delete()

    def tearDown(self) -> None:
        super().tearDown()
        for el in Dataset.objects.all():
            el.delete()

    def _assertimport(
        self,
        payload,
        initial_name,
        overwrite=False,
        last_update=None,
        skip_geoserver=False,
    ):
        try:
            self.client.force_login(self.admin)

            response = self.client.post(self.url, data=payload)
            self.assertEqual(201, response.status_code, response.json())

            # if is async, we must wait. It will wait for 1 min before raise exception
            if ast.literal_eval(os.getenv("ASYNC_SIGNALS", "False")):
                tentative = 1
                while (
                    ExecutionRequest.objects.get(exec_id=response.json().get("execution_id"))
                    != ExecutionRequest.STATUS_FINISHED
                    and tentative <= 10
                ):
                    time.sleep(10)
                    tentative += 1
            if (
                ExecutionRequest.objects.get(exec_id=response.json().get("execution_id")).status
                != ExecutionRequest.STATUS_FINISHED
            ):
                raise Exception("Async still in progress after 1 min of waiting")

            # check if the dynamic model is created
            if os.getenv("IMPORTER_ENABLE_DYN_MODELS", False):
                _schema_id = ModelSchema.objects.filter(name__icontains=initial_name)
                self.assertTrue(_schema_id.exists())
                schema_entity = _schema_id.first()
                self.assertTrue(FieldSchema.objects.filter(model_schema=schema_entity).exists())

                # Verify that ogr2ogr created the table with some data in it
                entries = ModelSchema.objects.filter(id=schema_entity.id).first()
                self.assertTrue(entries.as_model().objects.exists())

            # check if the geonode resource exists
            resource = ResourceBase.objects.filter(
                Q(alternate__icontains=f"geonode:{initial_name}") | Q(alternate__icontains=initial_name)
            )
            self.assertTrue(resource.exists())

            if not skip_geoserver:
                resources = self.cat.get_resources()
                # check if the resource is in geoserver
                self.assertTrue(resource.first().title in [y.name for y in resources])
            if overwrite:
                self.assertTrue(resource.first().last_updated > last_update)
        finally:
            resource = ResourceBase.objects.filter(
                Q(alternate__icontains=f"geonode:{initial_name}") | Q(alternate__icontains=initial_name)
            )
            resource.delete()


class ImporterGeoPackageImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geopackage(self):
        layer = self.cat.get_layer("geonode:stazioni_metropolitana")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.valid_gkpg, "rb"),
        }
        initial_name = "stazioni_metropolitana"
        self._assertimport(payload, initial_name)
        layer = self.cat.get_layer("geonode:stazioni_metropolitana")
        if layer:
            self.cat.delete(layer)

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_gpkg_overwrite(self):
        prev_dataset = create_single_dataset(name="stazioni_metropolitana")

        layer = self.cat.get_layer("geonode:stazioni_metropolitana")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.valid_gkpg, "rb"),
        }
        initial_name = "stazioni_metropolitana"
        payload["overwrite_existing_layer"] = True
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        layer = self.cat.get_layer("geonode:stazioni_metropolitana")
        if layer:
            self.cat.delete(layer)


class ImporterNoCRSImportTest(BaseImporterEndToEndTest):
    @override_settings(ASYNC_SIGNALS=False)
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geopackage_with_no_crs_table(self):
        layer = self.cat.get_layer("geonode:mattia_test")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.no_crs_gpkg, "rb"),
        }
        initial_name = "mattia_test"
        with self.assertLogs(level="ERROR") as _log:
            self._assertimport(payload, initial_name)

        self.assertIn(
            "The following layer layer_styles does not have a Coordinate Reference System (CRS) and will be skipped.",
            [x.message for x in _log.records],
        )
        layer = self.cat.get_layer("geonode:mattia_test")
        if layer:
            self.cat.delete(layer)

    @override_settings(ASYNC_SIGNALS=False)
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    @mock.patch("importer.handlers.common.vector.BaseVectorFileHandler._select_valid_layers")
    @override_settings(MEDIA_ROOT="/tmp/", ASSETS_ROOT="/tmp/")
    def test_import_geopackage_with_no_crs_table_should_raise_error_if_all_layer_are_invalid(
        self, _select_valid_layers
    ):
        _select_valid_layers.return_value = []
        layer = self.cat.get_layer("geonode:mattia_test")
        if layer:
            self.cat.delete(layer)

        payload = {
            "base_file": open(self.no_crs_gpkg, "rb"),
            "store_spatial_file": True,
        }

        with self.assertLogs(level="ERROR") as _log:
            self.client.force_login(self.admin)

            response = self.client.post(self.url, data=payload)
            self.assertEqual(500, response.status_code)

        self.assertIn(
            "No valid layers found",
            [x.message for x in _log.records],
        )
        layer = self.cat.get_layer("geonode:mattia_test")
        if layer:
            self.cat.delete(layer)


class ImporterGeoJsonImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geojson(self):
        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)

        payload = {
            "base_file": open(self.valid_geojson, "rb"),
        }
        initial_name = "valid"
        self._assertimport(payload, initial_name)
        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geojson_overwrite(self):
        prev_dataset = create_single_dataset(name="valid")

        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.valid_geojson, "rb"),
        }
        initial_name = "valid"
        payload["overwrite_existing_layer"] = True
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)


class ImporterGCSVImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geojson(self):
        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)

        payload = {
            "base_file": open(self.valid_csv, "rb"),
        }
        initial_name = "valid"
        self._assertimport(payload, initial_name)
        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_csv_overwrite(self):
        prev_dataset = create_single_dataset(name="valid")

        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.valid_csv, "rb"),
        }
        initial_name = "valid"
        payload["overwrite_existing_layer"] = True
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        layer = self.cat.get_layer("geonode:valid")
        if layer:
            self.cat.delete(layer)


class ImporterKMLImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_kml(self):
        layer = self.cat.get_layer("geonode:sample_point_dataset")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.valid_kml, "rb"),
        }
        initial_name = "sample_point_dataset"
        self._assertimport(payload, initial_name)
        layer = self.cat.get_layer("geonode:sample_point_dataset")
        if layer:
            self.cat.delete(layer)

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_kml_overwrite(self):
        prev_dataset = create_single_dataset(name="sample_point_dataset")

        layer = self.cat.get_layer("geonode:sample_point_dataset")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.valid_kml, "rb"),
        }
        initial_name = "sample_point_dataset"
        payload["overwrite_existing_layer"] = True
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        layer = self.cat.get_layer("geonode:sample_point_dataset")
        if layer:
            self.cat.delete(layer)


class ImporterShapefileImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_shapefile(self):
        layer = self.cat.get_layer("geonode:san_andres_y_providencia_highway")
        if layer:
            self.cat.delete(layer)
        payload = {_filename: open(_file, "rb") for _filename, _file in self.valid_shp.items()}
        initial_name = "san_andres_y_providencia_highway"
        self._assertimport(payload, initial_name)
        if layer:
            layer = self.cat.get_layer("geonode:san_andres_y_providencia_highway")
            self.cat.delete(layer)

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_shapefile_overwrite(self):

        prev_dataset = create_single_dataset(name="san_andres_y_providencia_highway")

        layer = self.cat.get_layer("geonode:san_andres_y_providencia_highway")
        if layer:
            self.cat.delete(layer)
        payload = {_filename: open(_file, "rb") for _filename, _file in self.valid_shp.items()}
        initial_name = "san_andres_y_providencia_highway"
        payload["overwrite_existing_layer"] = True
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        layer = self.cat.get_layer("geonode:san_andres_y_providencia_highway")
        if layer:
            self.cat.delete(layer)


class ImporterRasterImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_raster(self):
        layer = self.cat.get_layer("test_grid")
        if layer:
            self.cat.delete(layer)

        payload = {
            "base_file": open(self.valid_tif, "rb"),
        }
        initial_name = "test_grid"
        self._assertimport(payload, initial_name)
        layer = self.cat.get_layer("test_grid")
        if layer:
            self.cat.delete(layer)

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_raster_overwrite(self):
        prev_dataset = create_single_dataset(name="test_grid")

        layer = self.cat.get_layer("test_grid")
        if layer:
            self.cat.delete(layer)
        payload = {
            "base_file": open(self.valid_tif, "rb"),
        }
        initial_name = "test_grid"
        payload["overwrite_existing_layer"] = True
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        layer = self.cat.get_layer("test_grid")
        if layer:
            self.cat.delete(layer)
