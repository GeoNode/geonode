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

import time
import ast
import typing
import logging
import mercantile

from io import BytesIO
from pyproj import Transformer
from abc import ABC, abstractmethod
from math import ceil, floor, copysign
from PIL import Image, UnidentifiedImageError

from django.conf import settings
from django.utils.html import strip_tags

from geonode.thumbs import utils
from geonode.utils import http_client
from geonode.thumbs.exceptions import ThumbnailError

logger = logging.getLogger(__name__)


class BaseThumbBackground(ABC):

    def __init__(self, thumbnail_width: int, thumbnail_height: int, max_retries: int = 3, retry_delay: int = 1):
        """
        Base class for thumbnails background retrieval.

        :param thumbnail_width: target width of the background image in pixels
        :param thumbnail_height: target height of the background image in pixels
        :param max_retries: maximum number of retrieval retries before raising an exception
        :param retry_delay: number of seconds waited between consecutive retrieval retries
        """
        self.thumbnail_width = thumbnail_width
        self.thumbnail_height = thumbnail_height
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @abstractmethod
    def fetch(self, bbox: typing.List, *args, **kwargs) -> typing.Optional[Image.Image]:
        """
        Function fetching background image, based on the given BBOX.
        On error should raise an exception or return None.

        :param bbox: a dataset compliant BBOX: [west, east, south, north, CRS]
        """
        pass


class GenericWMSBackground(BaseThumbBackground):

    def __init__(
        self,
        thumbnail_width: int,
        thumbnail_height: int,
        max_retries: int = 3,
        retry_delay: int = 1,
    ):
        """
        Generic WMS background generation class.

        Initialization options (valid in settings.THUMBNAIL_BACKGROUND['options']):
        :key service_url: dataset's provider (OGC server's location)
        :key dataset_name: name of a dataset to be used as the background
        :key format: retrieve image's format/mime-type (defautl 'image/png')
        :key version: WMS service version (default '1.3.0')
        :key styles: dataset's style (default None)
        :key srid: CRS which an image should be retrieved in (default 'EPSG:3857')
        """
        super().__init__(thumbnail_width, thumbnail_height, max_retries, retry_delay)

        options = settings.THUMBNAIL_BACKGROUND.get("options", {})

        # WMS specific attributes (to be overwritten in specific background classes)
        service_url = options.get("service_url", None)
        self.service_url = f"{service_url}/" if service_url and not service_url.endswith("/") else service_url
        self.dataset_name = options.get("dataset_name", None)
        self.format = options.get("format", "image/png")
        self.version = options.get("version", "1.3.0")
        self.styles = options.get("styles", None)
        srid = options.get("srid", "EPSG:3857")
        self.srid = srid if "EPSG:" in srid else f"EPSG:{srid}"
        # ---

    def bbox_to_projection(self, bbox: typing.List):
        """
        Function converting BBOX to target projection system, keeping the order of the coordinates.
        To ensure no additional change is performed, conversion is based on top-left and bottom-right
        points conversion.

        :param bbox: a dataset compliant BBOX: [west, east, south, north, CRS]
        """
        transformer = Transformer.from_crs(bbox[-1].lower(), self.srid.lower(), always_xy=True)

        left, top = transformer.transform(bbox[0], bbox[3])
        right, bottom = transformer.transform(bbox[1], bbox[2])

        return [left, right, bottom, top]

    def fetch(self, bbox: typing.List, *args, **kwargs):
        """
        Function fetching background image, based on the given BBOX.
        On error should raise an exception or return None.

        :param bbox: a dataset compliant BBOX: [west, east, south, north, CRS]
        :param *args: not used, kept for API compatibility
        :param **kargs: not used, kept for API compatibility
        """

        if not self.service_url or not self.dataset_name:
            logger.error("Thumbnail background configured improperly: service URL and dataset name may not be empty")
            return

        background = Image.new("RGB", (self.thumbnail_width, self.thumbnail_height), (250, 250, 250))
        img = utils.get_map(
            self.service_url,
            [self.dataset_name],
            self.bbox_to_projection(bbox) + [self.srid],
            wms_version=self.version,
            mime_type=self.format,
            styles=self.styles,
            width=self.thumbnail_width,
            height=self.thumbnail_height,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
        )

        try:
            content = BytesIO(img)
            with Image.open(content) as image:
                image.verify()  # verify that it is, in fact an image
                image = Image.open(content)  # "re-open" the file (required after running verify method)
                background.paste(image)
        except UnidentifiedImageError as e:
            logger.error(f"Thumbnail generation. Error occurred while fetching background image: {e}")
            raise e
        except Exception as e:
            logger.error(f"Thumbnail generation. Error occurred while fetching background image: {e}")
            logger.exception(e)
        return background


