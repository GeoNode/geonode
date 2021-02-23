import re
import time
import base64
import logging

from PIL import Image
from io import BytesIO
from typing import List, Union, Optional, Dict, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.module_loading import import_string

from geonode import geoserver

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.base.auth import get_or_create_token
from geonode.base.thumb_utils import thumb_exists
from geonode.geoserver.helpers import OGC_Servers_Handler
from geonode.utils import http_client, check_ogc_backend, get_layer_name, get_layer_workspace, bbox_to_projection
from geonode.thumbs import utils
from geonode.thumbs.exceptions import ThumbnailError


logger = logging.getLogger(__name__)


# this is the original implementation of create_gs_thumbnail()
def create_gs_thumbnail_geonode(instance, overwrite=False, check_bbox=False):
    """
    Create a thumbnail with a GeoServer request.
    """
    ogc_server_settings = OGC_Servers_Handler(settings.OGC_SERVER)["default"]
    wms_version = getattr(ogc_server_settings, "WMS_VERSION") or "1.1.0"
    default_thumb_size = getattr(settings, "THUMBNAIL_GENERATOR_DEFAULT_SIZE", {"width": 240, "height": 200})

    create_thumbnail(
        instance,
        wms_version=wms_version,
        overwrite=overwrite,
        width=default_thumb_size["width"],
        height=default_thumb_size["height"],
    )


def create_thumbnail(
    instance: Union[Layer, Map],
    wms_version: str = settings.OGC_SERVER["default"].get("WMS_VERSION", "1.1.0"),
    bbox: Optional[Union[List, Tuple]] = None,
    forced_crs: Optional[str] = None,
    styles: Optional[str] = None,
    overwrite: bool = False,
    width: int = 240,
    height: int = 200,
    background_zoom: Optional[int] = None,
) -> None:
    """
    Function generating and saving a thumbnail of the given instance (Layer or Map), which is composed of
    outcomes of WMS GetMap queries to the instance's layers providers, and an outcome of querying background
    provider for thumbnail's background (by default Slippy Map provider).

    :param instance: instance of Layer or Map models
    :param wms_version: WMS version of the query
    :param bbox: bounding box of the thumbnail in format: (west, east, south, north, CRS), where CRS is in format
                 "EPSG:XXXX"
    :param forced_crs: CRS which should be used to fetch data from WMS services in format "EPSG:XXXX". By default
                       all data is translated and retrieved in EPSG:3857, since this enables background fetching from
                       Slippy Maps providers. Forcing another CRS can cause skipping background generation in
                       the thumbnail
    :param styles: styles, which OGC server should use for rendering an image
    :param overwrite: overwrite existing thumbnail
    :param width: target width of a thumbnail in pixels
    :param height: target height of a thumbnail in pixels
    :param background_zoom: zoom of the XYZ Slippy Map used to retrieve background image,
                            if Slippy Map is used as background
    """

    instance.refresh_from_db()

    thumbnail_name = _generate_thumbnail_name(instance)
    mime_type = "image/png"

    if thumbnail_name is None:
        # instance is Map and has no layers defined
        utils.assign_missing_thumbnail(instance)
        return

    if thumb_exists(thumbnail_name) and not overwrite:
        logger.debug(f"Thumbnail for {instance.name} already exists. Skipping thumbnail generation.")
        return

    # --- determine target CRS and bbox ---
    target_crs = forced_crs if forced_crs is not None else "EPSG:3857"

    compute_bbox_from_layers = False
    if bbox:
        source_crs = bbox[-1]

        srid_regex = re.match(r"EPSG:\d{4}", source_crs)
        if not srid_regex:
            logger.error(f"Thumbnail bbox is in a wrong format: {bbox}")
            raise ThumbnailError("Wrong BBOX format")

        bbox = bbox_to_projection(bbox, target_srid=int(target_crs.split(":")[1]))
    else:
        compute_bbox_from_layers = True

    # --- define layer locations ---
    locations, layers_bbox = _layers_locations(
        instance, compute_bbox=compute_bbox_from_layers, target_srid=int(target_crs.split(":")[1])
    )

    if compute_bbox_from_layers:
        if not layers_bbox:
            raise ThumbnailError(f"Thumbnail generation couldn't determine a BBOX for {instance.name}.")
        else:
            bbox = layers_bbox

    # --- add default style ---
    if not styles and hasattr(instance, "default_style"):
        if instance.default_style:
            styles = instance.default_style.name

    # --- fetch WMS layers ---
    partial_thumbs = []

    for ogc_server, layers in locations.items():
        try:
            # construct WMS url for the thumbnail
            thumbnail_url = thumbnail_construct_wms_url(
                ogc_server,
                layers,
                wms_version=wms_version,
                bbox=bbox,
                mime_type=mime_type,
                styles=styles,
                width=width,
                height=height,
            )

            partial_thumbs.append(fetch_wms_thumb(thumbnail_url))

        except Exception as e:
            logger.error(f"Exception occurred while fetching partial thumbnail for {instance.name}.")
            logger.exception(e)

    if not partial_thumbs:
        utils.assign_missing_thumbnail(instance)
        raise ThumbnailError("Thumbnail generation failed - no image retrieved from WMS services.")

    # --- merge retrieved WMS images ---
    merged_partial_thumbs = Image.new("RGBA", (width, height), (0, 0, 0))

    for image in partial_thumbs:
        content = BytesIO(image)
        img = Image.open(content)
        img.verify()  # verify that it is, in fact an image

        img = Image.open(BytesIO(image))  # "re-open" the file (required after running verify method)
        merged_partial_thumbs.paste(img)

    # --- fetch background image ---
    try:
        BackgroundGenerator = import_string(settings.THUMBNAIL_GENERATOR_BACKGROUND_GENERATOR)
        background = BackgroundGenerator(width, height).fetch(bbox, background_zoom)
    except Exception as e:
        logger.error(f"Thumbnail generation: Error occurred while fetching background image {e}")
        background = None

    # --- overlay image with background ---
    thumbnail = Image.new("RGB", (width, height), (250, 250, 250))

    if background is not None:
        thumbnail.paste(background, (0, 0))

    thumbnail.paste(merged_partial_thumbs, (0, 0), merged_partial_thumbs)

    # convert image to the format required by save_thumbnail
    with BytesIO() as output:
        thumbnail.save(output, format="PNG")
        content = output.getvalue()

    # save thumbnail
    instance.save_thumbnail(thumbnail_name, image=content)


