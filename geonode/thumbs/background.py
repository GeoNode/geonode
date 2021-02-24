import time
import typing
import logging
import mercantile

from PIL import Image
from math import ceil, copysign
from io import BytesIO
from abc import ABC, abstractmethod
from pyproj import Transformer

from geonode.utils import http_client
from geonode.thumbs.utils import make_bbox_to_pixels_transf
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
    def fetch(self, bbox: typing.List, *args, **kwargs):
        """
        Function fetching background image, based on the given BBOX

        :param bbox: a layer compliant BBOX: [west, east, south, north] bounds list
        """
        pass


class TileThumbBackground(BaseThumbBackground):
    def __init__(self, thumbnail_width: int, thumbnail_height: int, max_retries: int = 3, retry_delay: int = 1):
        super().__init__(thumbnail_width, thumbnail_height, max_retries, retry_delay)
        self.mercantile_bbox = None  # BBOX compliant with mercantile lib: [west, south, east, north] bounds list

    @property
    @abstractmethod
    def url_template(self) -> str:
        """
        URL template from where to fetch tiles, with x, y, z parameters, e.g.:
        'https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png'
        """
        pass

    @property
    @abstractmethod
    def tile_size(self) -> int:
        """
        A size of tiles retrieved from url_template URL in pixels
        """
        pass

    @property
    def tiles_crs(self) -> str:
        """
        The CRS of the retrieved tiles in format 'EPSG:xxxx', e.g.: EPSG:3857
        """
        return "EPSG:3857"

    def bbox3857to4326(self, x_min, x_max, y_min, y_max):
        """
        Function converting BBOX from EPSG:3857 to EPSG:4326, keeping the order of the coordinates.
        To ensure no additional change is performed, conversion is based on top-left and bottom-right
        points conversion.
        """
        transformer = Transformer.from_crs("epsg:3857", "epsg:4326", always_xy=True)
        left, top = transformer.transform(x_min, y_max)
        right, bottom = transformer.transform(x_max, y_min)

        return [left, right, bottom, top]

    def bbox4326to3857(self, x_min, x_max, y_min, y_max):
        """
        Function converting BBOX from EPSG:4326 to EPSG:3857, keeping the order of the coordinates.
        To ensure no additional change is performed, conversion is based on top-left and bottom-right
        points conversion.
        """
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857", always_xy=True)
        left, top = transformer.transform(x_min, y_max)
        right, bottom = transformer.transform(x_max, y_min)

        return [left, right, bottom, top]

    def fetch(self, bbox: typing.List, zoom: int = None, *args, **kwargs):
        """
        The function fetching tiles from a Slippy Map provider, composing them into a single image, and cropping it
        to match the given BBOX. Retrieval of each tile is repeated self.max_retries times, waiting self.retry_delay
        seconds between consecutive requests.

        :param bbox: bounding box of the background image, layer compliant format: [west, east, south, north, CRS]
        :param zoom: zoom with which to retrieve Slippy Map's tiles (by default, it's calculated based on width, height)
        :return: None if the CRS is different from self.tiles_crs, or background Image
        """

        if bbox[-1] != self.tiles_crs:
            # background service is not available the requested CRS CRS
            logger.debug(
                f"Thumbnail background generation skipped. "
                f"Clashing CRSs: requested {bbox[-1]}, supported {self.tiles_crs}"
            )
            return

        bbox = [float(coord) for coord in bbox[0:4]]
        bbox4326 = self.bbox3857to4326(*bbox)

        # change bbox from layer (left, right, bottom, top) to mercantile (left, bottom, right, top)
        self.mercantile_bbox = [bbox4326[0], bbox4326[2], bbox4326[1], bbox4326[3]]

        # calculate zoom level
        if zoom is None:
            zoom = self.calculate_zoom()

        top_left_tile = mercantile.tile(bbox4326[0], bbox4326[3], zoom)
        bottom_right_tile = mercantile.tile(bbox4326[1], bbox4326[2], zoom)

        map_row_number = 2**zoom - 1  # number of tiles in the Map's row for a certain zoom level

        if top_left_tile.x > bottom_right_tile.x:
            # BBOX crosses Slippy Map's border
            tiles_rows = list(range(top_left_tile.x, map_row_number + 1)) + list(range(bottom_right_tile.x + 1))
        else:
            # BBOx is contained by the Slippy Map
            tiles_rows = list(range(top_left_tile.x, bottom_right_tile.x + 1))

        tiles_cols = list(range(top_left_tile.y, bottom_right_tile.y + 1))

        background = Image.new(
            "RGB", (len(tiles_rows) * self.tile_size, len(tiles_cols) * self.tile_size), (250, 250, 250)
        )

        for offset_x, x in enumerate(tiles_rows):
            for offset_y, y in enumerate(tiles_cols):
                imgurl = self.url_template.format(x=x, y=y, z=zoom)

                for retries in range(self.max_retries):
                    try:
                        resp, content = http_client.request(imgurl)
                        im = BytesIO(content)
                        Image.open(im).verify()  # verify that it is, in fact an image
                    except Exception as e:
                        logger.debug(f"Thumbnail background fetching from {imgurl} failed {retries} time(s) with: {e}")
                        if retries + 1 == self.max_retries:
                            logger.exception(e)
                            raise
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        break

                image = Image.open(im)  # "re-open" the file (required after running verify method)

                # add the fetched tile to the background image, placing it under proper coordinates
                background.paste(image, (offset_x * self.tile_size, offset_y * self.tile_size))

        # get BBOX of the tiles
        top_left_bounds = mercantile.bounds(top_left_tile)
        bottom_right_bounds = mercantile.bounds(bottom_right_tile)

        tiles_bbox3857 = self.bbox4326to3857(
            getattr(top_left_bounds, 'west'),
            getattr(bottom_right_bounds, 'east'),
            getattr(bottom_right_bounds, 'south'),
            getattr(top_left_bounds, 'north')
        )

        # rescale tiles' boundaries - if space covered by the input BBOX is greater than the width of the world,
        # (e.g. two "worlds" are present on the map), translation between tiles' BBOX and image's pixel requires
        # additional rescaling, for tiles' BBOX coordinates to match input BBOX coordinates
        epsg3857_max_x = 20026376.39
        epsg3857_world_width = 2 * epsg3857_max_x

        west_rescaling_factor = abs(bbox[0]) // epsg3857_max_x * copysign(1, bbox[0])
        east_rescaling_factor = abs(bbox[1]) // epsg3857_max_x * copysign(1, bbox[0])
        west_coord = tiles_bbox3857[0] + west_rescaling_factor * epsg3857_world_width
        east_coord = tiles_bbox3857[1] + east_rescaling_factor * epsg3857_world_width

        # prepare translating function from received BBOX to pixel values of the background image
        src_quad = (0, 0, background.size[0], background.size[1])
        to_src_px = make_bbox_to_pixels_transf(
            [west_coord, tiles_bbox3857[2], east_coord, tiles_bbox3857[3]],
            src_quad
        )

        # translate received BBOX to pixel values
        minx, miny = to_src_px(bbox[0], bbox[2])
        maxx, maxy = to_src_px(bbox[1], bbox[3])

        crop_box = (round(minx), round(maxy), round(maxx), round(miny))

        if not all([0 < crop_x < background.size[0] for crop_x in [crop_box[0], crop_box[2]]]):
            raise ThumbnailError('Background cropping error. Boundaries outside of the image.')

        if not all([0 < crop_x < background.size[0] for crop_x in [crop_box[1], crop_box[3]]]):
            raise ThumbnailError('Background cropping error. Boundaries outside of the image.')

        # crop background image to the desired bbox and resize it
        background = background.crop(box=crop_box)
        background = background.resize((self.thumbnail_width, self.thumbnail_height))

        return background

    def calculate_zoom(self):
        # maximum number of needed tiles for thumbnail of given width and height
        max_tiles = (ceil(self.thumbnail_width / self.tile_size) + 1) * (
            ceil(self.thumbnail_height / self.tile_size) + 1
        )

        # zoom for which there are less needed tiles than max_tiles
        zoom = 0
        for z in range(1, 16):
            if len(list(mercantile.tiles(*self.mercantile_bbox, z))) > max_tiles:
                break
            else:
                zoom = max(zoom, z)

        return zoom


class WikimediaTileBackground(TileThumbBackground):
    @property
    def tile_size(self) -> int:
        return 256

    @property
    def url_template(self) -> str:
        return "https://maps.wikimedia.org/osm-intl/{z}/{x}/{y}.png"
