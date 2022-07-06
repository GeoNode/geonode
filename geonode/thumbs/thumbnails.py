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
import logging

from io import BytesIO
from PIL import Image, UnidentifiedImageError
from typing import List, Union, Optional, Tuple

from django.conf import settings
from django.utils.module_loading import import_string

from geonode.documents.models import Document
from geonode.geoapps.models import GeoApp
from geonode.maps.models import Map, MapLayer
from geonode.layers.models import Dataset
from geonode.geoserver.helpers import ogc_server_settings
from geonode.utils import get_dataset_name, get_dataset_workspace
from geonode.thumbs import utils
from geonode.thumbs.exceptions import ThumbnailError

logger = logging.getLogger(__name__)


# this is the original implementation of create_gs_thumbnail()
def create_gs_thumbnail_geonode(instance, overwrite=False, check_bbox=False):
    """
    Create a thumbnail with a GeoServer request.
    """
    wms_version = getattr(ogc_server_settings, "WMS_VERSION") or "1.1.1"

    create_thumbnail(
        instance,
        wms_version=wms_version,
        overwrite=overwrite,
    )


def create_thumbnail(
    instance: Union[Dataset, Map],
    wms_version: str = settings.OGC_SERVER["default"].get("WMS_VERSION", "1.1.1"),
    bbox: Optional[Union[List, Tuple]] = None,
    forced_crs: Optional[str] = None,
    styles: Optional[List] = None,
    overwrite: bool = False,
    background_zoom: Optional[int] = None,
) -> None:
    """
    Function generating and saving a thumbnail of the given instance (Dataset or Map), which is composed of
    outcomes of WMS GetMap queries to the instance's datasets providers, and an outcome of querying background
    provider for thumbnail's background (by default Slippy Map provider).

    :param instance: instance of Dataset or Map models
    :param wms_version: WMS version of the query
    :param bbox: bounding box of the thumbnail in format: (west, east, south, north, CRS), where CRS is in format
                 "EPSG:XXXX"
    :param forced_crs: CRS which should be used to fetch data from WMS services in format "EPSG:XXXX". By default
                       all data is translated and retrieved in EPSG:3857, since this enables background fetching from
                       Slippy Maps providers. Forcing another CRS can cause skipping background generation in
                       the thumbnail
    :param styles: styles, which OGC server should use for rendering an image
    :param overwrite: overwrite existing thumbnail
    :param background_zoom: zoom of the XYZ Slippy Map used to retrieve background image,
                            if Slippy Map is used as background
    """

    instance.refresh_from_db()

    default_thumbnail_name = _generate_thumbnail_name(instance)
    mime_type = "image/png"
    width = settings.THUMBNAIL_SIZE["width"]
    height = settings.THUMBNAIL_SIZE["height"]

    if default_thumbnail_name is None:
        # instance is Map and has no datasets defined
        utils.assign_missing_thumbnail(instance)
        return

    # handle custom, uploaded thumbnails, which may have different extensions from the default thumbnail
    thumbnail_exists = False
    if instance.thumbnail_url:
        thumbnail_exists = utils.thumb_exists(instance.thumbnail_url.rsplit('/')[-1])

    if (thumbnail_exists or utils.thumb_exists(default_thumbnail_name)) and not overwrite:
        logger.debug(f"Thumbnail for {instance.name} already exists. Skipping thumbnail generation.")
        return

    # --- determine target CRS and bbox ---
    target_crs = forced_crs.upper() if forced_crs is not None else "EPSG:3857"

    compute_bbox_from_datasets = False
    is_map_with_datasets = False

    if isinstance(instance, Map):
        is_map_with_datasets = MapLayer.objects.filter(map=instance, local=True).exclude(dataset=None).exists()
    if bbox:
        bbox = utils.clean_bbox(bbox, target_crs)
    elif instance.ll_bbox_polygon:
        bbox = utils.clean_bbox(instance.ll_bbox, target_crs)
    else:
        compute_bbox_from_datasets = True

    # --- define dataset locations ---
    locations, datasets_bbox = _datasets_locations(instance, compute_bbox=compute_bbox_from_datasets, target_crs=target_crs)

    if compute_bbox_from_datasets and is_map_with_datasets:
        if not datasets_bbox:
            raise ThumbnailError(f"Thumbnail generation couldn't determine a BBOX for: {instance}.")
        else:
            bbox = datasets_bbox

    # --- expand the BBOX to match the set thumbnail's ratio (prevent thumbnail's distortions) ---
    bbox = utils.expand_bbox_to_ratio(bbox) if bbox else None

    # --- add default style ---
    if not styles and hasattr(instance, "default_style"):
        if instance.default_style:
            styles = [instance.default_style.name]

    # --- fetch WMS datasets ---
    partial_thumbs = []

    for ogc_server, datasets, _styles in locations:
        if isinstance(instance, Map) and len(datasets) == len(_styles):
            styles = _styles
        try:
            partial_thumbs.append(
                utils.get_map(
                    ogc_server,
                    datasets,
                    wms_version=wms_version,
                    bbox=bbox,
                    mime_type=mime_type,
                    styles=styles,
                    width=width,
                    height=height,
                )
            )
        except Exception as e:
            logger.error(f"Exception occurred while fetching partial thumbnail for {instance.title}.")
            logger.exception(e)

    if not partial_thumbs and is_map_with_datasets:
        utils.assign_missing_thumbnail(instance)
        raise ThumbnailError("Thumbnail generation failed - no image retrieved from WMS services.")

    # --- merge retrieved WMS images ---
    merged_partial_thumbs = Image.new("RGBA", (width, height), (255, 255, 255, 0))

    for image in partial_thumbs:
        if image:
            content = BytesIO(image)
            try:
                img = Image.open(content)
                img.verify()  # verify that it is, in fact an image
                img = Image.open(BytesIO(image))  # "re-open" the file (required after running verify method)
                merged_partial_thumbs.paste(img, mask=img.convert('RGBA'))
            except UnidentifiedImageError as e:
                logger.error(f"Thumbnail generation. Error occurred while fetching dataset image: {image}")
                logger.exception(e)

    # --- fetch background image ---
    try:
        BackgroundGenerator = import_string(settings.THUMBNAIL_BACKGROUND["class"])
        background = BackgroundGenerator(width, height).fetch(bbox, background_zoom) if bbox else None
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
    return instance.thumbnail_url


