# -*- coding: utf-8 -*-
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
import base64
import logging

from pyproj import Transformer
from typing import List, Tuple, Callable, Union

from django.conf import settings
from django.contrib.auth import get_user_model

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.base.auth import get_or_create_token
from geonode.utils import http_client
from geonode.geoserver.helpers import OGC_Servers_Handler

logger = logging.getLogger(__name__)


def make_bbox_to_pixels_transf(src_bbox: Union[List, Tuple], dest_bbox: Union[List, Tuple]) -> Callable:
    """
    Linear transformation of bbox between CRS and pixel values:

    (xmin, ymax)          (xmax, ymax)                      (0, 0)          (width, 0)
         -------------------                                     -------------------
        |  x                |                                   |    | y'           |
        |----* (x, y)       |               ->                  |----* (x', y')     |
        |    | y            |                                   |  x'               |
         -------------------                                     -------------------
    (xmin, ymin)          (xmin, ymax)                      (0, height)    (width, height)

    based on linear proportions:
              x - xmin      x'                        y - ymin    height - y'
            ----------- = -----                     ----------- = -----------
            xmax - xmin   width                     ymax - ymin      height

    Note: Y axis have opposite directions

    :param src_bbox: image's BBOX in a certain CRS, in (xmin, ymin, xmax, ymax) order
    :param dest_bbox: image's BBOX in pixels: (0,0,PIL.Image().size[0], PIL.Image().size[1])
    :return: function translating X, Y coordinates in CRS to (x, y) coordinates in pixels
    """

    return lambda x, y: (
        (x - src_bbox[0]) * (dest_bbox[2] - dest_bbox[0]) / (src_bbox[2] - src_bbox[0]) + dest_bbox[0],
        dest_bbox[3] - dest_bbox[1] - (y - src_bbox[1]) * (dest_bbox[3] - dest_bbox[1]) / (src_bbox[3] - src_bbox[1]),
    )


def transform_bbox(bbox: List, target_crs: str = "epsg:3857"):
    """
    Function transforming BBOX in layer compliant format (xmin, xmax, ymin, ymax, 'EPSG:xxxx') to another CRS,
    preserving overflow values.
    """
    transformer = Transformer.from_crs(bbox[-1].lower(), target_crs.lower(), always_xy=True)
    x_min, y_min = transformer.transform(bbox[0], bbox[2])
    x_max, y_max = transformer.transform(bbox[1], bbox[3])

    return [x_min, x_max, y_min, y_max, target_crs]


def expand_bbox_to_ratio(
    bbox: List,
    target_width: int = settings.THUMBNAIL_SIZE["width"],
    target_height: int = settings.THUMBNAIL_SIZE["height"],
):
    """
    Function returning an expanded BBOX, ensuring it's ratio, based on the provided BBOX, and width and height
    of the target image.

    :param bbox: a layer compliant BBOX in a certain CRS, in (xmin, xmax, ymin, ymax, 'EPSG:xxxx') order
    :param target_width: width of the target image in pixels
    :param target_height: height of the target image in pixels
    :return: BBOX (in input's format) with provided height/width ratio, and unchanged center point
             (in regard to the input BBOX)
    """
    # convert bbox to EPSG:3857
    x_min, x_max, y_min, y_max, _ = transform_bbox(bbox)

    # scale up to ratio
    ratio = target_height / target_width

    bbox_width = abs(x_max - x_min)
    bbox_height = abs(y_max - y_min)

    if bbox_width > bbox_height:
        new_height = ratio * bbox_width
        new_width = bbox_width
    else:
        new_height = bbox_height
        new_width = bbox_height / ratio

    x_mid = (x_min + x_max) / 2
    y_mid = (y_min + y_max) / 2

    new_bbox = [
        x_mid - new_width / 2,
        x_mid + new_width / 2,
        y_mid - new_height / 2,
        y_mid + new_height / 2,
        "epsg:3857",
    ]

    # make sure we do not fell into a 'zero-area' use case
    TOLERANCE = 1.0e-7
    if new_bbox[0] == new_bbox[1]:
        new_bbox[0] -= TOLERANCE
        new_bbox[1] += TOLERANCE
    if new_bbox[2] == new_bbox[3]:
        new_bbox[2] -= TOLERANCE
        new_bbox[3] += TOLERANCE

    # convert bbox to target_crs
    return transform_bbox(new_bbox, target_crs=bbox[-1].lower())


