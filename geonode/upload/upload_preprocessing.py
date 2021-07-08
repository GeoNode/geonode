#########################################################################
#
# Copyright (C) 2018 OSGeo
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

"""Tools for dealing with preprocessing operations in the upload process

These functions are executed before the data is sent to geoserver. They're
main purpose is to prepare the data so that it can be ingested.

"""

from collections import namedtuple
import logging
import os.path
import subprocess

from .files import get_type
from .utils import get_kml_doc

logger = logging.getLogger(__name__)

GdalBoundingBox = namedtuple("GdalBoundingBox", [
    "ulx",
    "uly",
    "lrx",
    "lry",
])


def convert_kml_ground_overlay_to_geotiff(kml_path, other_file_path):
    """Write a geotiff file to disk from the provided kml and image

    KML files that specify GroundOverlay as their type are accompanied by a
    raster file. Since there is no direct support in geoserver for this type
    of KML, we extract the relevant information from the KML file and convert
    the raster file to a geotiff.

    """

    with open(kml_path) as kml_handler:
        kml_bytes = kml_handler.read()
    kml_doc, namespaces = get_kml_doc(kml_bytes)
    bbox = GdalBoundingBox(
        ulx=_extract_bbox_param(kml_doc, namespaces, "west"),
        uly=_extract_bbox_param(kml_doc, namespaces, "north"),
        lrx=_extract_bbox_param(kml_doc, namespaces, "east"),
        lry=_extract_bbox_param(kml_doc, namespaces, "south"),
    )
    dirname, basename = os.path.split(other_file_path)
    output_path = os.path.join(
        dirname,
        ".".join((os.path.splitext(basename)[0], "tif"))
    )
    command = [
        "gdal_translate",
        "-of", "GTiff",
        "-a_srs", "EPSG:4326",  # KML format always uses EPSG:4326
        "-a_ullr", bbox.ulx, bbox.uly, bbox.lrx, bbox.lry,
        other_file_path,
        output_path
    ]
    subprocess.check_output(command)
    return output_path


def preprocess_files(spatial_files):
    """Pre-process the input spatial files.

    This function is used during the upload workflow. It is called before the
    data is sent to geoserver, thus providing a hook to perform custom
    pre-processing for specific types of files.

    :arg spatial_files: The files that are about to be uploaded to geoserver
    :type spatial_files: geonode.upload.files.SpatialFiles
    :returns: A list with the paths of the pre-processed files

    """

    result = []
    for spatial_file in spatial_files:
        if spatial_file.file_type == get_type("KML Ground Overlay"):
            auxillary_file = spatial_file.auxillary_files[0] if\
                len(spatial_file.auxillary_files) > 0 else None
            preprocessed = convert_kml_ground_overlay_to_geotiff(
                spatial_file.base_file, auxillary_file)
            result.append(preprocessed)
        else:
            result.extend(spatial_file.all_files())
    if spatial_files.archive is not None:
        result.append(spatial_files.archive)
    return result


def _extract_bbox_param(kml_doc, namespaces, param):
    return kml_doc.xpath(
        "kml:Document/kml:GroundOverlay/kml:LatLonBox/"
        f"kml:{param}/text()",
        namespaces=namespaces
    )[0]
