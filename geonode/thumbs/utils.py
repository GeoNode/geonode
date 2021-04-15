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

from pyproj import Transformer, CRS
from owslib.wms import WebMapService
from typing import List, Tuple, Callable, Union

from django.conf import settings
from django.contrib.auth import get_user_model

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.base.auth import get_or_create_token
from geonode.thumbs.exceptions import ThumbnailError
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

    x_min, x_max, y_min, y_max, crs = bbox

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
        crs,
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
    return new_bbox


def assign_missing_thumbnail(instance: Union[Layer, Map]) -> None:
    """
    Function assigning settings.MISSING_THUMBNAIL to a provided instance

    :param instance: instance of Layer or Map models
    """
    instance.save_thumbnail("", image=None)


def get_map(
        ogc_server_location: str,
        layers: List,
        bbox: List,
        wms_version: str = settings.OGC_SERVER["default"].get("WMS_VERSION", "1.1.1"),
        mime_type: str = "image/png",
        styles: List = None,
        width: int = 240,
        height: int = 200,
        max_retries: int = 3,
        retry_delay: int = 1,
):
    """
    Function fetching an image from OGC server.
    For the requests to the configured OGC backend (ogc_server_settings.LOCATION) the function tries to generate
    an access_token and attach it to the URL.
    If access_token is not added ant the request is against Geoserver Basic Authentication is used instead.
    If image retrieval fails, function retries to fetch the image max_retries times, waiting
    retry_delay seconds between consecutive requests.

    :param ogc_server_location: OGC server URL
    :param layers: layers which should be fetched from the OGC server
    :param bbox: area's bounding box in format: [west, east, south, north, CRS]
    :param wms_version: WMS version of the query (default: 1.1.1)
    :param mime_type: mime type of the returned image
    :param styles: styles, which OGC server should use for rendering an image
    :param width: width of the returned image
    :param height: height of the returned image
    :param max_retries: maximum number of retries before skipping retrieval
    :param retry_delay: number of seconds waited between retries
    :returns: retrieved image
    """

    ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]

    if ogc_server_location is not None:
        thumbnail_url = ogc_server_location
    else:
        thumbnail_url = ogc_server_settings.LOCATION

    wms_endpoint = ""
    additional_kwargs = {}
    if thumbnail_url == ogc_server_settings.LOCATION:
        # add access token to requests to Geoserver (logic based on the previous implementation)
        username = ogc_server_settings.credentials.username
        user = get_user_model().objects.filter(username=username).first()
        if user:
            access_token = get_or_create_token(user)
            if access_token and not access_token.is_expired():
                additional_kwargs['access_token'] = access_token.token

        # add WMS endpoint to requests to Geoserver
        wms_endpoint = getattr(ogc_server_settings, "WMS_ENDPOINT") or "ows"

    # prepare authorization for WMS service
    headers = {}
    if "access_token" not in additional_kwargs.keys():
        if thumbnail_url.startswith(settings.OGC_SERVER["default"]["LOCATION"]):
            # for the Geoserver backend, use Basic Auth, if access_token is not provided
            _user = settings.OGC_SERVER["default"].get("USER")
            _pwd = settings.OGC_SERVER["default"].get("PASSWORD")
            encoded_credentials = base64.b64encode(f"{_user}:{_pwd}".encode("UTF-8")).decode("ascii")
            headers["Authorization"] = f"Basic {encoded_credentials}"

    wms = WebMapService(f"{thumbnail_url}{wms_endpoint}", version=wms_version, headers=headers)

    image = None
    for retry in range(max_retries):
        try:
            # fetch data
            image = wms.getmap(
                layers=layers,
                styles=styles,
                srs=bbox[-1],
                bbox=[bbox[0], bbox[2], bbox[1], bbox[3]],
                size=(width, height),
                format=mime_type,
                transparent=True,
                timeout=getattr(ogc_server_settings, "TIMEOUT", None),
                **additional_kwargs,
            )

            # validate response
            if not image or "ServiceException" in str(image.read()):
                raise ThumbnailError(
                    f"Fetching partial thumbnail from {thumbnail_url} failed with response: {str(image)}"
                )

        except Exception as e:
            if retry + 1 >= max_retries:
                logger.exception(e)
                return

            time.sleep(retry_delay)
            continue
        else:
            break

    return image.read()


def epsg_3857_area_of_use():
    """
    Shortcut function, returning area of use of EPSG:3857 (in EPSG:4326) in a layer compliant BBOX
    """
    epsg3857 = CRS.from_user_input('EPSG:3857')
    return [
        getattr(epsg3857.area_of_use, 'west'),
        getattr(epsg3857.area_of_use, 'east'),
        getattr(epsg3857.area_of_use, 'south'),
        getattr(epsg3857.area_of_use, 'north'),
        'EPSG:4326'
    ]


def crop_to_3857_area_of_use(bbox: List) -> List:

    # perform the comparison in EPSG:4326 (the pivot for EPSG:3857)
    bbox4326 = transform_bbox(bbox, target_crs='EPSG:4326')

    # get area of use of EPSG:3857 in EPSG:4326
    epsg3857_bounds_bbox = epsg_3857_area_of_use()

    bbox = []
    for coord, bound_coord in zip(bbox4326[:-1], epsg3857_bounds_bbox[:-1]):
        if abs(coord) > abs(bound_coord):
            logger.debug(
                "Thumbnail generation: cropping BBOX's coord to EPSG:3857 area of use."
            )
            bbox.append(bound_coord)
        else:
            bbox.append(coord)

    bbox.append('EPSG:4236')

    return bbox


def exceeds_epsg3857_area_of_use(bbox: List) -> bool:
    """
    Function checking if a provided BBOX extends the are of use of EPSG:3857. Comparison is performed after casting
    the BBOX to EPSG:4326 (pivot for EPSG:3857).

    :param bbox: a layer compliant BBOX in a certain CRS, in (xmin, xmax, ymin, ymax, 'EPSG:xxxx') order
    :returns: List of indicators whether BBOX's coord exceeds the area of use of EPSG:3857
    """

    # perform the comparison in EPSG:4326 (the pivot for EPSG:3857)
    bbox4326 = transform_bbox(bbox, target_crs='EPSG:4326')

    # get area of use of EPSG:3857 in EPSG:4326
    epsg3857_bounds_bbox = epsg_3857_area_of_use()

    exceeds = False
    for coord, bound_coord in zip(bbox4326[:-1], epsg3857_bounds_bbox[:-1]):
        if abs(coord) > abs(bound_coord):
            exceeds = True

    return exceeds
