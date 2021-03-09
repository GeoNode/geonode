from geonode.tests.base import GeoNodeLiveTestSupport, GeoNodeBaseSimpleTestSupport

import timeout_decorator

import os
import time
import gisdata
import logging
from lxml import etree
from defusedxml import lxml as dlxml
from urllib.request import urlopen, Request
from urllib.parse import urljoin

from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model

from geonode import geoserver
from geonode.layers.models import Layer
from geonode.compat import ensure_string
from geonode.tests.utils import check_layer
from geonode.utils import check_ogc_backend
from geonode.layers.utils import file_upload
from geonode.decorators import on_ogc_backend
from geonode.base.models import TopicCategory, Link
from geonode.geoserver.helpers import set_attributes_from_geoserver
from geonode.utils import HttpClient
from geonode.thumbs.background import OSMTileBackground, WikiMediaTileBackground, GenericXYZBackground, GenericWMSBackground
from geonode.thumbs.thumbnails import create_gs_thumbnail_geonode, _generate_thumbnail_name
from geonode.base.thumb_utils import thumb_path
from unittest.mock import patch
from PIL import UnidentifiedImageError, Image
from datetime import datetime
from pixelmatch.contrib.PIL import pixelmatch

LOCAL_TIMEOUT = 300


class GeoNodeThumbnailTileBackground(GeoNodeBaseSimpleTestSupport):

    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'url': 'http://some_fancy_url/',
            'tile_size': 256,
        }
    })
    @patch.object(HttpClient, 'request')
    def test_tile_background_retries(self, request_mock):
        request_mock.return_value = (None, None)

        width = 240
        height = 200
        max_retries = 3
        retry_delay = 1

        start = datetime.now()

        with self.assertRaises(UnidentifiedImageError):

            GenericXYZBackground(
                thumbnail_width=width, thumbnail_height=height, max_retries=max_retries, retry_delay=retry_delay
            ).fetch([623869.6556559108, 2458358.334500141, 4291621.974352865, 5270015.93640312, 'EPSG:3857'])

        end = datetime.now()

        self.assertEqual(request_mock.call_count, max_retries, f"Expected to {max_retries} number of failing fetches")
        self.assertGreaterEqual((end-start).seconds, max_retries*retry_delay-1, "Expected delay between consecutive failing fetches")

    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'url': 'http://some_fancy_url/',
            'tile_size': 256,
        }
    })
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
                [round(coord, 4) for coord in bbox_3857], [round(coord, 4) for coord in new_bbox_3857],
                "Expected converted BBOXes to be equal"
            )

    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'url': 'http://some_fancy_url/',
            'tile_size': 256,
        }
    })
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

    def _fetch_and_compare_background(self, generator, bbox_3857, expected_image_path, zoom=None):
        image = generator.fetch(bbox_3857, zoom)
        expected_image = Image.open(expected_image_path)
        diff = Image.new("RGB", image.size)

        mismatch = pixelmatch(image, expected_image, diff)
        self.assertEqual(mismatch, 0, "Expected test and pre-generated backgrounds to be identical")

    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'url': 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png',
            'tile_size': 256,
        }
    })
    def test_tile_background_generic_fetch(self):

        width = 240
        height = 200

        bbox_3857 = [-8250483.072013094, -8221819.186406153, 4961221.562116772, 4985108.133455889, 'EPSG:3857']
        expected_image_path = 'geonode/thumbs/tests/expected_results/background/wikimedia_outcome1.png'

        background = GenericXYZBackground(thumbnail_width=width, thumbnail_height=height)
        self._fetch_and_compare_background(background, bbox_3857, expected_image_path)

    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'url': 'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png',
            'tile_size': 256,
        }
    })
    def test_tile_background_generic_fetch_zoom(self):

        width = 240
        height = 200

        bbox_3857 = [-8250483.072013094, -8221819.186406153, 4961221.562116772, 4985108.133455889, 'EPSG:3857']

        zooms = range(6, 13)
        expected_image_paths = [
            f'geonode/thumbs/tests/expected_results/background/wikimedia_zoom_{zoom}_outcome.png' for zoom in zooms
        ]

        background = GenericXYZBackground(thumbnail_width=width, thumbnail_height=height)

        for zoom, expected_image_path in zip(zooms, expected_image_paths):
            image = background.fetch(bbox_3857, zoom)
            expected_image = Image.open(expected_image_path)
            diff = Image.new("RGB", image.size)

            mismatch = pixelmatch(image, expected_image, diff)
            self.assertEqual(mismatch, 0, "Expected test and pre-generated backgrounds to be identical")

    def test_tile_background_wikimedia_fetch(self):

        width = 240
        height = 200

        bboxes_3857 = [
            [-8250483.072013094, -8221819.186406153, 4961221.562116772, 4985108.133455889, 'EPSG:3857'],
            [-9990526.32372507, -6321548.96603661, 3335075.3607465066, 6392556.492153557, 'EPSG:3857'],
            [-107776710.17911679, 9630565.26691392, -50681609.070756994, 47157787.134268604, 'EPSG:3857'],
            [39681312.13711384, 43350289.494802296, 3596795.7455949546, 6654276.877002003, 'EPSG:3857']
        ]

        expected_results_dir = 'geonode/thumbs/tests/expected_results/background/'
        expected_images_paths = [
            expected_results_dir + 'wikimedia_outcome1.png',
            expected_results_dir + 'wikimedia_outcome2.png',
            expected_results_dir + 'wikimedia_outcome3.png',
            expected_results_dir + 'wikimedia_outcome4.png',
        ]

        background = WikiMediaTileBackground(thumbnail_width=width, thumbnail_height=height)

        for bbox, expected_image_path in zip(bboxes_3857, expected_images_paths):
            self._fetch_and_compare_background(background, bbox, expected_image_path)

    def test_tile_background_osm_fetch(self):

        width = 240
        height = 200

        bboxes_3857 = [
            [-8250483.072013094, -8221819.186406153, 4961221.562116772, 4985108.133455889, 'EPSG:3857'],
            [-9990526.32372507, -6321548.96603661, 3335075.3607465066, 6392556.492153557, 'EPSG:3857'],
            [-107776710.17911679, 9630565.26691392, -50681609.070756994, 47157787.134268604, 'EPSG:3857'],
            [39681312.13711384, 43350289.494802296, 3596795.7455949546, 6654276.877002003, 'EPSG:3857']
        ]

        expected_results_dir = 'geonode/thumbs/tests/expected_results/background/'
        expected_images_paths = [
            expected_results_dir + 'osm_outcome1.png',
            expected_results_dir + 'osm_outcome2.png',
            expected_results_dir + 'osm_outcome3.png',
            expected_results_dir + 'osm_outcome4.png',
        ]

        background = OSMTileBackground(thumbnail_width=width, thumbnail_height=height)

        for bbox, expected_image_path in zip(bboxes_3857, expected_images_paths):
            self._fetch_and_compare_background(background, bbox, expected_image_path)


