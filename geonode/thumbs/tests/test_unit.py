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

import re
import uuid

from unittest.mock import patch, PropertyMock
from django.conf import settings

from geonode.thumbs import utils
from geonode.thumbs import thumbnails
from geonode.layers.models import Layer
from geonode.utils import DisableDjangoSignals
from geonode.maps.models import Map, MapLayer
from geonode.tests.base import GeoNodeBaseTestSupport, GeoNodeBaseSimpleTestSupport

FIXTURES_DIR = "geonode/thumbs/tests/fixtures/"


class ThumbnailsUtilsUnitTest(GeoNodeBaseSimpleTestSupport):

    def test_make_bbox_to_pixels_transf_same(self):

        src_bbox = [0, 0, 1, 1]
        dest_bbox = [0, 0, 1, 1]
        transf = utils.make_bbox_to_pixels_transf(src_bbox, dest_bbox)
        point = [0.5, 0.5]
        transformed = transf(*point)
        self.assertEqual(tuple(point), transformed, "Expected linear transformation to return the same coords.")

    def test_make_bbox_to_pixels_transf_diff(self):

        multiplication_factor = 10
        src_bbox = [0, 0, 1, 1]
        dest_bbox = [0, 0, multiplication_factor * src_bbox[2], multiplication_factor * src_bbox[3]]
        transf = utils.make_bbox_to_pixels_transf(src_bbox, dest_bbox)
        point = [0.5, 0.5]
        transformed = transf(*point)
        self.assertEqual(
            tuple(multiplication_factor * coord for coord in point),
            transformed,
            "Expected linear transformation to return multiplied coords.",
        )

    def test_expand_bbox_to_ratio(self):
        bbox = [623869.6556559108, 2458358.334500141, 4291621.974352865, 5270015.93640312, "EPSG:3857"]
        center = [(bbox[1] + bbox[0]) / 2, (bbox[3] + bbox[2]) / 2]

        width = 250
        height = 200

        new_bbox = utils.expand_bbox_to_ratio(bbox, target_height=height, target_width=width)

        # round to 4 decimal places in order to get rid of float rounding errors
        ratio = round(abs(new_bbox[3] - new_bbox[2]) / abs(new_bbox[1] - new_bbox[0]), 4)

        new_center = [(new_bbox[1] + new_bbox[0]) / 2, (new_bbox[3] + new_bbox[2]) / 2]

        self.assertEqual(height / width, ratio, "Expected ratio to be equal target ratio after transformation")
        self.assertEqual(center, new_center, "Expected center to be preserved after transformation")


