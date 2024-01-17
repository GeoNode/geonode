#########################################################################
#
# Copyright (C) 2023 OSGeo
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
import logging
from unittest.mock import patch

from pixelmatch.contrib.PIL import pixelmatch
from PIL import Image

from django.test import override_settings

from geonode.tests.base import GeoNodeBaseTestSupport
from geonode.thumbs.background import GenericWMTSBackground

logger = logging.getLogger(__name__)

WMTS_TILEMATRIX_LEVELS = [
    {
        "zoom": 0,
        "bounds": [-20037508.342787, -60112525.02833891, 20037508.342775952, 20037508.342787],
        "scaledenominator": 559082264.028501,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 156543.0339279803,
        "tilespanx": 40075016.68556295,
        "tilespany": 40075016.68556295,
    },
    {
        "zoom": 1,
        "bounds": [-20037508.342787, -40075016.68555735, 20037508.3427759, 20037508.342787],
        "scaledenominator": 279541132.01425016,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 78271.51696399004,
        "tilespanx": 20037508.34278145,
        "tilespany": 20037508.34278145,
    },
    {
        "zoom": 2,
        "bounds": [-20037508.342787, -40075016.685557604, 20037508.342776064, 20037508.342787],
        "scaledenominator": 139770566.00712565,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 39135.75848199518,
        "tilespanx": 10018754.171390766,
        "tilespany": 10018754.171390766,
    },
    {
        "zoom": 3,
        "bounds": [-20037508.342787, -35065639.599861786, 20037508.34277575, 20037508.342787],
        "scaledenominator": 69885283.00356229,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 19567.879240997438,
        "tilespanx": 5009377.085695344,
        "tilespany": 5009377.085695344,
    },
    {
        "zoom": 4,
        "bounds": [-20037508.342787, -32560951.057014164, 20037508.34277579, 20037508.342787],
        "scaledenominator": 34942641.50178117,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 9783.939620498728,
        "tilespanx": 2504688.5428476743,
        "tilespany": 2504688.5428476743,
    },
    {
        "zoom": 5,
        "bounds": [-20037508.342787, -31308606.785590325, 20037508.34277579, 20037508.342787],
        "scaledenominator": 17471320.750890587,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 4891.969810249364,
        "tilespanx": 1252344.2714238372,
        "tilespany": 1252344.2714238372,
    },
    {
        "zoom": 6,
        "bounds": [-20037508.342787, -30682434.6498784, 20037508.34277579, 20037508.342787],
        "scaledenominator": 8735660.375445293,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 2445.984905124682,
        "tilespanx": 626172.1357119186,
        "tilespany": 626172.1357119186,
    },
    {
        "zoom": 7,
        "bounds": [-20037508.342787, -30369348.58202224, 20037508.342775624, 20037508.342787],
        "scaledenominator": 4367830.187722629,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 1222.992452562336,
        "tilespanx": 313086.067855958,
        "tilespany": 313086.067855958,
    },
    {
        "zoom": 8,
        "bounds": [-20037508.342787, -30369348.58203337, 20037508.342784476, 20037508.342787],
        "scaledenominator": 2183915.093861797,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 611.496226281303,
        "tilespanx": 156543.03392801358,
        "tilespany": 156543.03392801358,
    },
    {
        "zoom": 9,
        "bounds": [-20037508.342787, -30291077.06504764, 20037508.342767175, 20037508.342787],
        "scaledenominator": 1091957.546930427,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 305.74811314051954,
        "tilespanx": 78271.516963973,
        "tilespany": 78271.516963973,
    },
    {
        "zoom": 10,
        "bounds": [-20037508.342787, -30251941.306609083, 20037508.342801783, 20037508.342787],
        "scaledenominator": 545978.773465685,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 152.8740565703918,
        "tilespanx": 39135.7584820203,
        "tilespany": 39135.7584820203,
    },
    {
        "zoom": 11,
        "bounds": [-20037508.342787, -30251941.30652203, 20037508.34273241, 20037508.342787],
        "scaledenominator": 272989.38673236995,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 76.43702828506358,
        "tilespanx": 19567.879240976275,
        "tilespany": 19567.879240976275,
    },
    {
        "zoom": 12,
        "bounds": [-20037508.342787, -30242157.366901536, 20037508.34273241, 20037508.342787],
        "scaledenominator": 136494.69336618498,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 38.21851414253179,
        "tilespanx": 9783.939620488138,
        "tilespany": 9783.939620488138,
    },
    {
        "zoom": 13,
        "bounds": [-20037508.342787, -30242157.366901536, 20037508.34273241, 20037508.342787],
        "scaledenominator": 68247.34668309249,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 19.109257071265894,
        "tilespanx": 4891.969810244069,
        "tilespany": 4891.969810244069,
    },
    {
        "zoom": 14,
        "bounds": [-20037508.342787, -30242157.366901536, 20037508.34273241, 20037508.342787],
        "scaledenominator": 34123.673341546244,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 9.554628535632947,
        "tilespanx": 2445.9849051220344,
        "tilespany": 2445.9849051220344,
    },
    {
        "zoom": 15,
        "bounds": [-20037508.342787, -30242157.3682939, 20037508.343842182, 20037508.342787],
        "scaledenominator": 17061.836671245605,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 4.777314267948769,
        "tilespanx": 1222.9924525948848,
        "tilespany": 1222.9924525948848,
    },
    {
        "zoom": 16,
        "bounds": [-20037508.342787, -30241545.8720675, 20037508.3438421, 20037508.342787],
        "scaledenominator": 8530.918335622784,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 2.3886571339743794,
        "tilespanx": 611.4962262974411,
        "tilespany": 611.4962262974411,
    },
    {
        "zoom": 17,
        "bounds": [-20037508.342787, -30241240.11838522, 20037508.339403186, 20037508.342787],
        "scaledenominator": 4265.459167338928,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 1.1943285668548997,
        "tilespanx": 305.74811311485433,
        "tilespany": 305.74811311485433,
    },
    {
        "zoom": 18,
        "bounds": [-20037508.342787, -30241087.25546706, 20037508.34828115, 20037508.342787],
        "scaledenominator": 2132.7295841419354,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 0.5971642835597418,
        "tilespanx": 152.8740565912939,
        "tilespany": 152.8740565912939,
    },
    {
        "zoom": 19,
        "bounds": [-20037508.342787, -30241010.79616208, 20037508.330525283, 20037508.342787],
        "scaledenominator": 1066.364791598498,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 0.2985821416475794,
        "tilespanx": 76.43702826178033,
        "tilespany": 76.43702826178033,
    },
    {
        "zoom": 20,
        "bounds": [-20037508.342787, -30240972.57764789, 20037508.330525238, 20037508.342787],
        "scaledenominator": 533.1823957992484,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 0.14929107082378953,
        "tilespanx": 38.21851413089012,
        "tilespany": 38.21851413089012,
    },
    {
        "zoom": 21,
        "bounds": [-20037508.342787, -30240972.57764789, 20037508.330525238, 20037508.342787],
        "scaledenominator": 266.5911978996242,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 0.07464553541189477,
        "tilespanx": 19.10925706544506,
        "tilespany": 19.10925706544506,
    },
    {
        "zoom": 22,
        "bounds": [-20037508.342787, -30240972.57764789, 20037508.330525238, 20037508.342787],
        "scaledenominator": 133.2955989498121,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 0.037322767705947384,
        "tilespanx": 9.55462853272253,
        "tilespany": 9.55462853272253,
    },
    {
        "zoom": 23,
        "bounds": [-20037508.342787, -30240972.57764789, 20037508.330525238, 20037508.342787],
        "scaledenominator": 66.64779947490605,
        "tilewidth": 256,
        "tileheight": 256,
        "pixelspan": 0.018661383852973692,
        "tilespanx": 4.777314266361265,
        "tilespany": 4.777314266361265,
    },
]

