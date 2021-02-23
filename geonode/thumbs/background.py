import time
import typing
import logging
import mercantile

from PIL import Image
from math import ceil
from io import BytesIO
from abc import ABC, abstractmethod

from geonode.utils import http_client
from geonode.thumbs.utils import make_bbox_to_pixels_transf
from geonode.utils import bbox_to_projection

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

        # convert to EPSG:4326 used by mercantile & make sure bbox coords are numbers
        bbox4326 = [float(coord) for coord in bbox_to_projection(bbox, target_srid=4326)[0:4]]

        # change bbox from layer (left, right, bottom, top) to mercantile (left, bottom, right, top)
        self.mercantile_bbox = [bbox4326[0], bbox4326[2], bbox4326[1], bbox4326[3]]

        # calculate zoom level
        if zoom is None:
            zoom = self.calculate_zoom()

        tiles = list(mercantile.tiles(*self.mercantile_bbox, zoom))

        # create image of the desired size
        tiles_x = [t.x for t in tiles]
        tiles_y = [t.y for t in tiles]
        width = max(tiles_x) - min(tiles_x) + 1
        height = max(tiles_y) - min(tiles_y) + 1
        background = Image.new("RGB", (width * self.tile_size, height * self.tile_size), (250, 250, 250))

        # fetch tiles and merge them into a single image
        offset_x = tiles[0].x  # x coordinate in the background image
        offset_y = tiles[0].y  # y coordinate in the background image

        # background coordinates
        tiles_bbox4326 = [
            getattr(mercantile.bounds(tiles[0]), "west"),
            getattr(mercantile.bounds(tiles[0]), "south"),
            getattr(mercantile.bounds(tiles[0]), "east"),
            getattr(mercantile.bounds(tiles[0]), "north"),
        ]

        for tile in tiles:
            imgurl = self.url_template.format(x=tile.x, y=tile.y, z=tile.z)

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
                    # update background corners coords
                    tiles_bbox4326 = [
                        min(getattr(mercantile.bounds(tile), "west"), tiles_bbox4326[0]),
                        min(getattr(mercantile.bounds(tile), "south"), tiles_bbox4326[1]),
                        max(getattr(mercantile.bounds(tile), "east"), tiles_bbox4326[2]),
                        max(getattr(mercantile.bounds(tile), "north"), tiles_bbox4326[3]),
                    ]
                    break

            image = Image.open(im)  # "re-open" the file (required after running verify method)

            # add the fetched tile to the background image, placing it under proper coordinates
            background.paste(image, ((tile.x - offset_x) * self.tile_size, (tile.y - offset_y) * self.tile_size))

        # convert tiles BBOX to EPSG:3857 (required for the proper cropping) and make sure bbox coords are number
        tiles_bbox3857 = bbox_to_projection(
            [tiles_bbox4326[0], tiles_bbox4326[2], tiles_bbox4326[1], tiles_bbox4326[3], "EPSG:4326"], target_srid=3857
        )
        # rearrange coords to match mercantile notation
        tiles_bbox3857 = [
            float(tiles_bbox3857[0]),
            float(tiles_bbox3857[2]),
            float(tiles_bbox3857[1]),
            float(tiles_bbox3857[3]),
        ]

        # prepare translating function from received BBOX to pixel values of the background image
        src_quad = (0, 0, background.size[0], background.size[1])
        to_src_px = make_bbox_to_pixels_transf(tiles_bbox3857, src_quad)

        # translate received BBOX to pixel values
        minx, miny = to_src_px(float(bbox[0]), float(bbox[2]))
        maxx, maxy = to_src_px(float(bbox[1]), float(bbox[3]))

        crop_box = (round(minx), round(maxy), round(maxx), round(miny))

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