class GeoNodeThumbnailWMSBackground(GeoNodeLiveTestSupport):

    layer_coast_line = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # upload shape files
            shp_file = os.path.join(
                gisdata.VECTOR_DATA,
                'san_andres_y_providencia_coastline.shp')
            cls.layer_coast_line = file_upload(shp_file)

    @classmethod
    def tearDownClass(cls):
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            if cls.layer_coast_line:
                cls.layer_coast_line.delete()

        super().tearDownClass()

    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'service_url': settings.OGC_SERVER["default"]["LOCATION"],
            'layer_name': 'san_andres_y_providencia_coastline',
            'srid': 'EPSG:3857',
        }
    })
    @patch.object(HttpClient, 'request')
    def test_wms_background_retries(self, request_mock):
        request_mock.return_value = (None, None)

        width = 240
        height = 200
        max_retries = 3
        retry_delay = 1
        bbox = [-9072563.021775628, -9043899.136168687, 1492394.0457582686, 1507681.4514153039, 'EPSG:4326']

        start = datetime.now()

        with self.assertRaises(UnidentifiedImageError):

            GenericWMSBackground(
                thumbnail_width=width, thumbnail_height=height, max_retries=max_retries, retry_delay=retry_delay
            ).fetch(bbox)

        end = datetime.now()

        self.assertEqual(request_mock.call_count, max_retries, f"Expected to {max_retries} number of failing fetches")
        self.assertGreaterEqual((end-start).seconds, max_retries*retry_delay-1, "Expected delay between consecutive failing fetches")

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'service_url': settings.OGC_SERVER["default"]["LOCATION"] + 'ows/',
            'layer_name': 'san_andres_y_providencia_coastline',
            'srid': 'EPSG:3857',
            'version': '1.1.0',
        }
    })
    def test_wms_background_fetch_epsg3857(self):
        width = 240
        height = 200

        bbox = [-9072563.021775628, -9043899.136168687, 1492394.0457582686, 1507681.4514153039, 'EPSG:3857']

        image = GenericWMSBackground(
            thumbnail_width=width, thumbnail_height=height
        ).fetch(bbox)

        expected_image = Image.open('geonode/thumbs/tests/expected_results/background/wms_3857.png')
        diff = Image.new("RGB", image.size)

        mismatch = pixelmatch(image, expected_image, diff)
        self.assertEqual(mismatch, 0, "Expected test and pre-generated backgrounds to be identical")

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @override_settings(THUMBNAIL_BACKGROUND={
        'options': {
            'service_url': settings.OGC_SERVER["default"]["LOCATION"] + 'ows/',
            'layer_name': 'san_andres_y_providencia_coastline',
            'srid': 'EPSG:4326',
            'version': '1.1.0',
        }
    })
    def test_wms_background_fetch_epsg4326(self):
        width = 240
        height = 200

        bbox = [-9072563.021775628, -9043899.136168687, 1492394.0457582686, 1507681.4514153039, 'EPSG:3857']

        image = GenericWMSBackground(
            thumbnail_width=width, thumbnail_height=height
        ).fetch(bbox)

        expected_image = Image.open('geonode/thumbs/tests/expected_results/background/wms_4326.png')
        diff = Image.new("RGB", image.size)

        mismatch = pixelmatch(image, expected_image, diff)
        self.assertEqual(mismatch, 0, "Expected test and pre-generated backgrounds to be identical")