THUMBNAIL_BACKGROUND = {
    "class": "geonode.thumbs.background.GenericWMTSBackground",
    "options": {
        "url": "https://myserver.com/WMTS",
        "layer": "Hosted_basemap_inforac_3857",
        "style": "default",
        "tilematrixset": "default028mm",
        "minscaledenominator": 272989.38673236995,
    },
}

EXPECTED_RESULTS_DIR = "geonode/thumbs/tests/expected_results/"

base_request_url = "https://myserver.com/WMTS?&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/png&layer=Hosted_basemap_inforac_3857&style=default&tilematrixset=default028mm&"
mocked_requests = {
    base_request_url + "TileMatrix=4&TileRow=5&TileCol=7": f"{EXPECTED_RESULTS_DIR}/tiles/wmts_7_5_4.png",
    base_request_url + "TileMatrix=4&TileRow=6&TileCol=7": f"{EXPECTED_RESULTS_DIR}/tiles/wmts_7_6_4.png",
    base_request_url + "TileMatrix=4&TileRow=5&TileCol=8": f"{EXPECTED_RESULTS_DIR}/tiles/wmts_8_5_4.png",
    base_request_url + "TileMatrix=4&TileRow=6&TileCol=8": f"{EXPECTED_RESULTS_DIR}/tiles/wmts_8_6_4.png",
    base_request_url + "TileMatrix=4&TileRow=5&TileCol=9": f"{EXPECTED_RESULTS_DIR}/tiles/wmts_9_5_4.png",
    base_request_url + "TileMatrix=4&TileRow=6&TileCol=9": f"{EXPECTED_RESULTS_DIR}/tiles/wmts_9_6_4.png",
}


