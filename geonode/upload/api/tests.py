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
import io
import zipfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from geonode.layers.models import Dataset
from django.test import override_settings
from django.urls import reverse
from unittest.mock import MagicMock, patch

# Create your tests here.
from geonode.upload import project_dir
from geonode.base.populate_test_data import create_single_dataset
from django.http import HttpResponse, QueryDict

from geonode.upload.models import ResourceHandlerInfo
from geonode.upload.tests.utils import ImporterBaseTestSupport


def _build_gpkg_header():
    """
    Minimal 100-byte SQLite 3 / GeoPackage header, enough for libmagic to
    identify the buffer as 'SQLite 3.x database (OGC GeoPackage file)'.
    """
    hdr = b"SQLite format 3\x00"
    hdr += (0x1000).to_bytes(2, "big")  # page size
    hdr += b"\x01\x01"  # write / read format versions
    hdr += b"\x00"  # reserved space
    hdr += b"\x40\x20\x20"  # payload fraction fields
    hdr += (0).to_bytes(4, "big")  # file change counter
    hdr += (1).to_bytes(4, "big")  # database size in pages
    hdr += (0).to_bytes(4, "big")  # first freelist trunk
    hdr += (0).to_bytes(4, "big")  # total freelist pages
    hdr += (0).to_bytes(4, "big")  # schema cookie
    hdr += (4).to_bytes(4, "big")  # schema format
    hdr += (0).to_bytes(4, "big")  # default page cache size
    hdr += (0).to_bytes(4, "big")  # largest root b-tree page
    hdr += (1).to_bytes(4, "big")  # text encoding UTF-8
    hdr += (0).to_bytes(4, "big")  # user version
    hdr += (0).to_bytes(4, "big")  # incremental vacuum
    hdr += b"GPKG"  # application id (GeoPackage)
    hdr += b"\x00" * 20  # reserved
    hdr += (1).to_bytes(4, "big")  # version-valid-for
    hdr += (3039000).to_bytes(4, "big")  # sqlite version number
    assert len(hdr) == 100
    return hdr


GPKG_VALID_HEADER = _build_gpkg_header()
PE_LIKE_CONTENT = b"MZ" + b"\x00" * 58 + b"\x80\x00\x00\x00" + b"\x00" * 64 + b"PE\x00\x00" + b"\x4c\x01\x01\x00"