class GeoNodeThumbnailsIntegration(GeoNodeLiveTestSupport):

    layer_coast_line = None
    layer_highway = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # upload shape files
            shp_file = os.path.join(
                gisdata.VECTOR_DATA,
                'san_andres_y_providencia_coastline.shp')
            cls.layer_coast_line = file_upload(shp_file)

            shp_file = os.path.join(
                gisdata.VECTOR_DATA,
                'san_andres_y_providencia_highway.shp')
            cls.layer_highway = file_upload(shp_file)

    @classmethod
    def tearDownClass(cls):
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            if cls.layer_coast_line:
                cls.layer_coast_line.delete()
            if cls.layer_highway:
                cls.layer_highway.delete()

        super().tearDownClass()

    @on_ogc_backend(geoserver.BACKEND_PACKAGE)
    @timeout_decorator.timeout(LOCAL_TIMEOUT)
    def test_layer_default_thumb(self):
        create_gs_thumbnail_geonode(self.layer_coast_line)
        self.assertTrue(self.layer_coast_line.has_thumbnail())

        self.client.get(self.layer_coast_line.thumbnail_url)
        thumb = Image.open(thumb_path(_generate_thumbnail_name(self.layer_coast_line)))

        expected_thumb = Image.open('geonode/thumbs/tests/expected_results/thumbnails/default_layer_coast_line_thumb.png')
        diff = Image.new("RGB", thumb.size)

        mismatch = pixelmatch(thumb, expected_thumb, diff)
        self.assertEqual(mismatch, 0, "Expected test and pre-generated thumbnails to be identical")
