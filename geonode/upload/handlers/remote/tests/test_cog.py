#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from django.test import TestCase
from mock import MagicMock, patch
from geonode.upload.api.exceptions import ImportException
from django.contrib.auth import get_user_model
from geonode.upload.handlers.remote.cog import RemoteCOGResourceHandler
from geonode.upload.orchestrator import orchestrator
from geonode.layers.models import Dataset
from geonode.base.models import Link


class TestRemoteCOGResourceHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = RemoteCOGResourceHandler()
        cls.valid_url = "http://example.com/test.tif"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.valid_payload = {
            "url": cls.valid_url,
            "type": "cog",
            "title": "COG Test",
        }
        cls.owner = cls.user

    def test_can_handle_cog(self):
        self.assertTrue(self.handler.can_handle(self.valid_payload))
        self.assertTrue(self.handler.can_handle({"url": "http://example.com/y.tiff", "type": "cog"}))
        self.assertFalse(self.handler.can_handle({"url": "http://example.com/y.jpg", "type": "image"}))

    @patch("geonode.upload.handlers.remote.cog.requests.head")
    @patch("geonode.upload.handlers.remote.cog.requests.get")
    @patch("geonode.upload.handlers.common.remote.requests.get")
    def test_is_valid_url_success(self, mock_base_get, mock_get, mock_head):
        mock_head.return_value.headers = {"Accept-Ranges": "bytes"}
        mock_head.return_value.status_code = 200
        mock_base_get.return_value.status_code = 200

        self.assertTrue(self.handler.is_valid_url(self.valid_url))

    @patch("geonode.upload.handlers.remote.cog.requests.head")
    @patch("geonode.upload.handlers.remote.cog.requests.get")
    @patch("geonode.upload.handlers.common.remote.requests.get")
    def test_is_valid_url_no_range_support(self, mock_base_get, mock_get, mock_head):
        mock_head.return_value.headers = {}
        mock_get.return_value.status_code = 404  # Not 206
        mock_base_get.return_value.status_code = 200

        with self.assertRaises(ImportException):
            self.handler.is_valid_url(self.valid_url)

    @patch("geonode.upload.handlers.remote.cog.gdal.Open")
    def test_create_geonode_resource(self, mock_gdal_open):
        # Mock GDAL dataset
        mock_ds = MagicMock()
        mock_srs = MagicMock()
        mock_srs.GetAuthorityName.return_value = "EPSG"
        mock_srs.GetAuthorityCode.return_value = "4326"
        mock_ds.GetSpatialRef.return_value = mock_srs
        mock_ds.GetGeoTransform.return_value = [0, 1, 0, 0, 0, -1]
        mock_ds.RasterXSize = 100
        mock_ds.RasterYSize = 100
        mock_gdal_open.return_value = mock_ds

        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=self.valid_payload,
        )

        resource = self.handler.create_geonode_resource(
            "test_cog",
            "test_cog_alternate",
            execution_id=str(exec_id),
            resource_type=Dataset,
        )

        self.assertIsNotNone(resource)
        self.assertEqual(resource.subtype, "cog")
        self.assertEqual(resource.alternate, "test_cog_alternate")
        self.assertEqual(resource.srid, "EPSG:4326")
        self.assertIsNotNone(resource.bbox_polygon)

        # Verify Link creation (where URL is stored)
        link = Link.objects.get(resource=resource, link_type="data")
        self.assertEqual(link.url, self.valid_url)
        self.assertEqual(link.extension, "cog")
        self.assertEqual(link.name, resource.alternate)