def assign_missing_thumbnail(instance: Union[Layer, Map]) -> None:
    """
    Function assigning settings.MISSING_THUMBNAIL to a provided instance

    :param instance: instance of Layer or Map models
    """
    instance.save_thumbnail("", image=None)


def construct_wms_url(
    ogc_server_location: str,
    layers: List,
    bbox: List,
    wms_version: str = settings.OGC_SERVER["default"].get("WMS_VERSION", "1.1.0"),
    mime_type: str = "image/png",
    styles: str = None,
    width: int = 240,
    height: int = 200,
) -> str:
    """
    Method constructing a GetMap URL to the OGC server.

    :param ogc_server_location: OGC server URL
    :param layers: layers which should be fetched from the OGC server
    :param bbox: area's bounding box in format: [west, east, south, north, CRS]
    :param wms_version: WMS version of the query
    :param mime_type: mime type of the returned image
    :param styles: styles, which OGC server should use for rendering an image
    :param width: width of the returned image
    :param height: height of the returned image

    :return: GetMap URL
    """
    # create GetMap query parameters
    params = {
        "service": "WMS",
        "version": wms_version,
        "request": "GetMap",
        "layers": ",".join(layers),
        "bbox": ",".join([str(bbox[0]), str(bbox[2]), str(bbox[1]), str(bbox[3])]),
        "crs": bbox[-1],
        "width": width,
        "height": height,
        "format": mime_type,
        "transparent": True,
    }

    if styles is not None:
        params["styles"] = styles

    # create GetMap request
    ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]

    if ogc_server_location is not None:
        thumbnail_url = ogc_server_location
    else:
        thumbnail_url = ogc_server_settings.LOCATION

    wms_endpoint = ""
    if thumbnail_url == ogc_server_settings.LOCATION:
        # add access token to requests to Geoserver (logic based on the previous implementation)
        username = ogc_server_settings.credentials.username
        user = get_user_model().objects.filter(username=username).first()
        if user:
            access_token = get_or_create_token(user)
            if access_token and not access_token.is_expired():
                params["access_token"] = access_token.token

        # add WMS endpoint to requests to Geoserver
        wms_endpoint = getattr(ogc_server_settings, "WMS_ENDPOINT") or "ows"

    thumbnail_url = f"{thumbnail_url}{wms_endpoint}?{'&'.join(f'{key}={val}' for key, val in params.items())}"

    return thumbnail_url


def fetch_wms(url: str, max_retries: int = 3, retry_delay: int = 1):
    """
    Function fetching an image from OGC server. The request is performed based on the WMS URL.
    In case access_token in not present in the URL , and Geoserver is used and the OGC backend, Basic Authentication
    is used instead. If image retrieval fails, function retries to fetch the image max_retries times, waiting
    retry_delay seconds between consecutive requests.

    :param url: WMS URL of the image
    :param max_retries: maximum number of retries before skipping retrieval
    :param retry_delay: number of seconds waited between retries
    :returns: retrieved image
    """

    # prepare authorization for WMS service
    headers = {}
    if "access_token" not in url:
        if url.startswith(settings.OGC_SERVER["default"]["LOCATION"]):
            # for the Geoserver backend, use Basic Auth, if access_token is not provided
            _user = settings.OGC_SERVER["default"].get("USER")
            _pwd = settings.OGC_SERVER["default"].get("PASSWORD")
            encoded_credentials = base64.b64encode(f"{_user}:{_pwd}".encode("UTF-8")).decode("ascii")
            headers["Authorization"] = f"Basic {encoded_credentials}"

    image = None

    for retry in range(max_retries):
        try:
            # fetch data
            resp, image = http_client.request(
                url, headers=headers, timeout=settings.OGC_SERVER["default"].get("TIMEOUT", 60)
            )

            # validate response
            if not resp or resp.status_code < 200 or resp.status_code > 299 or "ServiceException" in str(image):
                _status_code = resp.status_code if resp else 'Unknown'
                logger.debug(
                    f"Fetching partial thumbnail from {url} failed with status code: "
                    f"{_status_code} and response: {str(image)}"
                )
                image = None
                time.sleep(retry_delay)
                continue

        except Exception as e:
            if retry + 1 >= max_retries:
                logger.exception(e)

            time.sleep(retry_delay)
            continue
        else:
            break

    return image
