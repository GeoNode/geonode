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
from unittest import mock

from geonode.harvesting.harvesters import arcgis
from geonode.tests.base import GeoNodeBaseSimpleTestSupport


class ArcgisModuleTestCase(GeoNodeBaseSimpleTestSupport):
    def test_parse_spatial_extent_with_latest_wkid(self):
        raw_extent = {
            "xmin": 10,
            "ymin": 5,
            "xmax": 20,
            "ymax": 45,
            "spatialReference": {
                "wkid": 102100,
                "latestWkid": 3857,
            },
        }
        epsg_code, polygon = arcgis._parse_spatial_extent(raw_extent)
        self.assertEqual(epsg_code, "EPSG:3857")
        self.assertEqual(polygon.wkt, "POLYGON ((10 5, 10 45, 20 45, 20 5, 10 5))")

    def test_parse_spatial_extent_without_latest_wkid(self):
        raw_extent = {
            "xmin": 10,
            "ymin": 5,
            "xmax": 20,
            "ymax": 45,
            "spatialReference": {
                "wkid": 102100,
            },
        }
        epsg_code, polygon = arcgis._parse_spatial_extent(raw_extent)
        self.assertEqual(epsg_code, "EPSG:102100")
        self.assertEqual(polygon.wkt, "POLYGON ((10 5, 10 45, 20 45, 20 5, 10 5))")

    def test_parse_remote_url(self):
        fixtures = [
            ("https://fake/rest/services/myservice/MapServer", "https://fake/rest/services", "myservice", "MapServer"),
            (
                "https://fake/rest/services/myservice/MapServer/Query",
                "https://fake/rest/services",
                "myservice",
                "MapServer",
            ),
            ("https://fake/rest/services", "https://fake/rest/services", None, None),
            (
                "https://fake/rest/services/myservice/ImageServer",
                "https://fake/rest/services",
                "myservice",
                "ImageServer",
            ),
        ]
        for url, expected_cat_url, expected_service_name, expected_service_type in fixtures:
            cat_url, service_name, service_type = arcgis.parse_remote_url(url)
            self.assertEqual(cat_url, expected_cat_url)
            self.assertEqual(service_name, expected_service_name)
            self.assertEqual(service_type, expected_service_type)

    @mock.patch("geonode.harvesting.harvesters.arcgis.arcrest")
    def test_get_resource_extractor(self, mock_arcrest):
        fixtures = [
            (
                "http://somewhere/rest/services/fakeservice1/MapServer/1",
                mock_arcrest.MapService,
                arcgis.ArcgisMapServiceResourceExtractor,
            ),
            (
                "http://somewhere/rest/services/fakeservice1/ImageServer/1",
                mock_arcrest.ImageService,
                arcgis.ArcgisImageServiceResourceExtractor,
            ),
        ]
        for identifier, mock_class, extractor_class in fixtures:
            result = arcgis.get_resource_extractor(identifier)
            mock_class.assert_called_with(identifier)
            self.assertIsInstance(result, extractor_class)
