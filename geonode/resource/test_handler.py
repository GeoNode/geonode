#########################################################################
#
# Copyright (C) 2021 OSGeo
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


from django.urls import reverse
from geonode.assets.utils import get_default_asset
from geonode.base.populate_test_data import (
    create_single_dataset,
    create_single_doc,
    create_single_geoapp,
    create_single_map,
)
from geonode.documents.handlers import DocumentHandler
from geonode.geoapps.handlers import GeoAppHandler
from geonode.layers.handlers import DatasetHandler, Tiles3DHandler
from geonode.maps.handlers import MapHandler
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.resource.manager import resource_manager
from geonode.utils import build_absolute_uri


class TestResourceManager(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.dataset = create_single_dataset("dataset_for_handlers")
        cls.map = create_single_map("map_for_handlers")
        cls.document = create_single_doc("document_for_handlers")
        cls.geoapp = create_single_geoapp("geoapp_for_handlers")
        cls.tiles3d = create_single_dataset("tiles3d_for_handlers", with_asset=True)
        cls.tiles3d.subtype = "3dtiles"
        cls.tiles3d.save()

    def test_correct_resource_manager_is_called_for_dataset(self):
        handler = resource_manager.get_handler(self.dataset)
        self.assertIsNotNone(handler)
        self.assertTrue(isinstance(handler, DatasetHandler))

    def test_correct_resource_manager_is_called_for_doc(self):
        handler = resource_manager.get_handler(self.document)
        self.assertIsNotNone(handler)
        self.assertTrue(isinstance(handler, DocumentHandler))

    def test_correct_resource_manager_is_called_for_map(self):
        handler = resource_manager.get_handler(self.map)
        self.assertIsNotNone(handler)
        self.assertTrue(isinstance(handler, MapHandler))

    def test_correct_resource_manager_is_called_for_geoapp(self):
        handler = resource_manager.get_handler(self.geoapp)
        self.assertIsNotNone(handler)
        self.assertTrue(isinstance(handler, GeoAppHandler))

    def test_correct_resource_manager_is_called_for_3dtiles(self):
        handler = resource_manager.get_handler(self.tiles3d)
        self.assertIsNotNone(handler)
        self.assertTrue(isinstance(handler, Tiles3DHandler))

    def test_correct_download_url_for_dataset(self):
        handler = resource_manager.get_handler(self.dataset)
        self.assertIsNotNone(handler)

        expected_payload = [{"url": self.dataset.download_url, "ajax_safe": True, "default": True}]

        self.assertListEqual(handler.download_urls(), expected_payload)

    def test_correct_download_url_for_doc(self):
        handler = resource_manager.get_handler(self.document)
        self.assertIsNotNone(handler)
        expected_payload = [{"url": self.document.download_url, "ajax_safe": True}]

        self.assertListEqual(handler.download_urls(), expected_payload)

    def test_correct_download_url_for_map(self):
        handler = resource_manager.get_handler(self.map)
        expected_payload = []

        self.assertListEqual(handler.download_urls(), expected_payload)

    def test_correct_download_url_for_geoapp(self):
        handler = resource_manager.get_handler(self.geoapp)
        self.assertIsNotNone(handler)
        expected_payload = []
        self.assertListEqual(handler.download_urls(), expected_payload)

    def test_correct_download_url_for_3dtiles(self):
        handler = resource_manager.get_handler(self.tiles3d)
        asset = get_default_asset(self.tiles3d)
        self.assertIsNotNone(handler)
        expected_payload = [
            {
                "url": build_absolute_uri(reverse("assets-download", kwargs={"pk": asset.pk})),
                "ajax_safe": True,
                "default": True,
            }
        ]

        self.assertListEqual(handler.download_urls(), expected_payload)
