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
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from geonode.layers.models import Dataset
from django.urls import reverse
from unittest.mock import MagicMock, patch

# Create your tests here.
from geonode.upload import project_dir
from geonode.base.populate_test_data import create_single_dataset
from django.http import HttpResponse, QueryDict

from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.tests.utils import ImporterBaseTestSupport
from geonode.upload.orchestrator import orchestrator
from django.utils.module_loading import import_string
from geonode.assets.models import LocalAsset


class TestImporterViewSet(ImporterBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("importer_upload")

    def setUp(self):
        self.dataset = create_single_dataset(name="test_dataset_copy")
        self.copy_url = reverse("importer_resource_copy", args=[self.dataset.id])

    def tearDown(self):
        Dataset.objects.filter(name="test_dataset_copy").delete()

    def test_upload_method_not_allowed(self):
        self.client.login(username="admin", password="admin")

        response = self.client.get(self.url)
        self.assertEqual(405, response.status_code)

        response = self.client.put(self.url)
        self.assertEqual(405, response.status_code)

        response = self.client.patch(self.url)
        self.assertEqual(405, response.status_code)

    def test_raise_exception_if_file_is_not_a_handled(self):

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {"base_file": SimpleUploadedFile(name="file.invalid", content=b"abc"), "action": "upload"}
        response = self.client.post(self.url, data=payload)
        self.assertEqual(500, response.status_code)

    def test_gpkg_raise_error_with_invalid_payload(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.gpkg",
                content=b'{"type": "FeatureCollection", "content": "some-content"}',
            ),
            "store_spatial_files": "invalid",
            "action": "upload",
        }
        expected = {
            "success": False,
            "errors": ["Must be a valid boolean."],
            "code": "invalid",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)
        self.assertEqual(expected, response.json())

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_gpkg_task_is_called(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.gpkg",
                content=b'{"type": "FeatureCollection", "content": "some-content"}',
            ),
            "store_spatial_files": True,
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(201, response.status_code)

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_geojson_task_is_called(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.geojson",
                content=b'{"type": "FeatureCollection", "content": "some-content"}',
            ),
            "store_spatial_files": True,
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(201, response.status_code)

        self.assertTrue(201, response.status_code)

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_zip_file_is_unzip_and_the_handler_is_found(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": open(f"{project_dir}/tests/fixture/valid.zip", "rb"),
            "zip_file": open(f"{project_dir}/tests/fixture/valid.zip", "rb"),
            "store_spatial_files": True,
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(201, response.status_code)

    def test_copy_method_not_allowed(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))

        response = self.client.get(self.copy_url)
        self.assertEqual(405, response.status_code)

        response = self.client.post(self.copy_url)
        self.assertEqual(405, response.status_code)

        response = self.client.patch(self.copy_url)
        self.assertEqual(405, response.status_code)

    @patch("geonode.upload.api.views.import_orchestrator")
    @patch("geonode.upload.api.views.ResourceBaseViewSet.resource_service_copy")
    def test_redirect_to_old_upload_if_file_handler_is_not_set(self, copy_view, _orc):
        copy_view.return_value = HttpResponse()
        self.client.force_login(get_user_model().objects.get(username="admin"))

        response = self.client.put(self.copy_url)

        self.assertEqual(200, response.status_code)
        _orc.assert_not_called()
        copy_view.assert_called_once()

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_copy_ther_resource_if_file_handler_is_set(self, _orc):
        user = get_user_model().objects.get(username="admin")
        user.is_superuser = True
        user.save()
        self.client.force_login(get_user_model().objects.get(username="admin"))
        ResourceHandlerInfo.objects.create(
            resource=self.dataset,
            handler_module_path="geonode.upload.handlers.gpkg.handler.GPKGFileHandler",
        )
        payload = QueryDict("", mutable=True)
        payload.update({"defaults": '{"title":"stili_di_vita_4scenari"}'})
        response = self.client.put(self.copy_url, data=payload, content_type="application/json")

        self.assertEqual(200, response.status_code)
        _orc.s.assert_called_once()

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_asset_is_created_before_the_import_start(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.geojson",
                content=b'{"type": "FeatureCollection", "content": "some-content"}',
            ),
            "store_spatial_files": True,
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(201, response.status_code)

        self.assertTrue(201, response.status_code)

        _exec = orchestrator.get_execution_object(response.json()["execution_id"])

        asset_handler = import_string(_exec.input_params["asset_module_path"])
        self.assertTrue(asset_handler.objects.filter(id=_exec.input_params["asset_id"]))

        asset_handler.objects.filter(id=_exec.input_params["asset_id"]).delete()

    @patch("geonode.upload.api.views.import_orchestrator")
    @patch("geonode.upload.api.views.UploadLimitValidator.validate_parallelism_limit_per_user")
    def test_asset_should_be_deleted_if_created_during_with_exception(
        self, validate_parallelism_limit_per_user, patch_upload
    ):
        patch_upload.apply_async.s.side_effect = MagicMock()
        validate_parallelism_limit_per_user.side_effect = Exception("random exception")

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.geojson",
                content=b'{"type": "FeatureCollection", "content": "some-content"}',
            ),
            "store_spatial_files": True,
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(500, response.status_code)
        self.assertFalse(LocalAsset.objects.exists())
