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
from django.db.models import Q
from geonode.base.models import ResourceBase
import logging
from django.forms.models import model_to_dict

logger = logging.getLogger()
geourl = settings.GEODATABASE_URL


@override_settings(
    FILE_UPLOAD_DIRECTORY_PERMISSIONS=0o777,
    FILE_UPLOAD_PERMISSIONS=0o7777,
    IMPORTER_ENABLE_DYN_MODELS=True,
    ASYNC_SIGNAL=False,
)
class BaseImporterEndToEndTest(ImporterBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = get_user_model().objects.exclude(username="Anonymous").first()
        cls.original = {
            "base_file": f"{project_dir}/tests/fixture/upsert/original.shp",
            "dbf_file": f"{project_dir}/tests/fixture/upsert/original.dbf",
            "prj_file": f"{project_dir}/tests/fixture/upsert/original.prj",
            "shx_file": f"{project_dir}/tests/fixture/upsert/original.shx",
        }
        cls.upsert_shp = {
            "base_file": f"{project_dir}/tests/fixture/upsert/upsert.shp",
            "dbf_file": f"{project_dir}/tests/fixture/upsert/upsert.dbf",
            "prj_file": f"{project_dir}/tests/fixture/upsert/upsert.prj",
            "shx_file": f"{project_dir}/tests/fixture/upsert/upsert.shx",
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
                    continue
        try:
            ResourceBase.objects.filter(alternate__icontains=name).delete()
        except Exception as e:  # noqa
            pass

        try:
            ModelSchema.objects.filter(name__icontains=name.lower().replace(" ", "_")).delete()
        except Exception as e:  # noqa
            pass

    def _assertimport(
        self,
        payload,
        initial_name,
        last_update=None,
        skip_geoserver=False,
        assert_payload=None,
        keep_resource=False,
        upsert=True,
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

            _schema_id = ModelSchema.objects.filter(name__icontains=initial_name.lower().replace(" ", "_"))
            self.assertTrue(_schema_id.exists())
            schema_entity = _schema_id.first()
            self.assertTrue(FieldSchema.objects.filter(model_schema=schema_entity).exists())

            # Verify that ogr2ogr created the table with some data in it
            entries = ModelSchema.objects.filter(id=schema_entity.id).first()
            self.assertTrue(entries.as_model().objects.exists())

            entries.as_model().objects.all()

            # check if the geonode resource exists
            resource = ResourceBase.objects.filter(
                Q(alternate__icontains=f"geonode:{initial_name.lower().replace(' ', '_')}")
                | Q(alternate__icontains=initial_name.lower().replace(" ", "_"))
            )
            self.assertTrue(resource.exists())

            if not skip_geoserver:
                resources = self.cat.get_resources()
                # check if the resource is in geoserver
                self.assertTrue(resource.first().title in res for res in [y.name for y in resources])

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

        except Exception as e:
            raise e
        finally:
            if not keep_resource:
                resource = ResourceBase.objects.filter(
                    Q(alternate__icontains=f"geonode:{initial_name}") | Q(alternate__icontains=initial_name)
                )
                resource.delete()


class ImporterShapefileImportTestUpsert(BaseImporterEndToEndTest):
    @mock.patch.dict(os.environ, {"GEONODE_GEODATABASE": "test_geonode_data"})
    @override_settings(
        GEODATABASE_URL=f"{geourl.split('/geonode_data')[0]}/test_geonode_data", IMPORTER_ENABLE_DYN_MODELS=True
    )
    def test_import_shapefile_upsert(self):

        self._cleanup_layers(name="original")
        payload = {_filename: open(_file, "rb") for _filename, _file in self.original.items()}
        payload["action"] = "upload"
        initial_name = "original"
        prev_dataset = self._assertimport(payload, initial_name, keep_resource=True)
        payload = {_filename: open(_file, "rb") for _filename, _file in self.upsert_shp.items()}
        payload["resource_pk"] = prev_dataset.pk
        payload["action"] = "upsert"
        payload["upsert_key"] = "unique"

        # time to upsert the data
        self.client.force_login(self.admin)

        response = self.client.post(self.url, data=payload)
        # evaluating entries if are upserted
        self.assertEqual(response.status_code, 201)
        output = ExecutionRequest.objects.get(exec_id=response.json().get("execution_id")).output_params

        self.assertTrue(output.get("upsert")[0])
        data = output.get("upsert")[1]
        expected = {
            "data": {
                "error": {"create": 0, "update": 0},
                "total": {"error": 0, "success": 2},
                "success": {"create": 1, "update": 1},
            },
            "errors": {"create": [], "update": []},
        }
        self.assertDictEqual(expected, data)