class GenericXYZBackground(BaseThumbBackground):

    def __init__(
        self,
        thumbnail_width: int,
        thumbnail_height: int,
        max_retries: int = 3,
        retry_delay: int = 1,
    ):
        """
        Generic Slippy Maps background generation class for services EPSG:3857 compliant.

        Initialization options (valid in settings.THUMBNAIL_BACKGROUND['options']):
        :key url: XYZ url template with '{x}', '{y}' and '{z}' placeholders for x, y coordinates and zoom respectively
        :key tile_size: tile size in pixels (default 256)
        """

        super().__init__(thumbnail_width, thumbnail_height, max_retries, retry_delay)

        options = settings.THUMBNAIL_BACKGROUND.get("options", {})

        # Slippy Maps specific attributes (to be overwritten in specific background classes)
        self.url = options.get("url", None)
        self.tile_size = options.get("tile_size", 256)
        self.tms = False
        try:
            self.tms = ast.literal_eval(str(options.get('tms')))
        except Exception:
            pass
        # ---

        # class's internal attributes
        self.crs = "EPSG:3857"
        self._epsg3857_max_x = 20026376.39
        self._epsg3857_max_y = 20048966.10
        self._mercantile_bbox = None  # BBOX compliant with mercantile lib: [west, south, east, north] bounds list

    def point3857to4326(self, x, y):
        transformer = Transformer.from_crs("EPSG:3857", "EPSG:4326", always_xy=True)
        return transformer.transform(x, y)

    def point4326to3857(self, x, y):
        transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)
        return transformer.transform(x, y)

    def bbox3857to4326(self, x_min, x_max, y_min, y_max):
        """
        Function converting BBOX from EPSG:3857 to EPSG:4326, keeping the order of the coordinates.
        To ensure no additional change is performed, conversion is based on top-left and bottom-right
        points conversion.
        """
        left, top = self.point3857to4326(x_min, y_max)
        right, bottom = self.point3857to4326(x_max, y_min)

        return [left, right, bottom, top]

    def bbox4326to3857(self, x_min, x_max, y_min, y_max):
        """
        Function converting BBOX from EPSG:4326 to EPSG:3857, keeping the order of the coordinates.
        To ensure no additional change is performed, conversion is based on top-left and bottom-right
        points conversion.
        """
        left, top = self.point4326to3857(x_min, y_max)
        right, bottom = self.point4326to3857(x_max, y_min)

        return [left, right, bottom, top]

    def fetch(self, bbox: typing.List, zoom: int = None, *args, **kwargs):
        """
        The function fetching tiles from a Slippy Map provider, composing them into a single image, and cropping it
        to match the given BBOX. Retrieval of each tile is repeated self.max_retries times, waiting self.retry_delay
        seconds between consecutive requests.

        :param bbox: bounding box of the background image, dataset compliant format: [west, east, south, north, CRS]
        :param zoom: zoom with which to retrieve Slippy Map's tiles (by default, it's calculated based on width, height)
        :return: None if the CRS is different from self.tiles_crs, or background Image
        """

        if not self.url:
            logger.error("Thumbnail background requires url to be configured.")
            raise ThumbnailError("Tiled background improperly configured.")

        if bbox[-1].lower() != self.crs.lower():
            # background service is not available the requested CRS CRS
            logger.debug(
                f"Thumbnail background generation skipped. "
                f"Clashing CRSs: requested {bbox[-1]}, supported {self.crs}"
            )
            return

        bbox = [float(coord) for coord in bbox[0:4]]

        # check if BBOX fits within the EPSG:3857 map, if not - return an empty background
        if bbox[2] > self._epsg3857_max_y or bbox[3] < -self._epsg3857_max_y:
            return Image.new("RGB", (self.thumbnail_width, self.thumbnail_height), (250, 250, 250))

        bbox4326 = self.bbox3857to4326(*bbox)

        # change bbox from dataset (left, right, bottom, top) to mercantile (left, bottom, right, top)
        self._mercantile_bbox = [bbox4326[0], bbox4326[2], bbox4326[1], bbox4326[3]]

        # calculate zoom level
        if zoom is None:
            zoom = self.calculate_zoom()
        else:
            zoom = int(zoom)

        top_left_tile = mercantile.tile(bbox4326[0], bbox4326[3], zoom)
        bottom_right_tile = mercantile.tile(bbox4326[1], bbox4326[2], zoom)

        # rescaling factors - indicators of how west and east BBOX boundaries are offset in respect to the world's map;
        # east and west boundaries may exceed the maximum coordinate of the world in EPSG:3857. In such case additinal
        # number of tiles need to be fetched to compose the image and the boundary tiles' coordinates need to be
        # rescaled to ensure the proper image cropping.
        epsg3857_world_width = 2 * self._epsg3857_max_x

        west_rescaling_factor = 0
        if abs(bbox[0]) > self._epsg3857_max_x:
            west_rescaling_factor = ceil((abs(bbox[0]) - self._epsg3857_max_x) / epsg3857_world_width) * copysign(
                1, bbox[0]
            )

        east_rescaling_factor = 0
        if abs(bbox[1]) > self._epsg3857_max_x:
            east_rescaling_factor = ceil((abs(bbox[1]) - self._epsg3857_max_x) / epsg3857_world_width) * copysign(
                1, bbox[1]
            )

        map_row_tiles = 2 ** zoom - 1  # number of tiles in the Map's row for a certain zoom level

        map_worlds = int(east_rescaling_factor - west_rescaling_factor)  # number maps in an image
        worlds_between = map_worlds - 1  # number of full maps in an image
        if top_left_tile.x > bottom_right_tile.x or bbox[1] - bbox[0] > epsg3857_world_width or map_worlds > 0:
            # BBOX crosses Slippy Map's border
            if worlds_between > 0:
                tiles_rows = (
                    list(range(top_left_tile.x, map_row_tiles + 1))
                    + worlds_between * list(range(map_row_tiles + 1))
                    + list(range(bottom_right_tile.x + 1))
                )
            else:
                tiles_rows = list(range(top_left_tile.x, map_row_tiles + 1)) + list(range(bottom_right_tile.x + 1))
        else:
            # BBOx is contained by the Slippy Map
            if worlds_between > 0:
                tiles_rows = list(range(top_left_tile.x, bottom_right_tile.x + 1)) + worlds_between * list(
                    range(map_row_tiles + 1)
                )
            else:
                tiles_rows = list(range(top_left_tile.x, bottom_right_tile.x + 1))

        tiles_cols = list(range(top_left_tile.y, bottom_right_tile.y + 1))

        # if latitude boundaries extend world's height - add background's height, and set constant Y offset for tiles
        additional_height = 0
        fixed_top_offset = 0
        fixed_bottom_offset = 0

        north_extension3857 = max(0, bbox[3] - self._epsg3857_max_y)
        south_extension3857 = abs(min(0, bbox[2] + self._epsg3857_max_y))
        extension3857 = north_extension3857 + south_extension3857

        if extension3857:
            # get single tile's height in ESPG:3857
            tile_bounds = mercantile.bounds(tiles_rows[0], tiles_cols[0], zoom)
            _, south = self.point4326to3857(getattr(tile_bounds, "west"), getattr(tile_bounds, "south"))
            _, north = self.point4326to3857(getattr(tile_bounds, "west"), getattr(tile_bounds, "north"))
            tile_hight3857 = north - south

            additional_height = round(self.tile_size * extension3857 / tile_hight3857)  # based on linear proportion

            if north_extension3857:
                fixed_top_offset = round(self.tile_size * north_extension3857 / tile_hight3857)

            if south_extension3857:
                fixed_bottom_offset = round(self.tile_size * south_extension3857 / tile_hight3857)

        background = Image.new(
            "RGB",
            (len(tiles_rows) * self.tile_size, len(tiles_cols) * self.tile_size + additional_height),
            (250, 250, 250),
        )

        for offset_x, x in enumerate(tiles_rows):
            for offset_y, y in enumerate(tiles_cols):
                if self.tms:
                    y = (2 ** zoom) - y - 1
                imgurl = self.url.format(x=x, y=y, z=zoom)

                im = None
                for retries in range(self.max_retries):
                    try:
                        resp, content = http_client.request(imgurl)
                        if resp.status_code > 400:
                            retries = self.max_retries - 1
                            raise Exception(f"{strip_tags(content)}")
                        im = BytesIO(content)
                        Image.open(im).verify()  # verify that it is, in fact an image
                        break
                    except Exception as e:
                        logger.error(f"Thumbnail background fetching from {imgurl} failed {retries} time(s) with: {e}")
                        if retries + 1 == self.max_retries:
                            raise e
                        time.sleep(self.retry_delay)
                        continue

                if im:
                    image = Image.open(im)  # "re-open" the file (required after running verify method)

                    # add the fetched tile to the background image, placing it under proper coordinates
                    background.paste(image, (offset_x * self.tile_size, offset_y * self.tile_size + fixed_top_offset))

        # get BBOX of the tiles
        top_left_bounds = mercantile.bounds(top_left_tile)
        bottom_right_bounds = mercantile.bounds(bottom_right_tile)

        tiles_bbox3857 = self.bbox4326to3857(
            getattr(top_left_bounds, "west"),
            getattr(bottom_right_bounds, "east"),
            getattr(bottom_right_bounds, "south"),
            getattr(top_left_bounds, "north"),
        )

        # rescale tiles' boundaries - if space covered by the input BBOX extends the width of the world,
        # (e.g. two "worlds" are present on the map), translation between tiles' BBOX and image's pixel requires
        # additional rescaling, for tiles' BBOX coordinates to match input BBOX coordinates
        west_coord = tiles_bbox3857[0] + west_rescaling_factor * epsg3857_world_width
        east_coord = tiles_bbox3857[1] + east_rescaling_factor * epsg3857_world_width

        # prepare translating function from received BBOX to pixel values of the background image
        src_quad = (0, fixed_top_offset, background.size[0], background.size[1] - fixed_bottom_offset)
        to_src_px = utils.make_bbox_to_pixels_transf(
            [west_coord, tiles_bbox3857[2], east_coord, tiles_bbox3857[3]], src_quad
        )

        # translate received BBOX to pixel values
        minx, miny = to_src_px(bbox[0], bbox[2])
        maxx, maxy = to_src_px(bbox[1], bbox[3])

        # max and min function for Y axis were introduced to mitigate rounding errors
        crop_box = (
            ceil(minx),
            max(ceil(maxy) + fixed_top_offset, 0),
            floor(maxx),
            min(floor(miny) + fixed_top_offset, background.size[1]),
        )

        if not all([0 <= crop_x <= background.size[0] for crop_x in [crop_box[0], crop_box[2]]]):
            raise ThumbnailError(f"Tiled background cropping error. Boundaries outside of the image: {crop_box}")

        # crop background image to the desired bbox and resize it
        background = background.crop(box=crop_box)
        background = background.resize((self.thumbnail_width, self.thumbnail_height))

        if sum(background.convert("L").getextrema()) in (0, 2):
            # either all black or all white
            logger.error("Thumbnail background outside the allowed area.")
            raise ThumbnailError("Thumbnail background outside the allowed area.")
        return background

    def calculate_zoom(self):
        # maximum number of needed tiles for thumbnail of given width and height
        max_tiles = (ceil(self.thumbnail_width / self.tile_size) + 1) * (
            ceil(self.thumbnail_height / self.tile_size) + 1
        )

        # zoom for which there are less needed tiles than max_tiles
        zoom = 0
        for z in range(1, 16):
            if len(list(mercantile.tiles(*self._mercantile_bbox, z))) > max_tiles:
                break
            else:
                zoom = max(zoom, z)
        return zoom


class WikiMediaTileBackground(GenericXYZBackground):

    def __init__(
        self,
        thumbnail_width: int,
        thumbnail_height: int,
        max_retries: int = 3,
        retry_delay: int = 1,
    ):
        """
        Specific Wikimedia background generation class for thumbnails.
        """
        super().__init__(thumbnail_width, thumbnail_height, max_retries, retry_delay)

        self.url = "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"
        self.tile_size = 256


class OSMTileBackground(GenericXYZBackground):

    def __init__(
        self,
        thumbnail_width: int,
        thumbnail_height: int,
        max_retries: int = 3,
        retry_delay: int = 1,
    ):
        """
        Specific OpenStreetMaps background generation class for thumbnails.
        """
        super().__init__(thumbnail_width, thumbnail_height, max_retries, retry_delay)

        self.url = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        self.tile_size = 256
