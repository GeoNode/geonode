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
import os
import re
import json
import logging
import tempfile
import requests
import timeout_decorator

from io import BytesIO
from datetime import datetime
from unittest.mock import MagicMock, call, patch
from owslib.map.wms111 import WebMapService_1_1_1
from PIL import UnidentifiedImageError, Image
from pixelmatch.contrib.PIL import pixelmatch

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test.utils import override_settings

from geonode import geoserver
from geonode.maps.models import Map, MapLayer
from geonode.utils import check_ogc_backend
from geonode.decorators import on_ogc_backend
from geonode.utils import http_client, DisableDjangoSignals
from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.thumbs.thumbnails import create_gs_thumbnail_geonode, create_thumbnail
from geonode.layers.models import Dataset
from geonode.thumbs.background import (
    OSMTileBackground,
    WikiMediaTileBackground,
    GenericXYZBackground,
    GenericWMSBackground,
)
from geonode.base.populate_test_data import all_public, create_models, remove_models, create_single_dataset
from geonode.resource.registry import resource_manager_registry, dataset_manager

logger = logging.getLogger(__name__)


LOCAL_TIMEOUT = 300
EXPECTED_RESULTS_DIR = "geonode/thumbs/tests/expected_results/"

TILE_URL_RE = re.compile(r"/(\d+)/(\d+)/(\d+)\.png$")

TILE_TEST_BBOXES_3857 = [
    [-8250483.072013094, -8221819.186406153, 4961221.562116772, 4985108.133455889, "EPSG:3857"],
    [-9990526.32372507, -6321548.96603661, 3335075.3607465066, 6392556.492153557, "EPSG:3857"],
    [-107776710.17911679, 9630565.26691392, -50681609.070756994, 47157787.134268604, "EPSG:3857"],
    [39681312.13711384, 43350289.494802296, 3596795.7455949546, 6654276.877002003, "EPSG:3857"],
]


# colours far enough apart to exceed pixelmatch's default threshold
TILE_PALETTE = [
    (220, 40, 40),
    (40, 170, 60),
    (40, 80, 220),
    (235, 205, 30),
    (200, 50, 200),
    (30, 200, 210),
    (245, 140, 20),
    (110, 50, 160),
]


def synthetic_tile_response(url, *args, **kwargs):
    """Mocked HttpClient.request returning a checkerboard tile coloured by its z/x/y."""
    z, x, y = (int(v) for v in TILE_URL_RE.search(url).groups())
    tile = Image.new("RGB", (256, 256), TILE_PALETTE[(x + 3 * y + 5 * z) % len(TILE_PALETTE)])
    for i in range(4):
        for j in range(4):
            if (i + j) % 2:
                tile.paste((20, 20, 20), (i * 64, j * 64, (i + 1) * 64, (j + 1) * 64))
    buf = BytesIO()
    tile.save(buf, format="PNG")
    return MagicMock(status_code=200), buf.getvalue()


