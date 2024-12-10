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
import ast
import os
import time

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
from geonode.upload import project_dir
from geonode.upload.tests.utils import ImporterBaseTestSupport
import gisdata
from django.db.models import Q
from geonode.base.models import ResourceBase
import logging
from geonode.harvesting.harvesters.wms import WebMapService
from django.forms.models import model_to_dict
from unittest import skip

logger = logging.getLogger()
geourl = settings.GEODATABASE_URL


@override_settings(FILE_UPLOAD_DIRECTORY_PERMISSIONS=0o777, FILE_UPLOAD_PERMISSIONS=0o7777)
class BaseImporterEndToEndTest(ImporterBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = get_user_model().objects.exclude(username="Anonymous").first()
        cls.valid_gkpg = f"{project_dir}/tests/fixture/valid.gpkg"
        cls.valid_geojson = f"{project_dir}/tests/fixture/valid.geojson"
        cls.no_crs_gpkg = f"{project_dir}/tests/fixture/noCrsTable.gpkg"
        file_path = gisdata.PROJECT_ROOT
        filename = os.path.join(file_path, "both/good/sangis.org/Airport/Air_Runways.shp")
        cls.valid_shp = {
            "base_file": filename,
            "dbf_file": f"{file_path}/both/good/sangis.org/Airport/Air_Runways.dbf",
            "prj_file": f"{file_path}/both/good/sangis.org/Airport/Air_Runways.prj",
            "shx_file": f"{file_path}/both/good/sangis.org/Airport/Air_Runways.shx",
        }
        cls.valid_kml = f"{project_dir}/tests/fixture/valid.kml"
        cls.valid_tif = f"{project_dir}/tests/fixture/test_raster.tif"
        cls.valid_csv = f"{project_dir}/tests/fixture/valid.csv"

        cls.url = reverse("importer_upload")
        ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]

        _user, _password = ogc_server_settings.credentials

        cls.cat = Catalog(service_url=ogc_server_settings.rest, username=_user, password=_password)

    def setUp(self) -> None:
        self.admin, _ = get_user_model().objects.get_or_create(username="admin")
        self.admin.is_superuser = True
        self.admin.is_staff = True
        self.admin.save()
        for el in Dataset.objects.all():
            el.delete()

    def tearDown(self) -> None:
        super().tearDown()
        for el in Dataset.objects.all():
            el.delete()

    def _cleanup_layers(self, name):
        layer = [x for x in self.cat.get_resources() if name in x.name]
        if layer:
            for el in layer:
                try:
                    self.cat.delete(el)
                except:  # noqa
                    pass
        try:
            ResourceBase.objects.filter(alternate__icontains=name).delete()
        except:  # noqa
            pass

    def _assertimport(
        self,
        payload,
        initial_name,
        overwrite=False,
        last_update=None,
        skip_geoserver=False,
        assert_payload=None,
        keep_resource=False,
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
            exc_obj = ExecutionRequest.objects.get(exec_id=response.json().get("execution_id"))
            if exc_obj.status != ExecutionRequest.STATUS_FINISHED:
                raise Exception(f"Async still in progress after 1 min of waiting: {model_to_dict(exc_obj)}")

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
                self.assertTrue(resource.first().title in res for res in [y.name for y in resources])
            if overwrite:
                self.assertTrue(resource.first().last_updated > last_update)

            if assert_payload:
                target = resource.first()
                target.refresh_from_db()
                for key, value in assert_payload.items():
                    if hasattr(target, key):
                        self.assertEqual(getattr(target, key), value)
                    else:
                        logger.error(f"The attribute {key} doesn't belong to the resource.")
            if keep_resource:
                return resource.first()
        finally:
            if not keep_resource:
                resource = ResourceBase.objects.filter(
                    Q(alternate__icontains=f"geonode:{initial_name}") | Q(alternate__icontains=initial_name)
                )
                resource.delete()


class ImporterGeoPackageImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geopackage(self):
        self._cleanup_layers(name="stazioni_metropolitana")

        payload = {"base_file": open(self.valid_gkpg, "rb"), "action": "upload"}
        initial_name = "stazioni_metropolitana"
        self._assertimport(payload, initial_name)
        self._cleanup_layers(name="stazioni_metropolitana")

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_gpkg_overwrite(self):
        self._cleanup_layers(name="stazioni_metropolitana")
        initial_name = "stazioni_metropolitana"
        payload = {"base_file": open(self.valid_gkpg, "rb"), "action": "upload"}
        prev_dataset = self._assertimport(payload, initial_name, keep_resource=True)

        payload = {"base_file": open(self.valid_gkpg, "rb"), "action": "upload"}
        payload["overwrite_existing_layer"] = True
        payload["resource_pk"] = prev_dataset.pk
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        self._cleanup_layers(name="stazioni_metropolitana")


class ImporterNoCRSImportTest(BaseImporterEndToEndTest):
    @override_settings(ASYNC_SIGNALS=False)
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    @skip("unknown fail on circleci")
    def test_import_geopackage_with_no_crs_table(self):

        self._cleanup_layers(name="mattia_test")
        payload = {"base_file": open(self.no_crs_gpkg, "rb"), "action": "upload"}
        initial_name = "mattia_test"
        with self.assertLogs(level="ERROR") as _log:
            self._assertimport(payload, initial_name)

        self.assertIn(
            "The following layer layer_styles does not have a Coordinate Reference System (CRS) and will be skipped.",
            [x.message for x in _log.records],
        )

        self._cleanup_layers(name="mattia_test")

    @override_settings(ASYNC_SIGNALS=False)
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    @mock.patch("geonode.upload.handlers.common.vector.BaseVectorFileHandler._select_valid_layers")
    @override_settings(MEDIA_ROOT="/tmp/", ASSETS_ROOT="/tmp/")
    def test_import_geopackage_with_no_crs_table_should_raise_error_if_all_layer_are_invalid(
        self, _select_valid_layers
    ):
        _select_valid_layers.return_value = []

        self._cleanup_layers(name="mattia_test")
        payload = {"base_file": open(self.no_crs_gpkg, "rb"), "store_spatial_file": True, "action": "upload"}

        with self.assertLogs(level="ERROR") as _log:
            self.client.force_login(self.admin)

            response = self.client.post(self.url, data=payload)
            self.assertEqual(500, response.status_code)

        self.assertIn(
            "No valid layers found",
            [x.message for x in _log.records],
        )

        self._cleanup_layers(name="mattia_test")


class ImporterGeoJsonImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geojson(self):

        self._cleanup_layers(name="valid")

        payload = {"base_file": open(self.valid_geojson, "rb"), "action": "upload"}
        initial_name = "valid"
        self._assertimport(payload, initial_name)

        self._cleanup_layers(name="valid")

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geojson_overwrite(self):
        self._cleanup_layers(name="valid")
        payload = {"base_file": open(self.valid_geojson, "rb"), "action": "upload"}
        initial_name = "valid"
        prev_dataset = self._assertimport(payload, initial_name, keep_resource=True)
        payload = {"base_file": open(self.valid_geojson, "rb"), "action": "upload"}
        payload["overwrite_existing_layer"] = True
        payload["resource_pk"] = prev_dataset.pk
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)

        self._cleanup_layers(name="valid")


class ImporterGCSVImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_geojson(self):
        self._cleanup_layers(name="valid")

        payload = {"base_file": open(self.valid_csv, "rb"), "action": "upload"}
        initial_name = "valid"
        self._assertimport(payload, initial_name)
        self._cleanup_layers(name="valid")

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_csv_overwrite(self):
        self._cleanup_layers(name="valid")
        payload = {"base_file": open(self.valid_csv, "rb"), "action": "upload"}
        initial_name = "valid"
        prev_dataset = self._assertimport(payload, initial_name, keep_resource=True)

        payload = {"base_file": open(self.valid_csv, "rb"), "action": "upload"}
        initial_name = "valid"
        payload["overwrite_existing_layer"] = True
        payload["resource_pk"] = prev_dataset.pk
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        self._cleanup_layers(name="valid")


class ImporterKMLImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_kml(self):
        self._cleanup_layers(name="sample_point_dataset")
        payload = {"base_file": open(self.valid_kml, "rb"), "action": "upload"}
        initial_name = "sample_point_dataset"
        self._assertimport(payload, initial_name)
        self._cleanup_layers(name="sample_point_dataset")

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_kml_overwrite(self):
        initial_name = "sample_point_dataset"

        self._cleanup_layers(name="sample_point_dataset")
        payload = {"base_file": open(self.valid_kml, "rb"), "action": "upload"}
        prev_dataset = self._assertimport(payload, initial_name, keep_resource=True)

        payload = {"base_file": open(self.valid_kml, "rb"), "action": "upload"}
        payload["overwrite_existing_layer"] = True
        payload["resource_pk"] = prev_dataset.pk
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        self._cleanup_layers(name="sample_point_dataset")


class ImporterShapefileImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_shapefile(self):
        self._cleanup_layers(name="air_Runways")
        payload = {_filename: open(_file, "rb") for _filename, _file in self.valid_shp.items()}
        payload["action"] = "upload"
        initial_name = "air_Runways"
        self._assertimport(payload, initial_name)
        self._cleanup_layers(name="air_Runways")

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_shapefile_overwrite(self):

        self._cleanup_layers(name="air_Runways")
        payload = {_filename: open(_file, "rb") for _filename, _file in self.valid_shp.items()}
        payload["action"] = "upload"
        initial_name = "air_Runways"
        prev_dataset = self._assertimport(payload, initial_name, keep_resource=True)
        payload = {_filename: open(_file, "rb") for _filename, _file in self.valid_shp.items()}
        payload["overwrite_existing_layer"] = True
        payload["resource_pk"] = prev_dataset.pk
        payload["action"] = "upload"
        self._assertimport(
            payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated, keep_resource=True
        )
        self._cleanup_layers(name="air_Runways")


class ImporterRasterImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_raster(self):
        self._cleanup_layers(name="test_raster")

        payload = {"base_file": open(self.valid_tif, "rb"), "action": "upload"}
        initial_name = "test_raster"
        self._assertimport(payload, initial_name)
        self._cleanup_layers(name="test_raster")

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_import_raster_overwrite(self):
        initial_name = "test_raster"

        self._cleanup_layers(name="test_raster")
        payload = {"base_file": open(self.valid_tif, "rb"), "action": "upload"}
        prev_dataset = self._assertimport(payload, initial_name, keep_resource=True)

        payload = {"base_file": open(self.valid_tif, "rb"), "action": "upload"}
        initial_name = "test_raster"
        payload["overwrite_existing_layer"] = True
        payload["resource_pk"] = prev_dataset.pk
        self._assertimport(payload, initial_name, overwrite=True, last_update=prev_dataset.last_updated)
        self._cleanup_layers(name="test_raster")


class Importer3dTilesImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data", "ASYNC_SIGNALS": "False"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data", ASYNC_SIGNALS=False)
    def test_import_3dtiles(self):
        payload = {
            "url": "https://raw.githubusercontent.com/CesiumGS/3d-tiles-samples/main/1.1/TilesetWithFullMetadata/tileset.json",
            "title": "Remote Title",
            "type": "3dtiles",
            "action": "upload",
        }
        initial_name = "remote_title"
        assert_payload = {
            "subtype": "3dtiles",
            "title": "Remote Title",
            "resource_type": "dataset",
        }
        self._assertimport(payload, initial_name, skip_geoserver=True, assert_payload=assert_payload)

    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data", "ASYNC_SIGNALS": "False"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data", ASYNC_SIGNALS=False)
    def test_import_3dtiles_overwrite(self):
        payload = {
            "url": "https://raw.githubusercontent.com/CesiumGS/3d-tiles-samples/main/1.1/TilesetWithFullMetadata/tileset.json",
            "title": "Remote Title",
            "type": "3dtiles",
            "action": "upload",
        }
        initial_name = "remote_title"
        assert_payload = {
            "subtype": "3dtiles",
            "title": "Remote Title",
            "resource_type": "dataset",
        }
        # Lets import the resource first but without deleting it
        resource = self._assertimport(
            payload,
            initial_name,
            skip_geoserver=True,
            keep_resource=True,
            assert_payload=assert_payload,
        )
        prev_timestamp = resource.last_updated
        # let's re-import it again with the overwrite mode activated
        assert_payload = {
            "subtype": "3dtiles",
            "resource_type": "dataset",
        }
        payload["overwrite_existing_layer"] = True
        self._assertimport(
            payload,
            initial_name,
            skip_geoserver=True,
            overwrite=True,
            assert_payload=assert_payload,
            last_update=prev_timestamp,
        )


class ImporterWMSImportTest(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data", "ASYNC_SIGNALS": "False"})
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data", ASYNC_SIGNALS=False)
    def test_import_wms(self):
        _, wms = WebMapService(
            "https://development.demo.geonode.org/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities"
        )
        resource_to_take = next(iter(wms.contents))
        res = wms[next(iter(wms.contents))]
        payload = {
            "url": "https://development.demo.geonode.org/geoserver/ows?service=WMS&version=1.3.0&request=GetCapabilities",
            "title": "Remote Title",
            "type": "wms",
            "lookup": resource_to_take,
            "parse_remote_metadata": True,
            "action": "upload",
        }
        initial_name = res.title.lower().replace(" ", "_")
        assert_payload = {
            "subtype": "remote",
            "title": res.title,
            "resource_type": "dataset",
            "sourcetype": "REMOTE",
            "ptype": "gxp_wmscsource",
        }
        self._assertimport(payload, initial_name, skip_geoserver=True, assert_payload=assert_payload)
