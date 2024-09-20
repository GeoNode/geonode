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
import time
import base64
import logging
from PIL import Image, ImageOps

from typing import List, Tuple, Callable, Union
from uuid import uuid4
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model

from geonode.base.auth import get_or_create_token
from geonode.thumbs.exceptions import ThumbnailError
from geonode.storage.manager import storage_manager

logger = logging.getLogger(__name__)

MISSING_THUMB = settings.MISSING_THUMBNAIL
BASE64_PATTERN = "data:image/(jpeg|png|jpg);base64"


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


def expand_bbox_to_ratio(
    bbox: List,
    target_width: int = settings.THUMBNAIL_SIZE["width"],
    target_height: int = settings.THUMBNAIL_SIZE["height"],
):
    """
    Function returning an expanded BBOX, ensuring it's ratio, based on the provided BBOX, and width and height
    of the target image.

    :param bbox: a dataset compliant BBOX in a certain CRS, in (xmin, xmax, ymin, ymax, 'EPSG:xxxx') order
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


def assign_missing_thumbnail(instance) -> None:
    """
    Function assigning None in thumbnail_url to a provided instance

    :param instance: instance of Dataset or Map models
    """
    instance.save_thumbnail("", image=None)


def get_map(
    ogc_server_location: str,
    layers: List,
    bbox: List,
    wms_version: str = settings.OGC_SERVER["default"].get("WMS_VERSION", "1.3.0"),
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
    from geonode.geoserver.helpers import ogc_server_settings

    if ogc_server_location is not None:
        thumbnail_url = ogc_server_location
    else:
        thumbnail_url = ogc_server_settings.LOCATION

    if thumbnail_url.startswith(ogc_server_settings.PUBLIC_LOCATION):
        thumbnail_url = thumbnail_url.replace(ogc_server_settings.PUBLIC_LOCATION, ogc_server_settings.LOCATION)

    wms_endpoint = ""
    additional_kwargs = {}
    if thumbnail_url == ogc_server_settings.LOCATION:
        # add access token to requests to Geoserver (logic based on the previous implementation)
        username = ogc_server_settings.credentials.username
        user = get_user_model().objects.filter(username=username).first()
        if user:
            access_token = get_or_create_token(user)
            if access_token and not access_token.is_expired():
                additional_kwargs["access_token"] = access_token.token

        # add WMS endpoint to requests to Geoserver
        wms_endpoint = getattr(ogc_server_settings, "WMS_ENDPOINT") or "ows"

    # prepare authorization for WMS service
    headers = {}
    if thumbnail_url.startswith(ogc_server_settings.LOCATION):
        if "access_token" not in additional_kwargs.keys():
            # for the Geoserver backend, use Basic Auth, if access_token is not provided
            _user, _pwd = ogc_server_settings.credentials
            encoded_credentials = base64.b64encode(f"{_user}:{_pwd}".encode("UTF-8")).decode("ascii")
            headers["Authorization"] = f"Basic {encoded_credentials}"
        else:
            headers["Authorization"] = f"Bearer {additional_kwargs['access_token']}"

    image = None
    for retry in range(max_retries):
        try:
            # fetch data
            image = getmap(
                f"{thumbnail_url}{wms_endpoint}",
                version=wms_version,
                headers=headers,
                layers=layers,
                styles=styles,
                srs=bbox[-1] if bbox else None,
                bbox=[bbox[0], bbox[2], bbox[1], bbox[3]] if bbox else None,
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


def _build_getmap_request(
    version="1.3.0",
    layers=None,
    styles=None,
    srs=None,
    bbox=None,
    format=None,
    size=None,
    time=None,
    dimensions={},
    elevation=None,
    transparent=False,
    bgcolor=None,
    exceptions=None,
    **kwargs,
):
    from owslib.crs import Crs

    request = {"service": "WMS", "version": version, "request": "GetMap"}

    # check layers and styles
    assert len(layers) > 0
    request["layers"] = ",".join(layers)
    if styles:
        assert len(styles) == len(layers)
        request["styles"] = ",".join(styles)
    else:
        request["styles"] = ""

    # size
    request["width"] = str(size[0])
    request["height"] = str(size[1])

    # remap srs to crs for the actual request
    if srs.upper() == "EPSG:0":
        # if it's esri's unknown spatial ref code, bail
        raise Exception(f"Undefined spatial reference ({srs}).")

    sref = Crs(srs)
    if sref.axisorder == "yx":
        # remap the given bbox
        bbox = (bbox[1], bbox[0], bbox[3], bbox[2])

    # remapping the srs to crs for the request
    request["crs"] = str(srs)
    request["bbox"] = ",".join([repr(x) for x in bbox])
    request["format"] = str(format)
    request["transparent"] = str(transparent).upper()
    request["bgcolor"] = f"0x{bgcolor[1:7]}"
    request["exceptions"] = str(exceptions)

    if time is not None:
        request["time"] = str(time)

    if elevation is not None:
        request["elevation"] = str(elevation)

    # any other specified dimension, prefixed with "dim_"
    for k, v in list(dimensions.items()):
        request[f"dim_{k}"] = str(v)

    if kwargs:
        for kw in kwargs:
            request[kw] = kwargs[kw]
    return request


def getmap(
    base_url,
    version="1.3.0",
    headers={},
    layers=None,
    styles=None,
    srs=None,
    bbox=None,
    format=None,
    size=None,
    time=None,
    elevation=None,
    dimensions={},
    transparent=False,
    bgcolor="#FFFFFF",
    exceptions="XML",
    method="Get",
    timeout=None,
    **kwargs,
):
    """Request and return an image from the WMS as a file-like object.

    Parameters
    ----------
    layers : list
        List of content layer names.
    styles : list
        Optional list of named styles, must be the same length as the
        layers list.
    srs : string
        A spatial reference system identifier.
        Note: this is an invalid query parameter key for 1.3.0 but is being
                retained for standardization with 1.1.1.
        Note: throws exception if the spatial ref is ESRI's "no reference"
                code (EPSG:0)
    bbox : tuple
        (left, bottom, right, top) in srs units (note, this order does not
            change depending on axis order of the crs).

        CRS:84: (long, lat)
        EPSG:4326: (lat, long)
    format : string
        Output image format such as 'image/jpeg'.
    size : tuple
        (width, height) in pixels.

    time : string or list or range
        Optional. Time value of the specified layer as ISO-8601 (per value)
    elevation : string or list or range
        Optional. Elevation value of the specified layer.
    dimensions: dict (dimension : string or list or range)
        Optional. Any other Dimension option, as specified in the GetCapabilities

    transparent : bool
        Optional. Transparent background if True.
    bgcolor : string
        Optional. Image background color.
    method : string
        Optional. HTTP DCP method name: Get or Post.
    **kwargs : extra arguments
        anything else e.g. vendor specific parameters

    Example
    -------
        wms = WebMapService('http://webservices.nationalatlas.gov/wms/1million',\
                                version='1.3.0')
        img = wms.getmap(layers=['airports1m'],\
                                styles=['default'],\
                                srs='EPSG:4326',\
                                bbox=(-176.646, 17.7016, -64.8017, 71.2854),\
                                size=(300, 300),\
                                format='image/jpeg',\
                                transparent=True)
        out = open('example.jpg.jpg', 'wb')
        out.write(img.read())
        out.close()

    """
    from owslib.etree import etree
    from owslib.namespaces import Namespaces
    from owslib.util import openURL, ServiceException, nspath

    n = Namespaces()

    request = _build_getmap_request(
        version=version,
        layers=layers,
        styles=styles,
        srs=srs,
        bbox=bbox,
        dimensions=dimensions,
        elevation=elevation,
        format=format,
        size=size,
        time=time,
        transparent=transparent,
        bgcolor=bgcolor,
        exceptions=exceptions,
        **kwargs,
    )

    data = urlencode(request)

    u = openURL(base_url, data, method, timeout=timeout, auth=None, headers=headers)

    # need to handle casing in the header keys
    headers = {}
    for k, v in list(u.info().items()):
        headers[k.lower()] = v

    # handle the potential charset def
    if headers.get("content-type", "").split(";")[0] in ["application/vnd.ogc.se_xml", "text/xml"]:
        se_xml = u.read()
        se_tree = etree.fromstring(se_xml)
        try:
            err_message = str(se_tree.find(nspath("ServiceException", n.get_namespace("ogc"))).text).strip()
        except Exception:
            err_message = se_xml
        raise ServiceException(err_message)
    return u


def thumb_path(filename):
    """Return the complete path of the provided thumbnail file accessible
    via Django storage API"""
    return os.path.join(settings.THUMBNAIL_LOCATION, filename)


def thumb_exists(filename):
    """Determine if a thumbnail file exists in storage"""
    return storage_manager.exists(thumb_path(filename))


def thumb_size(filepath):
    """Determine if a thumbnail file size in storage"""
    if storage_manager.exists(filepath):
        return storage_manager.size(filepath)
    elif os.path.exists(filepath):
        return os.path.getsize(filepath)
    return 0


def thumb_open(filename):
    """Returns file handler of a thumbnail on the storage"""
    return storage_manager.open(thumb_path(filename))


def get_thumbs():
    """Fetches a list of all stored thumbnails"""
    if not storage_manager.exists(settings.THUMBNAIL_LOCATION):
        return []
    subdirs, thumbs = storage_manager.listdir(settings.THUMBNAIL_LOCATION)
    return thumbs


def remove_thumb(filename):
    """Delete a thumbnail from storage"""
    path = thumb_path(filename)
    if storage_manager.exists(path):
        storage_manager.delete(path)


def remove_thumbs(name):
    """Removes all stored thumbnails that start with the same name as the
    file specified"""
    for thumb in get_thumbs():
        if thumb.startswith(name):
            remove_thumb(thumb)


def get_unique_upload_path(filename):
    """Generates a unique name from the given filename and
    creates a unique file upload path"""
    # create an upload path from a unique filename
    filename, ext = os.path.splitext(filename)
    unique_file_name = f"{filename}-{uuid4()}{ext}"
    upload_path = thumb_path(unique_file_name)
    return upload_path


def _decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    _thumbnail_format = "png"
    _invalid_padding = data.find(";base64,")
    if _invalid_padding:
        _thumbnail_format = data[data.find("image/") + len("image/") : _invalid_padding]
        data = data[_invalid_padding + len(";base64,") :]
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += b"=" * (4 - missing_padding)
    return (base64.b64decode(data), _thumbnail_format)


class ThumbnailAlgorithms:
    @staticmethod
    def fit(image: Image.Image, **kwargs):
        _default_thumb_size = settings.THUMBNAIL_SIZE
        centering = kwargs.get("centering", (0.5, 0.5))
        cover = ImageOps.fit(
            image, (_default_thumb_size["width"], _default_thumb_size["height"]), centering=centering
        ).convert("RGB")
        return cover

    @staticmethod
    def scale(img: Image.Image, **kwargs):
        trg_w = settings.THUMBNAIL_SIZE["width"]
        trg_h = settings.THUMBNAIL_SIZE["height"]

        src_w, src_w = img.size

        ratio = min(trg_w / src_w, trg_h / src_w)
        new_size = (int(src_w * ratio), int(src_w * ratio))
        scaled_img = img.resize(new_size, Image.Resampling.BILINEAR)

        # Create a new image with the desired size and a white background
        resized_img = Image.new("RGB", (trg_w, trg_h), (255, 255, 255))

        # Paste the scaled image onto a properly sized new image
        paste_position = ((trg_w - new_size[0]) // 2, (trg_h - new_size[1]) // 2)
        resized_img.paste(scaled_img, paste_position)

        return resized_img