class GeoNodeThumbnailTileBackground(GeoNodeBaseTestSupport):
    dataset_coast_line = None

    fixtures = ["initial_data.json", "group_test_data.json", "default_oauth_apps.json"]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        create_models(type=cls.get_type, integration=cls.get_integration)
        all_public()
        cls.user_admin = get_user_model().objects.get(username="admin")

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            cls.dataset_coast_line = create_single_dataset("san_andres_y_providencia_coastline")

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        remove_models(cls.get_obj_ids, type=cls.get_type, integration=cls.get_integration)

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "url": "http://some_fancy_url/{z}/{x}/{y}.png",
                "tile_size": 256,
            }
        }
    )
    @patch("geonode.thumbs.background.time")
    @patch.object(http_client, "request", return_value=(None, "Connection refused"))
    def test_tile_background_retries(self, request_mock, time_mock):
        max_retries = 3
        retry_delay = 1

        with self.assertRaises(requests.exceptions.RequestException):
            GenericXYZBackground(
                thumbnail_width=240, thumbnail_height=200, max_retries=max_retries, retry_delay=retry_delay
            ).fetch([623869.6556559108, 2458358.334500141, 4291621.974352865, 5270015.93640312, "EPSG:3857"])

        self.assertEqual(request_mock.call_count, max_retries, f"Expected {max_retries} failing fetches")
        time_mock.sleep.assert_has_calls([call(retry_delay)] * (max_retries - 1))

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "url": "http://some_fancy_url/{z}/{x}/{y}.png",
                "tile_size": 256,
            }
        }
    )
    @patch.object(http_client, "request")
    def test_tile_background_http_error_not_retried(self, request_mock):
        response = requests.Response()
        response.status_code = 429
        request_mock.return_value = (response, None)

        with self.assertRaises(requests.exceptions.HTTPError):
            GenericXYZBackground(thumbnail_width=240, thumbnail_height=200, max_retries=3).fetch(
                TILE_TEST_BBOXES_3857[0]
            )

        self.assertEqual(request_mock.call_count, 1)

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "url": "http://some_fancy_url/",
                "tile_size": 256,
            }
        }
    )
    def test_tile_background_bbox_conversions(self):
        bboxes_3857 = [
            [-8252241.123663656, -8223577.238056716, 4967814.255806367, 4983101.661463401],
            [-8972128.86948389, -7211019.73779343, 4554411.364647665, 5532805.32669792],
            [-1915008.1381942185, 5129428.388567626, -1125203.1711428363, 2788372.6770581882],
            [9669176.372480828, 16713612.899242673, 4035824.978672272, 7949400.826873297],
        ]

        for bbox_3857 in bboxes_3857:
            background = GenericXYZBackground(thumbnail_width=1, thumbnail_height=1)
            bbox4326 = background.bbox3857to4326(*bbox_3857)
            new_bbox_3857 = background.bbox4326to3857(*bbox4326)

            self.assertEqual(
                [round(coord, 4) for coord in bbox_3857],
                [round(coord, 4) for coord in new_bbox_3857],
                "Expected converted BBOXes to be equal",
            )

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "url": "http://some_fancy_url/",
                "tile_size": 256,
            }
        }
    )
    def test_tile_background_bbox_zoom_calculation(self):
        bboxes_3857 = [
            [-8252241.123663656, -8223577.238056716, 4967814.255806367, 4983101.661463401],
            [-8972128.86948389, -7211019.73779343, 4554411.364647665, 5532805.32669792],
            [-1915008.1381942185, 5129428.388567626, -1125203.1711428363, 2788372.6770581882],
            [9669176.372480828, 16713612.899242673, 4035824.978672272, 7949400.826873297],
        ]

        expected_zooms = [11, 4, 2, 2]

        background = GenericXYZBackground(thumbnail_width=1, thumbnail_height=1)

        for expected_zoom, bbox in zip(expected_zooms, bboxes_3857):
            bbox4326 = background.bbox3857to4326(*bbox)
            background._mercantile_bbox = [bbox4326[0], bbox4326[2], bbox4326[1], bbox4326[3]]

            zoom = background.calculate_zoom()

            self.assertEqual(zoom, expected_zoom, "Calculated zooms should be equal expected")

    def _assert_background_matches(self, image, expected_image_path, tolerance=0.01):
        expected_image = Image.open(expected_image_path)
        self.assertEqual(image.size, expected_image.size, f"Unexpected background size for {expected_image_path}")
        mismatch = pixelmatch(image, expected_image)
        self.assertLess(
            mismatch,
            expected_image.size[0] * expected_image.size[1] * tolerance,
            f"Background differs from {expected_image_path} by {mismatch} pixels",
        )

    def _assert_tiles_requested_from(self, request_mock, url_prefix):
        self.assertTrue(request_mock.call_count)
        for request_call in request_mock.call_args_list:
            self.assertTrue(request_call.args[0].startswith(url_prefix), request_call.args[0])

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "url": "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png",
                "tile_size": 256,
            }
        }
    )
    @patch.object(http_client, "request", side_effect=synthetic_tile_response)
    def test_tile_background_generic_fetch(self, request_mock):
        background = GenericXYZBackground(thumbnail_width=240, thumbnail_height=200)
        image = background.fetch(TILE_TEST_BBOXES_3857[0])

        self._assert_tiles_requested_from(request_mock, "https://maps.wikimedia.org/osm-intl/")
        self._assert_background_matches(image, f"{EXPECTED_RESULTS_DIR}background/xyz_outcome1.png")

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "url": "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png",
                "tile_size": 256,
            }
        }
    )
    @patch.object(http_client, "request", side_effect=synthetic_tile_response)
    def test_tile_background_generic_fetch_zoom(self, request_mock):
        background = GenericXYZBackground(thumbnail_width=500, thumbnail_height=200)

        for zoom in range(6, 13):
            request_mock.reset_mock()
            image = background.fetch(TILE_TEST_BBOXES_3857[0], zoom)

            for request_call in request_mock.call_args_list:
                self.assertIn(f"/osm-intl/{zoom}/", request_call.args[0])
            self._assert_background_matches(image, f"{EXPECTED_RESULTS_DIR}background/xyz_zoom_{zoom}_outcome.png")

    @patch.object(http_client, "request", side_effect=synthetic_tile_response)
    def test_tile_background_wikimedia_fetch(self, request_mock):
        background = WikiMediaTileBackground(thumbnail_width=240, thumbnail_height=200)

        for i, bbox in enumerate(TILE_TEST_BBOXES_3857, start=1):
            image = background.fetch(bbox)
            self._assert_background_matches(image, f"{EXPECTED_RESULTS_DIR}background/xyz_outcome{i}.png")

        self._assert_tiles_requested_from(request_mock, "https://maps.wikimedia.org/osm-intl/")

    @patch.object(http_client, "request", side_effect=synthetic_tile_response)
    def test_tile_background_osm_fetch(self, request_mock):
        background = OSMTileBackground(thumbnail_width=240, thumbnail_height=200)

        for i, bbox in enumerate(TILE_TEST_BBOXES_3857, start=1):
            image = background.fetch(bbox)
            self._assert_background_matches(image, f"{EXPECTED_RESULTS_DIR}background/xyz_outcome{i}.png")

        self._assert_tiles_requested_from(request_mock, "https://tile.openstreetmap.org/")

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "url": "http://maps.geosolutionsgroup.com/geoserver/gwc/service/tms/1.0.0/osm%3Aosm_simple_light@EPSG%3A900913@png/{z}/{x}/{y}.png",
                "tms": True,
            }
        }
    )
    @patch.object(http_client, "request", side_effect=synthetic_tile_response)
    def test_tile_background_tms_fetch(self, request_mock):
        background = GenericXYZBackground(thumbnail_width=240, thumbnail_height=200)

        # TMS flips the tile rows, so the same synthetic tiles compose a different image than XYZ
        for i, bbox in enumerate(TILE_TEST_BBOXES_3857, start=1):
            image = background.fetch(bbox)
            self._assert_background_matches(image, f"{EXPECTED_RESULTS_DIR}background/tms_outcome{i}.png")

        self._assert_tiles_requested_from(request_mock, "http://maps.geosolutionsgroup.com/geoserver/gwc/service/tms/")

    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "service_url": settings.OGC_SERVER["default"]["LOCATION"],
                "dataset_name": "san_andres_y_providencia_coastline_foo",
                "srid": "EPSG:3857",
                "version": "1.1.1",
            }
        }
    )
    @patch.object(WebMapService_1_1_1, "getmap")
    def test_wms_background_retries(self, request_mock):
        request_mock.return_value = None

        width = 240
        height = 200
        max_retries = 3
        retry_delay = 1
        bbox = [-9072563.021775628, -9043899.136168687, 1492394.0457582686, 1507681.4514153039, "EPSG:4326"]

        start = datetime.now()

        with self.assertRaises(UnidentifiedImageError):
            GenericWMSBackground(
                thumbnail_width=width, thumbnail_height=height, max_retries=max_retries, retry_delay=retry_delay
            ).fetch(bbox)

        end = datetime.now()

        if request_mock.call_count:
            self.assertEqual(
                request_mock.call_count, max_retries, f"Expected to {max_retries} number of failing fetches"
            )
            self.assertGreaterEqual(
                (end - start).seconds,
                max_retries * retry_delay - 1,
                "Expected delay between consecutive failing fetches",
            )

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "service_url": f"{settings.OGC_SERVER['default']['LOCATION']}ows/",
                "dataset_name": "san_andres_y_providencia_coastline",
                "srid": "EPSG:3857",
                "version": "1.1.1",
            }
        }
    )
    def test_wms_background_fetch_epsg3857(self):
        width = 240
        height = 200

        bbox = [-9072563.021775628, -9043899.136168687, 1492394.0457582686, 1507681.4514153039, "EPSG:3857"]

        try:
            image = GenericWMSBackground(thumbnail_width=width, thumbnail_height=height).fetch(bbox)
        except UnidentifiedImageError as e:
            logger.error(f"It was not possible to fetch the background: {e}")
            return

        expected_image = Image.open(f"{EXPECTED_RESULTS_DIR}background/wms_3857.png")
        diff = Image.new("RGB", image.size)

        mismatch = pixelmatch(image, expected_image, diff)
        if mismatch >= expected_image.size[0] * expected_image.size[1] * 0.01:
            logger.warn("Mismatch, it was not possible to bump the bg!")
            # Sometimes this test fails to fetch the OSM background
            with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                logger.error(f"Dumping image to: {tmpfile.name}")
                image.save(tmpfile)
                # Let's check that the thumb is valid at least
                with Image.open(tmpfile) as img:
                    img.verify()
            with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                logger.error(f"Dumping diff to: {tmpfile.name}")
                diff.save(tmpfile)
                # Let's check that the thumb is valid at least
                with Image.open(tmpfile) as img:
                    img.verify()
        else:
            self.assertTrue(
                mismatch < width * height * 0.01, "Expected test and pre-generated backgrounds to differ up to 1%"
            )

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @override_settings(
        THUMBNAIL_BACKGROUND={
            "options": {
                "service_url": f"{settings.OGC_SERVER['default']['LOCATION']}ows/",
                "dataset_name": "san_andres_y_providencia_coastline",
                "srid": "EPSG:4326",
                "version": "1.1.1",
            }
        }
    )
    def test_wms_background_fetch_epsg4326(self):
        width = 240
        height = 200

        bbox = [-9072563.021775628, -9043899.136168687, 1492394.0457582686, 1507681.4514153039, "EPSG:3857"]

        try:
            image = GenericWMSBackground(thumbnail_width=width, thumbnail_height=height).fetch(bbox)
        except UnidentifiedImageError as e:
            logger.error(f"It was not possible to fetch the background: {e}")
            return

        expected_image = Image.open(f"{EXPECTED_RESULTS_DIR}background/wms_4326.png")
        diff = Image.new("RGB", image.size)

        mismatch = pixelmatch(image, expected_image, diff)
        if mismatch >= expected_image.size[0] * expected_image.size[1] * 0.01:
            logger.warn("Mismatch, it was not possible to bump the bg!")
            # Sometimes this test fails to fetch the OSM background
            with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                logger.error(f"Dumping image to: {tmpfile.name}")
                image.save(tmpfile)
                # Let's check that the thumb is valid at least
                with Image.open(tmpfile) as img:
                    img.verify()
            with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                logger.error(f"Dumping diff to: {tmpfile.name}")
                diff.save(tmpfile)
                # Let's check that the thumb is valid at least
                with Image.open(tmpfile) as img:
                    img.verify()
        else:
            self.assertTrue(
                mismatch < width * height * 0.01, "Expected test and pre-generated backgrounds to differ up to 1%"
            )


