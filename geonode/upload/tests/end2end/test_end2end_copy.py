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
from django.http import QueryDict
import gisdata
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
from geonode.upload.tests.utils import TransactionImporterBaseTestSupport
from django.db import transaction
from django.forms.models import model_to_dict

geourl = settings.GEODATABASE_URL


class BaseClassEnd2End(TransactionImporterBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.valid_gkpg = f"{project_dir}/tests/fixture/valid.gpkg"
        cls.valid_geojson = f"{project_dir}/tests/fixture/valid.geojson"
        file_path = gisdata.PROJECT_ROOT
        filename = os.path.join(file_path, "both/good/sangis.org/Airport/Air_Runways.shp")
        cls.valid_shp = {
            "base_file": filename,
            "dbf_file": f"{file_path}/both/good/sangis.org/Airport/Air_Runways.dbf",
            "prj_file": f"{file_path}/both/good/sangis.org/Airport/Air_Runways.prj",
            "shx_file": f"{file_path}/both/good/sangis.org/Airport/Air_Runways.shx",
        }
        cls.url_create = reverse("importer_upload")
        ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]
        cls.valid_kml = f"{project_dir}/tests/fixture/valid.kml"
        cls.url_create = reverse("importer_upload")
        ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]

        _user, _password = ogc_server_settings.credentials

        cls.cat = Catalog(service_url=ogc_server_settings.rest, username=_user, password=_password)

    def setUp(self) -> None:
        for el in Dataset.objects.all():
            el.delete()

        self.admin = get_user_model().objects.get(username="admin")

    def tearDown(self) -> None:
        for el in Dataset.objects.all():
            el.delete()

    def _assertCloning(self, initial_name):
        # getting the geonode resource
        print(initial_name)
        dataset = Dataset.objects.get(alternate__icontains=f"geonode:{initial_name}")
        prev_dataset_count = Dataset.objects.count()
        self.client.force_login(get_user_model().objects.get(username="admin"))
        # creating the url and login
        _url = reverse("importer_resource_copy", args=[dataset.id])

        # defining the payload
        payload = QueryDict("", mutable=True)
        payload.update({"defaults": '{"title":"title_of_the_cloned_resource"}'})
        payload["action"] = "copy"

        # calling the endpoint
        response = self.client.put(_url, data=payload, content_type="application/json")
        self.assertEqual(200, response.status_code)
        self._wait_execution(response)

        # checking if a new resource is created
        self.assertEqual(prev_dataset_count + 1, Dataset.objects.count())

        # check if the geonode resource exists
        dataset = Dataset.objects.filter(title="title_of_the_cloned_resource")
        self.assertTrue(dataset.exists())
        dataset = dataset.first()
        # check if the dynamic model is created
        _schema_id = ModelSchema.objects.filter(name__icontains=dataset.alternate.split(":")[1])
        self.assertTrue(_schema_id.exists())
        schema_entity = _schema_id.first()
        self.assertTrue(FieldSchema.objects.filter(model_schema=schema_entity).exists())

        # Verify that ogr2ogr created the table with some data in it
        entries = ModelSchema.objects.filter(id=schema_entity.id).first()
        self.assertTrue(entries.as_model().objects.exists())

        # check if the resource is in geoserver
        resources = self.cat.get_resources()
        self.assertTrue(schema_entity.name in [y.name for y in resources])

    def _import_resource(self, payload, initial_name):
        payload["action"] = "upload"
        _url = reverse("importer_upload")
        self.client.force_login(get_user_model().objects.get(username="admin"))

        response = self.client.post(_url, data=payload)
        self.assertEqual(201, response.status_code)
        self._wait_execution(response)

    def _wait_execution(self, response, _id="execution_id"):
        # if is async, we must wait. It will wait for 1 min before raise exception
        if ast.literal_eval(os.getenv("ASYNC_SIGNALS", "False")):
            print("is false")
            tentative = 1
            while (
                ExecutionRequest.objects.get(exec_id=response.json().get(_id)) != ExecutionRequest.STATUS_FINISHED
                and tentative <= 6
            ):
                time.sleep(10)
                tentative += 1
        exc_obj = ExecutionRequest.objects.get(exec_id=response.json().get(_id))
        if exc_obj.status != ExecutionRequest.STATUS_FINISHED:
            print(ExecutionRequest.objects.get(exec_id=response.json().get(_id)))
            raise Exception(f"Async still in progress after 1 min of waiting: {model_to_dict(exc_obj)}")


class ImporterCopyEnd2EndGpkgTest(BaseClassEnd2End):
    @mock.patch.dict(
        os.environ,
        {
            "GEONODE_GEODATABASE": "test_geonode_data",
            "IMPORTER_ENABLE_DYN_MODELS": "True",
        },
    )
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_copy_dataset_from_geopackage(self):
        payload = {"base_file": open(self.valid_gkpg, "rb"), "action": "copy"}
        initial_name = "stazioni_metropolitana"
        # first we need to import a resource
        with transaction.atomic():
            self._import_resource(payload, initial_name)

            self._assertCloning(initial_name)


class ImporterCopyEnd2EndGeoJsonTest(BaseClassEnd2End):
    @mock.patch.dict(
        os.environ,
        {
            "GEONODE_GEODATABASE": "test_geonode_data",
            "IMPORTER_ENABLE_DYN_MODELS": "True",
        },
    )
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_copy_dataset_from_geojson(self):
        payload = {"base_file": open(self.valid_geojson, "rb"), "action": "copy"}
        initial_name = "valid"
        # first we need to import a resource
        with transaction.atomic():
            self._import_resource(payload, initial_name)
            self._assertCloning(initial_name)


class ImporterCopyEnd2EndShapeFileTest(BaseClassEnd2End):
    @mock.patch.dict(
        os.environ,
        {
            "GEONODE_GEODATABASE": "test_geonode_data",
            "IMPORTER_ENABLE_DYN_MODELS": "True",
        },
    )
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_copy_dataset_from_shapefile(self):
        payload = {_filename: open(_file, "rb") for _filename, _file in self.valid_shp.items()}
        payload["action"] = "copy"
        initial_name = "air_runways"
        # first we need to import a resource
        with transaction.atomic():
            self._import_resource(payload, initial_name)
            self._assertCloning(initial_name)


class ImporterCopyEnd2EndKMLTest(BaseClassEnd2End):
    @mock.patch.dict(
        os.environ,
        {
            "GEONODE_GEODATABASE": "test_geonode_data",
            "IMPORTER_ENABLE_DYN_MODELS": "True",
        },
    )
    @override_settings(GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data")
    def test_copy_dataset_from_kml(self):
        payload = {"base_file": open(self.valid_kml, "rb"), "action": "copy"}
        initial_name = "sample_point_dataset"
        # first we need to import a resource
        with transaction.atomic():
            self._import_resource(payload, initial_name)
            self._assertCloning(initial_name)