class ThumbnailsUnitTest(GeoNodeBaseTestSupport):

    fixtures = GeoNodeBaseTestSupport.fixtures.copy() + [
        FIXTURES_DIR + filename
        for filename in [
            "resource_base.json",
            "upload_session.json",
            "service.json",
            "style.json",
            "layer.json",
            "map.json",
            "map_layer.json",
        ]
    ]

    re_uuid = "[0-F]{8}-([0-F]{4}-){3}[0-F]{12}"

    @classmethod
    def setUpClass(cls):
        # temporarily disconnect signals to load Service fixture
        with DisableDjangoSignals():
            super().setUpClass()

    def test_generate_thumbnail_name_layer(self):

        layer_name = thumbnails._generate_thumbnail_name(Layer.objects.first())
        self.assertIsNotNone(
            re.match(f"layer-{self.re_uuid}-thumb.png", layer_name, re.I), "Layer name should meet a provided pattern"
        )

    def test_get_unique_upload_path(self):

        layer = Layer.objects.first()
        thumbnail_name = thumbnails._generate_thumbnail_name(layer)
        upload_path = utils.thumb_path(thumbnail_name)
        new_upload_path = utils.get_unique_upload_path(layer, thumbnail_name)
        self.assertNotEqual(upload_path, new_upload_path)
        new_upload_path2 = utils.get_unique_upload_path(layer, thumbnail_name)
        self.assertNotEqual(new_upload_path, new_upload_path2)

    @patch("geonode.maps.models.Map.layers", new_callable=PropertyMock)
    def test_generate_thumbnail_name_map_empty(self, layers_mock):
        layers_mock.return_value = []

        map_name = thumbnails._generate_thumbnail_name(Map.objects.first())
        self.assertIsNone(map_name, "Map name for maps without layers should return None.")

    @patch("geonode.maps.models.Map.layers", new_callable=PropertyMock)
    @patch("geonode.maps.models.Map.uuid", new_callable=PropertyMock)
    def test_generate_thumbnail_name_map(self, uuid_mock, layers_mock):

        layers_mock.return_value = [MapLayer()]
        uuid_mock.return_value = str(uuid.uuid4())

        map_name = thumbnails._generate_thumbnail_name(Map.objects.first())
        self.assertIsNotNone(
            re.match(f"map-{self.re_uuid}-thumb.png", map_name, re.I), "Map name should meet a provided pattern"
        )

    def test_layers_locations_layer(self):
        layer = Layer.objects.get(title_en="theaters_nyc")

        locations, bbox = thumbnails._layers_locations(layer)

        self.assertFalse(bbox, "Expected BBOX not to be calculated")
        self.assertEqual(locations, [[settings.OGC_SERVER["default"]["LOCATION"], [layer.alternate], []]])

    def test_layers_locations_layer_default_bbox(self):
        expected_bbox = [-8238681.374829309, -8220320.783295829, 4969844.093033709, 4984363.884452854, "EPSG:3857"]
        layer = Layer.objects.get(title_en="theaters_nyc")

        locations, bbox = thumbnails._layers_locations(layer, compute_bbox=True)

        self.assertEqual(bbox[-1].upper(), "EPSG:3857", "Expected calculated BBOX CRS to be EPSG:3857")
        self.assertEqual(bbox, expected_bbox, "Expected calculated BBOX to match pre-converted one.")
        self.assertEqual(locations, [[settings.OGC_SERVER["default"]["LOCATION"], [layer.alternate], []]])

    def test_layers_locations_layer_bbox(self):
        layer = Layer.objects.get(title_en="theaters_nyc")

        locations, bbox = thumbnails._layers_locations(layer, compute_bbox=True, target_crs="EPSG:4326")

        self.assertEqual(bbox[0:4], layer.bbox[0:4], "Expected calculated BBOX to match layer's")
        self.assertEqual(bbox[-1].lower(), layer.bbox[-1].lower(), "Expected calculated BBOX's CRS to match layer's")
        self.assertEqual(locations, [[settings.OGC_SERVER["default"]["LOCATION"], [layer.alternate], []]])

    def test_layers_locations_simple_map(self):
        layer = Layer.objects.get(title_en="theaters_nyc")
        map = Map.objects.get(title_en="theaters_nyc_map")
        MapLayer(
            map=map,
            name="Meteorite_Landings_from_NASA_Open_Data_Portal1",
            stack_order=1,
            visibility=True,
            ows_url="https://maps.geo-solutions.it/geoserver/wms",
            layer_params="""{\"id\": 1, \"title\": \"Open Street Map\", \"style\": \"test_style\", \"type\": \"osm\", \"singleTile\": false, \"dimensions\": [], \"hideLoading\": false,
            \"handleClickOnLayer\": false, \"useForElevation\": false, \"hidden\": false, \"extraParams\": {\"msId\": \"mapnik__0\"}, \"wrapDateLine\": true, \"displayOutsideMaxExtent\": true}"""
        ).save()
        locations, bbox = thumbnails._layers_locations(map)

        self.assertFalse(bbox, "Expected BBOX not to be calculated")
        self.assertEqual(locations, [[settings.OGC_SERVER["default"]["LOCATION"], ["geonode:Meteorite_Landings_from_NASA_Open_Data_Portal1", layer.alternate], ["test_style"]]])

    def test_layers_locations_simple_map_default_bbox(self):
        expected_bbox = [-74.00933448096204, -73.84439803442388, 40.71125142832557, 40.8100474377091, "epsg:3857"]

        layer = Layer.objects.get(title_en="theaters_nyc")
        map = Map.objects.get(title_en="theaters_nyc_map")

        locations, bbox = thumbnails._layers_locations(map, compute_bbox=True)

        self.assertEqual(bbox[-1].upper(), "EPSG:3857", "Expected calculated BBOX CRS to be EPSG:3857")
        self.assertEqual(bbox, expected_bbox, "Expected calculated BBOX to match pre-converted one.")
        self.assertEqual(locations, [[settings.OGC_SERVER["default"]["LOCATION"], [layer.alternate], []]])

    def test_layers_locations_composition_map_default_bbox(self):
        expected_bbox = [-165.43333, 180.0, -85.06, 81.16667, 'EPSG:3857']
        expected_locations = [
            [
                settings.GEOSERVER_LOCATION,
                ["geonode:theaters_nyc", "geonode:Meteorite_Landings_from_NASA_Open_Data_Portal1"],
                []
            ],
            [
                "http://www502.regione.toscana.it/wmsraster/com.rt.wms.RTmap/wms",
                ["rt_geologia.dbg_risorse_minerarie"],
                []
            ]
        ]

        map = Map.objects.get(title_en="composition_map")
        locations, bbox = thumbnails._layers_locations(map, compute_bbox=True)

        self.assertEqual(bbox[-1].upper(), "EPSG:3857", "Expected calculated BBOX CRS to be EPSG:3857")
        self.assertEqual(bbox, expected_bbox, "Expected calculated BBOX to match pre-converted one.")
        self.assertEqual(locations, expected_locations, "Expected calculated locations to match pre-computed.")