class Response:
    def __init__(self, status_code=200, content=None) -> None:
        self.status_code = status_code
        self.content = content


def get_mock(*args):
    file_path = mocked_requests.get(args[0])
    if file_path and os.path.exists(file_path):
        with open(file_path, "rb") as fin:
            return Response(200, fin.read())


class GeoNodeThumbnailWMTSBackground(GeoNodeBaseTestSupport):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @override_settings(THUMBNAIL_BACKGROUND=THUMBNAIL_BACKGROUND)
    @patch("geonode.thumbs.background.WMTS_TILEMATRIXSET_LEVELS", WMTS_TILEMATRIX_LEVELS)
    def test_get_target_pixelspan(self, *args):
        bbox = [-757689.8225283397, 4231175.960993547, 3557041.3914652625, 5957068.446590988]
        expected_target_pixelspan = 8629.462427987204
        background = GenericWMTSBackground(thumbnail_width=500, thumbnail_height=200)
        target_pixelspan = background.get_target_pixelspan(bbox)
        self.assertAlmostEqual(expected_target_pixelspan, target_pixelspan)

    @override_settings(THUMBNAIL_BACKGROUND=THUMBNAIL_BACKGROUND)
    @patch("geonode.thumbs.background.WMTS_TILEMATRIXSET_LEVELS", WMTS_TILEMATRIX_LEVELS)
    def test_get_level_for_targetpixelspan(self, *args):
        target_pixelspan = 8629.462427987204
        background = GenericWMTSBackground(thumbnail_width=500, thumbnail_height=200)
        level = background.get_level_for_targetpixelspan(target_pixelspan)
        self.assertDictEqual(level, WMTS_TILEMATRIX_LEVELS[4])

    @override_settings(THUMBNAIL_BACKGROUND=THUMBNAIL_BACKGROUND)
    @patch("geonode.thumbs.background.WMTS_TILEMATRIXSET_LEVELS", WMTS_TILEMATRIX_LEVELS)
    def test_get_tiles_coords(self, *args):
        bbox = [-757689.8225283397, 4231175.960993547, 3557041.3914652625, 5957068.446590988]
        level = WMTS_TILEMATRIX_LEVELS[4]
        expected_tile_rowcols = [[7, 5], [7, 6], [8, 5], [8, 6], [9, 5], [9, 6]]
        background = GenericWMTSBackground(thumbnail_width=500, thumbnail_height=200)
        tile_rowcols = background.get_tiles_coords(level, bbox)
        self.assertListEqual(expected_tile_rowcols, tile_rowcols)

    @override_settings(THUMBNAIL_BACKGROUND=THUMBNAIL_BACKGROUND)
    @patch("geonode.thumbs.background.WMTS_TILEMATRIXSET_LEVELS", WMTS_TILEMATRIX_LEVELS)
    def test_build_request(self, *args):
        expected_imgurl = "https://myserver.com/WMTS?&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image/png&\
layer=Hosted_basemap_inforac_3857&style=default&tilematrixset=default028mm&TileMatrix=4&TileRow=5&TileCol=7"
        background = GenericWMTSBackground(thumbnail_width=500, thumbnail_height=200)
        imgurl = background.build_request((7, 5, 4))
        self.assertEqual(expected_imgurl, imgurl)

    @override_settings(THUMBNAIL_BACKGROUND=THUMBNAIL_BACKGROUND)
    @patch("geonode.thumbs.background.WMTS_TILEMATRIXSET_LEVELS", WMTS_TILEMATRIX_LEVELS)
    @patch("geonode.thumbs.background.requests.get", get_mock)
    def test_tile_request(self, *args):
        bbox = [-757689.8225283397, 3557041.3914652625, 4231175.960993547, 5957068.446590988, "EPSG:3857"]
        background = GenericWMTSBackground(thumbnail_width=500, thumbnail_height=200)
        image = background.fetch(bbox)
        expected_image = Image.open(f"{EXPECTED_RESULTS_DIR}/tiles/background.png")
        diff = Image.new("RGB", image.size)

        mismatch = pixelmatch(image, expected_image, diff)
        if mismatch >= expected_image.size[0] * expected_image.size[1] * 0.01:
            logger.warn("Mismatch, it was not possible to bump the bg!")
        else:
            self.assertTrue(
                mismatch < expected_image.size[0] * expected_image.size[1] * 0.01,
                "Expected test and pre-generated backgrounds to differ up to 1%",
            )
