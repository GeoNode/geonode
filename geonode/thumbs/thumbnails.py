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

import re
import logging

from PIL import Image, UnidentifiedImageError
from io import BytesIO
from typing import List, Union, Optional, Tuple

from django.conf import settings
from django.utils.module_loading import import_string

from geonode.maps.models import Map
from geonode.layers.models import Layer
from geonode.base.thumb_utils import thumb_exists
from geonode.geoserver.helpers import OGC_Servers_Handler
from geonode.utils import get_layer_name, get_layer_workspace
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

    create_thumbnail(
        instance,
        wms_version=wms_version,
        overwrite=overwrite,
    )


def create_thumbnail(
    instance: Union[Layer, Map],
    wms_version: str = settings.OGC_SERVER["default"].get("WMS_VERSION", "1.1.0"),
    bbox: Optional[Union[List, Tuple]] = None,
    forced_crs: Optional[str] = None,
    styles: Optional[str] = None,
    overwrite: bool = False,
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

    default_thumbnail_name = _generate_thumbnail_name(instance)
    mime_type = "image/png"
    width = settings.THUMBNAIL_SIZE["width"]
    height = settings.THUMBNAIL_SIZE["height"]

    if default_thumbnail_name is None:
        # instance is Map and has no layers defined
        utils.assign_missing_thumbnail(instance)
        return

    # handle custom, uploaded thumbnails, which may have different extensions from the default thumbnail
    thumbnail_exists = False
    if instance.thumbnail_url and instance.thumbnail_url != settings.MISSING_THUMBNAIL:
        thumbnail_exists = thumb_exists(instance.thumbnail_url.rsplit('/')[-1])

    if (thumbnail_exists or thumb_exists(default_thumbnail_name)) and not overwrite:
        logger.debug(f"Thumbnail for {instance.name} already exists. Skipping thumbnail generation.")
        return

    # --- determine target CRS and bbox ---
    target_crs = forced_crs if forced_crs is not None else "EPSG:3857"

    compute_bbox_from_layers = False
    if bbox:
        source_crs = bbox[-1]

        srid_regex = re.match(r"EPSG:\d+", source_crs)
        if not srid_regex:
            logger.error(f"Thumbnail bbox is in a wrong format: {bbox}")
            raise ThumbnailError("Wrong BBOX format")

        bbox = utils.transform_bbox(bbox, target_crs=target_crs)
    else:
        compute_bbox_from_layers = True

    # --- define layer locations ---
    locations, layers_bbox = _layers_locations(instance, compute_bbox=compute_bbox_from_layers, target_crs=target_crs)

    if compute_bbox_from_layers:
        if not layers_bbox:
            raise ThumbnailError(f"Thumbnail generation couldn't determine a BBOX for: {instance}.")
        else:
            bbox = layers_bbox

    # --- expand the BBOX to match the set thumbnail's ratio (prevent thumbnail's distortions) ---
    bbox = utils.expand_bbox_to_ratio(bbox)

    # --- add default style ---
    if not styles and hasattr(instance, "default_style"):
        if instance.default_style:
            styles = instance.default_style.name

    # --- fetch WMS layers ---
    partial_thumbs = []

    for ogc_server, layers in locations:
        try:
            # construct WMS url for the thumbnail
            thumbnail_url = utils.construct_wms_url(
                ogc_server,
                layers,
                wms_version=wms_version,
                bbox=bbox,
                mime_type=mime_type,
                styles=styles,
                width=width,
                height=height,
            )

            logger.debug(f" -- fetching thumnail URL: {thumbnail_url}")
            partial_thumbs.append(utils.fetch_wms(thumbnail_url))
        except Exception as e:
            logger.error(f"Exception occurred while fetching partial thumbnail for {instance.name}.")
            logger.exception(e)

    if not partial_thumbs:
        utils.assign_missing_thumbnail(instance)
        raise ThumbnailError("Thumbnail generation failed - no image retrieved from WMS services.")

    # --- merge retrieved WMS images ---
    merged_partial_thumbs = Image.new("RGBA", (width, height), (0, 0, 0))

    for image in partial_thumbs:
        if image:
            content = BytesIO(image)
            try:
                img = Image.open(content)
                img.verify()  # verify that it is, in fact an image
                img = Image.open(BytesIO(image))  # "re-open" the file (required after running verify method)
                merged_partial_thumbs.paste(img)
            except UnidentifiedImageError as e:
                logger.error(f"Thumbnail generation. Error occurred while fetching layer image: {image}")
                logger.exception(e)

    # --- fetch background image ---
    try:
        BackgroundGenerator = import_string(settings.THUMBNAIL_BACKGROUND["class"])
        background = BackgroundGenerator(width, height).fetch(bbox, background_zoom)
    except Exception as e:
        logger.error(f"Thumbnail generation. Error occurred while fetching background image: {e}")
        logger.exception(e)
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
    instance.save_thumbnail(default_thumbnail_name, image=content)


def _generate_thumbnail_name(instance: Union[Layer, Map]) -> Optional[str]:
    """
    Method returning file name for the thumbnail.
    If provided instance is a Map, and doesn't have any defined layers, None is returned.

    :param instance: instance of Layer or Map models
    :return: file name for the thumbnail
    :raises ThumbnailError: if provided instance is neither an instance of the Map nor of the Layer
    """

    if isinstance(instance, Layer):
        file_name = f"layer-{instance.uuid}-thumb.png"

    elif isinstance(instance, Map):
        # if a Map is empty - nothing to do here
        if not instance.layers:
            logger.debug(f"Thumbnail generation skipped - Map {instance.title} has no defined layers")
            return None

        file_name = f"map-{instance.uuid}-thumb.png"
    else:
        raise ThumbnailError(
            "Thumbnail generation didn't recognize the provided instance: it's neither a Layer nor a Map."
        )

    return file_name


def _layers_locations(
    instance: Union[Layer, Map], compute_bbox: bool = False, target_crs: str = "EPSG:3857"
) -> Tuple[List[List], List]:
    """
    Function returning a list mapping instance's layers to their locations, enabling to construct a minimum
    number of  WMS request for multiple layers of the same OGC source (ensuring layers order for Maps)

    :param instance: instance of Layer or Map models
    :param compute_bbox: flag determining whether a BBOX containing the instance should be computed,
                         based on instance's layers
    :param target_crs: valid only when compute_bbox is True - CRS of the returned BBOX
    :return: a tuple with a list, which maps layers to their locations in a correct layers order
             e.g.
                [
                    ["http://localhost:8080/geoserver/": ["geonode:layer1", "geonode:layer2]]
                ]
             and a list optionally consisting of 5 elements containing west, east, south, north
             instance's boundaries and CRS
    """
    locations = []
    bbox = []

    if isinstance(instance, Layer):

        # for local layers
        if instance.remote_service is None:
            locations.append([settings.OGC_SERVER["default"]["LOCATION"], [instance.alternate]])
        # for remote layers
        else:
            locations.append([instance.remote_service.service_url, [instance.alternate]])

        if compute_bbox:
            bbox = utils.transform_bbox(instance.bbox, target_crs.lower())

    elif isinstance(instance, Map):

        map_layers = instance.layers.copy()
        # ensure correct order of layers in the map (higher stack_order are printed on top of lower)
        map_layers.sort(key=lambda l: l.stack_order)

        for map_layer in map_layers:

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
                # limit number of locations, ensuring layer order
                if len(locations) and locations[-1][0] == layer.remote_service.service_url:
                    # if previous layer's location is the same as the current one - append current layer there
                    locations[-1][1].append(layer.alternate)
                else:
                    locations.append([layer.remote_service.service_url, [layer.alternate]])
            else:
                # limit number of locations, ensuring layer order
                if len(locations) and locations[-1][0] == settings.OGC_SERVER["default"]["LOCATION"]:
                    # if previous layer's location is the same as the current one - append current layer there
                    locations[-1][1].append(layer.alternate)
                else:
                    locations.append([settings.OGC_SERVER["default"]["LOCATION"], [layer.alternate]])

            if compute_bbox:
                if not bbox:
                    bbox = utils.transform_bbox(layer.bbox, target_crs.lower())
                else:
                    layer_bbox = utils.transform_bbox(layer.bbox, target_crs.lower())
                    # layer's BBOX: (left, right, bottom, top)
                    bbox = [
                        min(bbox[0], layer_bbox[0]),
                        max(bbox[1], layer_bbox[1]),
                        min(bbox[2], layer_bbox[2]),
                        max(bbox[3], layer_bbox[3]),
                    ]

    if bbox and len(bbox) < 5:
        bbox = list(bbox) + [target_crs]  # convert bbox to list, if it's tuple

    return locations, bbox