def _generate_thumbnail_name(instance: Union[Dataset, Map, Document, GeoApp]) -> Optional[str]:
    """
    Method returning file name for the thumbnail.
    If provided instance is a Map, and doesn't have any defined datasets, None is returned.

    :param instance: instance of Dataset or Map models
    :return: file name for the thumbnail
    :raises ThumbnailError: if provided instance is neither an instance of the Map nor of the Dataset
    """

    if isinstance(instance, Dataset):
        file_name = f"dataset-{instance.uuid}-thumb.png"

    elif isinstance(instance, Map):
        # if a Map is empty - nothing to do here
        if not instance.maplayers:
            logger.debug(f"Thumbnail generation skipped - Map {instance.title} has no defined datasets")
            return None

        file_name = f"map-{instance.uuid}-thumb.png"

    elif isinstance(instance, Document):
        file_name = f"document-{instance.uuid}-thumb.png"

    elif isinstance(instance, GeoApp):
        file_name = f"geoapp-{instance.uuid}-thumb.png"
    else:
        raise ThumbnailError(
            "Thumbnail generation didn't recognize the provided instance."
        )

    return file_name


def _datasets_locations(
    instance: Union[Dataset, Map], compute_bbox: bool = False, target_crs: str = "EPSG:3857"
) -> Tuple[List[List], List]:
    """
    Function returning a list mapping instance's datasets to their locations, enabling to construct a minimum
    number of  WMS request for multiple datasets of the same OGC source (ensuring datasets order for Maps)

    :param instance: instance of Dataset or Map models
    :param compute_bbox: flag determining whether a BBOX containing the instance should be computed,
                         based on instance's datasets
    :param target_crs: valid only when compute_bbox is True - CRS of the returned BBOX
    :return: a tuple with a list, which maps datasets to their locations in a correct datasets order
             e.g.
                [
                    ["http://localhost:8080/geoserver/": ["geonode:layer1", "geonode:layer2]]
                ]
             and a list optionally consisting of 5 elements containing west, east, south, north
             instance's boundaries and CRS
    """
    locations = []
    bbox = []
    if isinstance(instance, Dataset):
        locations.append(
            [
                instance.ows_url or ogc_server_settings.LOCATION,
                [instance.alternate],
                []
            ]
        )
        if compute_bbox:
            if instance.ll_bbox_polygon:
                bbox = utils.clean_bbox(instance.ll_bbox, target_crs)
            elif (
                    instance.bbox[-1].upper() != 'EPSG:3857'
                    and target_crs.upper() == 'EPSG:3857'
                    and utils.exceeds_epsg3857_area_of_use(instance.bbox)
            ):
                # handle exceeding the area of use of the default thumb's CRS
                bbox = utils.transform_bbox(utils.crop_to_3857_area_of_use(instance.bbox), target_crs)
            else:
                bbox = utils.transform_bbox(instance.bbox, target_crs)
    elif isinstance(instance, Map):
        for map_dataset in instance.maplayers.iterator():

            if not map_dataset.local and not map_dataset.ows_url:
                logger.warning(
                    "Incorrectly defined remote dataset encountered (no OWS URL defined)."
                    "Skipping it in the thumbnail generation."
                )
                continue

            name = get_dataset_name(map_dataset)
            store = map_dataset.store
            workspace = get_dataset_workspace(map_dataset)
            map_dataset_style = map_dataset.current_style

            if store and Dataset.objects.filter(store=store, workspace=workspace, name=name).exists():
                dataset = Dataset.objects.filter(store=store, workspace=workspace, name=name).first()
            elif workspace and Dataset.objects.filter(workspace=workspace, name=name).exists():
                dataset = Dataset.objects.filter(workspace=workspace, name=name).first()
            elif Dataset.objects.filter(alternate=map_dataset.name).exists():
                dataset = Dataset.objects.filter(alternate=map_dataset.name).first()
            else:
                logger.warning(f"Dataset for MapLayer {name} was not found. Skipping it in the thumbnail.")
                continue

            if dataset.subtype in ['tileStore', 'remote']:
                # limit number of locations, ensuring dataset order
                if len(locations) and locations[-1][0] == dataset.remote_service.service_url:
                    # if previous dataset's location is the same as the current one - append current dataset there
                    locations[-1][1].append(dataset.alternate)
                    # update the styles too
                    if map_dataset_style:
                        locations[-1][2].append(map_dataset_style)
                else:
                    locations.append([
                        dataset.remote_service.service_url,
                        [dataset.alternate],
                        [map_dataset_style] if map_dataset_style else []
                    ])
            else:
                # limit number of locations, ensuring dataset order
                if len(locations) and locations[-1][0] == settings.OGC_SERVER["default"]["LOCATION"]:
                    # if previous dataset's location is the same as the current one - append current dataset there
                    locations[-1][1].append(dataset.alternate)
                    # update the styles too
                    if map_dataset_style:
                        locations[-1][2].append(map_dataset_style)
                else:
                    locations.append([
                        settings.OGC_SERVER["default"]["LOCATION"],
                        [dataset.alternate],
                        [map_dataset_style] if map_dataset_style else []
                    ])

            if compute_bbox:
                if dataset.ll_bbox_polygon:
                    dataset_bbox = utils.clean_bbox(dataset.ll_bbox, target_crs)
                elif (
                        dataset.bbox[-1].upper() != 'EPSG:3857'
                        and target_crs.upper() == 'EPSG:3857'
                        and utils.exceeds_epsg3857_area_of_use(dataset.bbox)
                ):
                    # handle exceeding the area of use of the default thumb's CRS
                    dataset_bbox = utils.transform_bbox(utils.crop_to_3857_area_of_use(dataset.bbox), target_crs)
                else:
                    dataset_bbox = utils.transform_bbox(dataset.bbox, target_crs)

                if not bbox:
                    bbox = dataset_bbox
                else:
                    # dataset's BBOX: (left, right, bottom, top)
                    bbox = [
                        min(bbox[0], dataset_bbox[0]),
                        max(bbox[1], dataset_bbox[1]),
                        min(bbox[2], dataset_bbox[2]),
                        max(bbox[3], dataset_bbox[3]),
                    ]

    if bbox and len(bbox) < 5:
        bbox = list(bbox) + [target_crs]  # convert bbox to list, if it's tuple

    return locations, bbox