class GeoNodeThumbnailsIntegration(GeoNodeBaseTestSupport):
    dataset_coast_line = None
    dataset_highway = None
    map_composition = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rm = resource_manager_registry
        cls.user_admin = get_user_model().objects.get(username="admin")

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            cls.dataset_coast_line = create_single_dataset("san_andres_y_providencia_coastline")
            cls.dataset_highway = create_single_dataset("san_andres_y_providencia_highway")

            # create a map from loaded layers
            admin_user = get_user_model().objects.get(username="admin")
            cls.map_composition = Map.objects.create(
                title="composition",
                abstract="abstract",
                owner=admin_user,
            )
            cls.map_composition.id
            MapLayer.objects.create(
                map=cls.map_composition,
                extra_params={},
                name="geonode:san_andres_y_providencia_coastline",
                store=None,
                current_style=None,
                ows_url=None,
                local=True,
            )
            MapLayer.objects.create(
                map=cls.map_composition,
                extra_params={},
                name="geonode:san_andres_y_providencia_highway",
                store=None,
                current_style=None,
                ows_url=None,
                local=True,
            )
            # update MapLayers to correctly show layers' location
            with DisableDjangoSignals():
                for maplayer in cls.map_composition.maplayers.iterator():
                    if maplayer.name in [cls.dataset_coast_line.alternate, cls.dataset_highway.alternate]:
                        maplayer.local = True
                        maplayer.save(force_update=True)
                        maplayer.refresh_from_db()

            cls.map_composition.refresh_from_db()

    def _fetch_thumb_and_compare(self, url, expected_image):
        if not url:
            logger.error(f"It was not possible to fetch the remote dataset WMS GetMap! thumb_url: {url}")
            return
        _, img = http_client.request(url)
        content = BytesIO(img)
        try:
            Image.open(content).verify()  # verify that it is, in fact an image
            thumb = Image.open(content)

            diff = Image.new("RGB", thumb.size)

            mismatch = pixelmatch(thumb, expected_image, diff)

            if mismatch >= expected_image.size[0] * expected_image.size[1] * 0.01:
                logger.warn("Mismatch, it was not possible to bump the bg!")
                # Sometimes this test fails to fetch the OSM background
                with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                    logger.error(f"Dumping thumb to: {tmpfile.name}")
                    thumb.save(tmpfile)
                    # Let's check that the thumb is valid at least
                    with Image.open(tmpfile) as img:
                        img.verify()
                with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                    logger.error(f"Dumping diff to: {tmpfile.name}")
                    diff.save(tmpfile)
                    # Let's check that the thumb is valid at least
                    with Image.open(tmpfile) as img:
                        img.verify()
            else:
                self.assertTrue(
                    mismatch < expected_image.size[0] * expected_image.size[1] * 0.01,
                    "Expected test and pre-generated thumbnails to differ up to 1%",
                )
        except UnidentifiedImageError as e:
            logger.error(e)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @override_settings(
        THUMBNAIL_BACKGROUND={
            "class": "geonode.thumbs.background.WikiMediaTileBackground",
        }
    )
    def test_dataset_default_thumb(self):
        expected_thumb = Image.open(f"{EXPECTED_RESULTS_DIR}thumbnails/default_dataset_coast_line_thumb.png")
        create_gs_thumbnail_geonode(self.dataset_coast_line, overwrite=True)
        self.dataset_coast_line.refresh_from_db()
        self._fetch_thumb_and_compare(self.dataset_coast_line.thumbnail_url, expected_thumb)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @override_settings(
        THUMBNAIL_BACKGROUND={
            "class": "geonode.thumbs.background.WikiMediaTileBackground",
        }
    )
    def test_dataset_custom_thumbs(self):
        bboxes = [
            [-9072629.904175375, -9043966.018568434, 1491839.8773032012, 1507127.2829602365, "EPSG:3857"],
            [-9701812.234583871, -8784567.895161757, 1183222.3819935687, 1672419.363018697, "EPSG:3857"],
            [-84665859.2306568, 32741416.215373922, -33346586.656875588, 29270626.9143408, "EPSG:3857"],
            [-72434308.4190976, -43082489.55758992, -7279981.1852046205, 8374322.207599477, "EPSG:3857"],
            [-77007211.63038959, -18303573.90737422, 781254.9545387309, 32089861.740146928, "EPSG:3857"],
        ]

        expected_results_dir = f"{EXPECTED_RESULTS_DIR}thumbnails/"
        expected_thumbs_paths = [
            f"{expected_results_dir}dataset_thumb1.png",
            f"{expected_results_dir}dataset_thumb2.png",
            f"{expected_results_dir}dataset_thumb3.png",
            f"{expected_results_dir}dataset_thumb4.png",
            f"{expected_results_dir}dataset_thumb5.png",
        ]

        self.client.login(username="norman", password="norman")
        dataset_id = Dataset.objects.get(alternate="geonode:san_andres_y_providencia_coastline").resourcebase_ptr_id
        thumbnail_post_url = reverse("base-resources-set-thumb-from-bbox", args=[dataset_id])

        for bbox, expected_thumb_path in zip(bboxes, expected_thumbs_paths):
            response = self.client.post(
                thumbnail_post_url, json.dumps({"bbox": bbox[0:4], "srid": bbox[-1]}), content_type="application/json"
            )

            if response.status_code != 200:
                logger.error(f"Expected 200 OK response from {thumbnail_post_url}")
            else:
                expected_thumb = Image.open(expected_thumb_path)

                self.dataset_coast_line.refresh_from_db()
                self._fetch_thumb_and_compare(self.dataset_coast_line.thumbnail_url, expected_thumb)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @override_settings(
        THUMBNAIL_BACKGROUND={
            "class": "geonode.thumbs.background.WikiMediaTileBackground",
        }
    )
    def test_map_default_thumb(self):
        create_gs_thumbnail_geonode(self.map_composition, overwrite=True)
        if not self.map_composition.has_thumbnail():
            logger.warn("It was not possible to dump the background!")
            logger.error(f"map_composition thumb: {self.map_composition.thumbnail_url}")
        else:
            _, img = http_client.request(self.map_composition.thumbnail_url)
            content = BytesIO(img)
            Image.open(content).verify()  # verify that it is, in fact an image
            thumb = Image.open(content)

            diff = Image.new("RGB", thumb.size)

            expected_thumb = Image.open(f"{EXPECTED_RESULTS_DIR}thumbnails/default_map_thumb.png")

            mismatch = pixelmatch(thumb, expected_thumb, diff)
            if mismatch >= expected_thumb.size[0] * expected_thumb.size[1] * 0.01:
                logger.warn("Mismatch, it was not possible to bump the bg!")
                # Sometimes this test fails to fetch the OSM background
                with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                    logger.error(f"Dumping thumb to: {tmpfile.name}")
                    thumb.save(tmpfile)
                    # Let's check that the thumb is valid at least
                    with Image.open(tmpfile) as img:
                        img.verify()
                with tempfile.NamedTemporaryFile(dir="/tmp", suffix=".png", delete=False) as tmpfile:
                    logger.error(f"Dumping diff to: {tmpfile.name}")
                    diff.save(tmpfile)
                    # Let's check that the thumb is valid at least
                    with Image.open(tmpfile) as img:
                        img.verify()
            else:
                self.assertTrue(
                    mismatch < expected_thumb.size[0] * expected_thumb.size[1] * 0.01,
                    "Expected test and pre-generated thumbnails to differ up to 1%",
                )

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @override_settings(
        THUMBNAIL_BACKGROUND={
            "class": "geonode.thumbs.background.WikiMediaTileBackground",
        }
    )
    def test_map_custom_thumbs(self):
        bboxes = [
            [-9072629.904175375, -9043966.018568434, 1491839.8773032012, 1507127.2829602365, "EPSG:3857"],
            [-9701812.234583871, -8784567.895161757, 1183222.3819935687, 1672419.363018697, "EPSG:3857"],
            [-84665859.2306568, 32741416.215373922, -33346586.656875588, 29270626.9143408, "EPSG:3857"],
            [-72434308.4190976, -43082489.55758992, -7279981.1852046205, 8374322.207599477, "EPSG:3857"],
            [-77007211.63038959, -18303573.90737422, 781254.9545387309, 32089861.740146928, "EPSG:3857"],
        ]

        expected_results_dir = f"{EXPECTED_RESULTS_DIR}thumbnails/"
        expected_thumbs_paths = [
            f"{expected_results_dir}map_thumb1.png",
            f"{expected_results_dir}map_thumb2.png",
            f"{expected_results_dir}map_thumb3.png",
            f"{expected_results_dir}map_thumb4.png",
            f"{expected_results_dir}map_thumb5.png",
        ]

        for bbox, expected_thumb_path in zip(bboxes, expected_thumbs_paths):
            create_thumbnail(self.map_composition, bbox=bbox, overwrite=True)

            expected_thumb = Image.open(expected_thumb_path)
            self.map_composition.refresh_from_db()

            self._fetch_thumb_and_compare(self.map_composition.thumbnail_url, expected_thumb)

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    @override_settings(
        THUMBNAIL_BACKGROUND={
            "class": "geonode.thumbs.background.WikiMediaTileBackground",
        }
    )
    def test_UTM_dataset_thumbnail(self):
        res = None
        try:
            dt_files = [os.path.join(os.path.abspath(os.path.dirname(__file__)), "data", "WY_USNG.zip")]
            # raises an exception if resource_type is not provided
            res = dataset_manager.create(
                None, resource_type=Dataset, defaults={"owner": self.user_admin, "files": dt_files}
            )
            # ingest with datasets
            if (
                res
            ):  # Since importing this dataset takes some time, the connection might be reset due to very low timeout set for testing.
                self.assertTrue(isinstance(res.get_real_instance(), Dataset))

                expected_results_dir = f"{EXPECTED_RESULTS_DIR}thumbnails/"
                expected_thumb_path = f"{expected_results_dir}WY_USNG_thumb.png"
                expected_thumb = Image.open(expected_thumb_path)
                self._fetch_thumb_and_compare(res.thumbnail_url, expected_thumb)
        finally:
            if res:
                dataset_manager.delete(res.uuid)