class TestImporterViewSet(ImporterBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse("importer_upload")
        cls.test_user = get_user_model().objects.create_user(
            username="test_user12", email="testuser@example.com", password="testpass123"
        )

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
        # FileValidationUploadHandler rejects the extension before the view runs.
        self.assertEqual(400, response.status_code)

    def test_importer_upload_rejects_disallowed_extension(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(name="malicious.exe", content=PE_LIKE_CONTENT),
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)
        self.assertFalse(Dataset.objects.filter(name="malicious").exists())

    def test_importer_upload_rejects_shapefile_with_mismatched_content(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(name="fake.shp", content=PE_LIKE_CONTENT),
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)
        self.assertFalse(Dataset.objects.filter(name="fake").exists())

    def test_importer_upload_rejects_gpkg_with_mismatched_content(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="fake.gpkg",
                content=b'{"type": "FeatureCollection", "content": "some-content"}',
            ),
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)
        self.assertFalse(Dataset.objects.filter(name="fake").exists())

    def test_importer_upload_rejects_geojson_with_binary_content(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(name="fake.geojson", content=PE_LIKE_CONTENT),
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)
        self.assertFalse(Dataset.objects.filter(name="fake").exists())

    def test_importer_upload_rejects_zip_with_path_traversal(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("../../etc/passwd", b"root:x:0:0")
        payload = {
            "base_file": SimpleUploadedFile(name="traversal.zip", content=buf.getvalue()),
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)
        self.assertIn(b"traversal", response.content)
        self.assertFalse(Dataset.objects.filter(name="traversal").exists())

    def test_importer_upload_rejects_zip_bomb(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            info = zipfile.ZipInfo("bomb.bin")
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, b"\x00" * (5 * 1024 * 1024))
        payload = {
            "base_file": SimpleUploadedFile(name="bomb.zip", content=buf.getvalue()),
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)
        self.assertIn(b"compression ratio", response.content)
        self.assertFalse(Dataset.objects.filter(name="bomb").exists())

    def test_gpkg_raise_error_with_invalid_payload(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        # Use a valid GeoPackage header so that FileValidationUploadHandler's
        # libmagic description check passes and the serializer reaches the
        # boolean validation that is being tested.
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.gpkg",
                content=GPKG_VALID_HEADER,
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

    @override_settings(REGISTERED_USERS_CAN_ADD_REMOTE_RESOURCES=False)
    @patch("geonode.upload.handlers.remote.cog.RemoteCOGResourceHandler.is_valid_url")
    @patch("geonode.upload.handlers.remote.cog.RemoteCOGResourceHandler.can_handle")
    @patch("geonode.upload.api.views.import_orchestrator.s")
    def test_remote_dataset_add_allowed_for_admin(
        self,
        mock_sig,
        mock_can_handle,
        mock_is_valid_url,
    ):
        mock_is_valid_url.return_value = True
        mock_can_handle.return_value = True

        self.client.force_login(get_user_model().objects.get(username="admin"))

        payload = {
            "url": "https://example.com/data.tif",
            "title": "Remote dataset",
            "type": "cog",
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)
        self.assertEqual(201, response.status_code)

    @override_settings(REGISTERED_USERS_CAN_ADD_REMOTE_RESOURCES=False)
    def test_remote_dataset_add_forbidden_for_regular_user_by_default(self):
        self.client.force_login(self.test_user)

        payload = {
            "url": "https://example.com/data.tif",
            "title": "Remote dataset denied",
            "type": "cog",
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)
        self.assertEqual(403, response.status_code)

    @patch("geonode.upload.api.views.import_orchestrator")
    def test_gpkg_task_is_called(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.gpkg",
                content=GPKG_VALID_HEADER,
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
    def test_geojson_mixed_geometry_succed(self, patch_upload):
        patch_upload.apply_async.side_effect = MagicMock()

        self.client.force_login(get_user_model().objects.get(username="admin"))
        payload = {
            "base_file": SimpleUploadedFile(
                name="test.geojson",
                content=b'{"type": "FeatureCollection", "features": '
                b'[{"type": "Feature", "properties": {}, "geometry": '
                b'{"type": "Point", "coordinates": [1, 2]}}, '
                b'{"type": "Feature", "properties": {}, "geometry": '
                b'{"type": "Polygon", "coordinates": '
                b"[[[1, 2], [1, 3], [2, 3], [2, 2], [1, 2]]]}}]}",
            ),
            "store_spatial_files": True,
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(201, response.status_code)

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

    @override_settings(SAFE_URL_CHECK_ENABLED=True)
    def test_remote_upload_rejects_unsafe_url(self):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        invalid_urls = [
            "http://127.0.0.1/tileset.json",
            "http://10.0.0.1/tileset.json",
            "http://192.168.1.10/tileset.json",
        ]

        for invalid_url in invalid_urls:
            with self.subTest(url=invalid_url):
                payload = {
                    "url": invalid_url,
                    "title": "Remote Title",
                    "type": "3dtiles",
                    "action": "upload",
                }

                response = self.client.post(self.url, data=payload)
                self.assertEqual(400, response.status_code)

    @patch("geonode.utils.socket.getaddrinfo")
    @override_settings(SAFE_URL_CHECK_ENABLED=True)
    def test_remote_upload_rejects_dns_resolving_to_private_ip(self, mock_dns):
        self.client.force_login(get_user_model().objects.get(username="admin"))
        mock_dns.return_value = [(None, None, None, None, ("127.0.0.1", 0))]

        payload = {
            "url": "http://example.com/tileset.json",
            "title": "Remote Title",
            "type": "3dtiles",
            "action": "upload",
        }

        response = self.client.post(self.url, data=payload)

        self.assertEqual(400, response.status_code)

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
