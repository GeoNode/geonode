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
from geonode.upload.handlers.remote.flatgeobuf import RemoteFlatGeobufResourceHandler
from geonode.upload.orchestrator import orchestrator
from geonode.layers.models import Dataset, Attribute
from geonode.base.models import Link


class TestRemoteFlatGeobufResourceHandler(TestCase):
    databases = ("default", "datastore")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.handler = RemoteFlatGeobufResourceHandler()
        cls.valid_url = "http://example.com/test.fgb"
        cls.user, _ = get_user_model().objects.get_or_create(username="admin")
        cls.valid_payload = {
            "url": cls.valid_url,
            "type": "flatgeobuf",
            "title": "FlatGeobuf Test",
        }
        cls.owner = cls.user

    def test_can_handle_flatgeobuf(self):
        self.assertTrue(self.handler.can_handle(self.valid_payload))
        self.assertTrue(self.handler.can_handle({"url": "http://example.com/y.fgb", "type": "flatgeobuf"}))
        self.assertTrue(self.handler.can_handle({"url": "http://example.com/y.fgb", "type": "FlatGeobuf"}))
        self.assertFalse(self.handler.can_handle({"url": "http://example.com/y.jpg", "type": "image"}))

    @patch("geonode.upload.handlers.remote.flatgeobuf.requests.head")
    @patch("geonode.upload.handlers.remote.flatgeobuf.requests.get")
    @patch("geonode.upload.handlers.common.remote.requests.get")
    def test_is_valid_url_success(self, mock_base_get, mock_get, mock_head):
        mock_head.return_value.headers = {"Accept-Ranges": "bytes"}
        mock_head.return_value.status_code = 200
        mock_base_get.return_value.status_code = 200

        self.assertTrue(self.handler.is_valid_url(self.valid_url))

    @patch("geonode.upload.handlers.remote.flatgeobuf.requests.head")
    @patch("geonode.upload.handlers.remote.flatgeobuf.requests.get")
    @patch("geonode.upload.handlers.common.remote.requests.get")
    def test_is_valid_url_no_range_support(self, mock_base_get, mock_get, mock_head):
        mock_head.return_value.headers = {}
        mock_get.return_value.status_code = 404
        mock_base_get.return_value.status_code = 200

        with self.assertRaises(ImportException):
            self.handler.is_valid_url(self.valid_url)

    @patch("geonode.upload.handlers.remote.flatgeobuf.gdal.OpenEx")
    def test_create_geonode_resource(self, mock_ogr_openex):
        # Mock OGR dataset and layer
        mock_ds = MagicMock()
        mock_layer = MagicMock()
        mock_srs = MagicMock()
        mock_layer_defn = MagicMock()
        mock_field_defn = MagicMock()

        mock_srs.GetAuthorityName.return_value = "EPSG"
        mock_srs.GetAuthorityCode.return_value = "4326"
        mock_layer.GetSpatialRef.return_value = mock_srs

        mock_layer.GetExtent.return_value = [-180.0, 180.0, -90.0, 90.0]

        mock_field_defn.GetName.return_value = "test_field"
        mock_field_defn.GetTypeName.return_value = "String"
        mock_layer_defn.GetFieldCount.return_value = 1
        mock_layer_defn.GetFieldDefn.return_value = mock_field_defn
        mock_layer.GetLayerDefn.return_value = mock_layer_defn

        mock_ds.GetLayer.return_value = mock_layer
        mock_ogr_openex.return_value = mock_ds

        exec_id = orchestrator.create_execution_request(
            user=self.owner,
            func_name="funct1",
            step="step",
            input_params=self.valid_payload,
        )

        resource = self.handler.create_geonode_resource(
            "test_flatgeobuf",
            "test_flatgeobuf_alternate",
            execution_id=str(exec_id),
            resource_type=Dataset,
        )

        self.assertIsNotNone(resource)
        self.assertEqual(resource.subtype, "flatgeobuf")
        self.assertEqual(resource.alternate, "test_flatgeobuf_alternate")
        self.assertEqual(resource.srid, "EPSG:4326")
        self.assertIsNotNone(resource.bbox_polygon)

        link = Link.objects.get(resource=resource, link_type="data")
        self.assertEqual(link.url, self.valid_url)
        self.assertEqual(link.extension, "flatgeobuf")
        self.assertEqual(link.name, resource.alternate)

        # Verify Attribute metadata persistence
        attrs = Attribute.objects.filter(dataset=resource)
        self.assertTrue(attrs.filter(attribute="test_field").exists())