def thumbnail_construct_wms_url(
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

    thumbnail_url = thumbnail_url + f"{wms_endpoint}?" + "&".join(f"{key}={val}" for key, val in params.items())

    return thumbnail_url


def _generate_thumbnail_name(instance: Union[Layer, Map]) -> Optional[str]:
    """
    Method returning file name for the thumbnail.
    If provided instance is a Map, and doesn't have any defined layers, None is returned.

    :param instance: instance of Layer or Map models
    :return: file name for the thumbnail
    :raises ThumbnailError: if provided instance is neither an instance of the Map nor of the Layer
    """

    if isinstance(instance, Layer):
        file_name = "layer-%s-thumb.png" % instance.uuid

    elif isinstance(instance, Map):
        # if a Map is empty - nothing to do here
        if not instance.layers:
            logger.debug(f"Thumbnail generation skipped - Map {instance.name} has no defined layers")
            return None

        file_name = "map-%s-thumb.png" % instance.uuid
    else:
        raise ThumbnailError(
            "Thumbnail generation didn't recognize the provided instance: it's neither a Layer nor a Map."
        )

    return file_name


def _layers_locations(
    instance: Union[Layer, Map], compute_bbox: bool = False, target_srid: int = 3857
) -> Tuple[Dict, List]:
    """
    Function returning a dict mapping instance's layers to their locations, enabling to construct a single
    WMS request for multiple layers of the same OGC source.

    :param instance: instance of Layer or Map models
    :param compute_bbox: flag determining whether a BBOX containing the instance should be computed,
                         based on instance's layers
    :param target_srid: valid only when compute_bbox is True - SRID of the returned BBOX
    :return: a tuple with a dict, which maps layers to their locations
             (e.g. {"'http://localhost:8080/geoserver/'": ["geonode:nyc"]}),
             and a list of 5 elements containing (west, east, south, north) instance's boundaries and CRS
    """
    locations = {}
    bbox = []

    if isinstance(instance, Layer):

        # for local layers
        if instance.remote_service is None:
            locations[settings.OGC_SERVER["default"]["LOCATION"]] = [instance.alternate]
        # for remote layers
        else:
            locations[instance.remote_service.service_url] = [instance.alternate]

        if compute_bbox:
            bbox = bbox_to_projection(instance.bbox, target_srid)

    elif isinstance(instance, Map):

        for map_layer in instance.layers:

            if not map_layer.visibility:
                logger.debug("Skipping not visible layer in the thumbnail generation.")
                continue

            if not map_layer.local and not map_layer.ows_url:
                logger.warning(
                    "Incorrectly defined remote layer encountered (no OWS URL defined)."
                    "Skipping it in the thumbnail generation."
                )
                continue

            name = get_layer_name(map_layer)
            store = map_layer.store
            workspace = get_layer_workspace(map_layer)

            if store and Layer.objects.filter(store=store, workspace=workspace, name=name).count() > 0:
                layer = Layer.objects.filter(store=store, workspace=workspace, name=name).first()

            elif workspace and Layer.objects.filter(workspace=workspace, name=name).count() > 0:
                layer = Layer.objects.filter(workspace=workspace, name=name).first()

            elif Layer.objects.filter(alternate=map_layer.name).count() > 0:
                layer = Layer.objects.filter(alternate=map_layer.name).first()

            else:
                logger.warning(f"Layer for MapLayer {name} was not found. Skipping it in the thumbnail.")
                continue

            if layer.storeType == "remoteStore":
                locations.setdefault(layer.remote_service.service_url, []).append(layer.alternate)
            else:
                locations.setdefault(settings.OGC_SERVER["default"]["LOCATION"], []).append(layer.alternate)

            if compute_bbox:
                if not bbox:
                    bbox = bbox_to_projection(layer.bbox, target_srid)
                else:
                    layer_bbox = bbox_to_projection(layer.bbox, target_srid)
                    # layer's BBOX: (left, right, bottom, top)
                    bbox = [
                        min(bbox[0], layer_bbox[0]),
                        max(bbox[1], layer_bbox[1]),
                        min(bbox[2], layer_bbox[2]),
                        max(bbox[3], layer_bbox[3]),
                    ]

    if bbox:
        bbox += [f"EPSG:{target_srid}"]

    return locations, bbox


def fetch_wms_thumb(thumbnail_url: str, max_retries: int = 3, retry_delay: int = 1):
    """
    Function fetching an image from OGC server. The request is performed based on the WMS URL.
    In case access_token in not present in the URL , and Geoserver is used and the OGC backend, Basic Authentication
    is used instead. If image retrieval fails, function retries to fetch the image max_retries times, waiting
    retry_delay seconds between consecutive requests.

    :param thumbnail_url: WMS URL of the thumbnail
    :param max_retries: maximum number of retries before skipping retrieval
    :param retry_delay: number of seconds waited between retries
    :returns: retrieved image
    """

    # prepare authorization for WMS service
    headers = {}
    if "access_token" not in thumbnail_url:
        if check_ogc_backend(geoserver.BACKEND_PACKAGE):
            # for the Geoserver backend, use Basic Auth, if access_token is not provided
            _user = settings.OGC_SERVER["default"].get("USER")
            _pwd = settings.OGC_SERVER["default"].get("PASSWORD")
            encoded_credentials = base64.b64encode(f"{_user}:{_pwd}".encode("UTF-8")).decode("ascii")
            headers["Authorization"] = f"Basic {encoded_credentials}"

    image = None

    for retry in range(max_retries):
        try:
            # fetch WMS data
            resp, image = http_client.request(
                thumbnail_url, headers=headers, timeout=settings.OGC_SERVER["default"].get("TIMEOUT", 60)
            )

            # validate response
            if resp.status_code < 200 or resp.status_code > 299 or "ServiceException" in str(image):
                logger.debug(
                    f"Fetching partial thumbnail from {thumbnail_url} failed with status code: "
                    f"{resp.status_code} and response: {str(image)}"
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
