#########################################################################
#
# Copyright (C) 2026 OSGeo
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
import requests
from osgeo import ogr, gdal

from django.conf import settings
from geonode.layers.models import Dataset
from geonode.upload.handlers.common.remote import BaseRemoteResourceHandler
from geonode.upload.api.exceptions import ImportException
from geonode.upload.orchestrator import orchestrator
from geonode.geoserver.helpers import set_attributes

logger = logging.getLogger("importer")


class RemoteFlatGeobufResourceHandler(BaseRemoteResourceHandler):

    @property
    def supported_file_extension_config(self):
        return {}

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        if "url" in _data and "flatgeobuf" in _data.get("type", "").lower():
            return True
        return False

    @staticmethod
    def is_valid_url(url, **kwargs):
        """
        Check if the URL is reachable and supports HTTP Range requests
        """
        logger.debug(f"Checking FlatGeobuf URL validity (HEAD): {url}")
        try:
            # Reachability check using HEAD
            head_res = requests.head(url, timeout=10, allow_redirects=True)
            logger.debug(f"HTTP HEAD status: {head_res.status_code}")
            head_res.raise_for_status()

            accept_ranges = head_res.headers.get("Accept-Ranges", "").lower()

            # Check for range request support
            if accept_ranges == "bytes":
                logger.debug("Server explicitly supports Accept-Ranges: bytes")
                return True

            # Some servers might not return Accept-Ranges in HEAD, so we try a small range request
            logger.debug("Accept-Ranges header missing, trying a small Range GET...")
            range_res = requests.get(url, headers={"Range": "bytes=0-1"}, timeout=10, stream=True)
            logger.debug(f"Range GET status: {range_res.status_code}")
            try:
                if range_res.status_code != 206:
                    raise ImportException(
                        "The remote server does not support HTTP Range requests, which are required for FlatGeobuf."
                    )
            finally:
                range_res.close()
        except Exception as e:
            logger.debug(f"is_valid_url ERROR: {str(e)}")
            logger.exception(e)
            if isinstance(e, ImportException):
                raise e
            raise ImportException("Error checking FlatGeobuf URL")

        return True

    def create_geonode_resource(
        self,
        layer_name: str,
        alternate: str,
        execution_id: str,
        resource_type: Dataset = Dataset,
        asset=None,
    ):
        """
        Base function to create the resource into geonode.
        Extracts metadata from remote FlatGeobuf using OGR via HTTP range requests.
        """
        logger.debug(f"Entering create_geonode_resource for {layer_name}")
        _exec = orchestrator.get_execution_object(execution_id)
        params = _exec.input_params.copy()
        url = params.get("url")

        # Extract metadata via OGR VSICURL
        ogr.UseExceptions()
        logger.debug(f"Attempting to open FlatGeobuf with OGR: /vsicurl/{url}")
        try:
            # Set GDAL config options for faster failure
            gdal.SetConfigOption("GDAL_HTTP_TIMEOUT", "15")
            gdal.SetConfigOption("GDAL_HTTP_MAX_RETRY", "1")

            vsifile = f"/vsicurl/{url}"
            ds = ogr.Open(vsifile)
            if ds is None:
                logger.debug(f"OGR failed to open dataset: {vsifile}")
                raise ImportException(f"Could not open remote FlatGeobuf: {url}")

            logger.debug("OGR opened dataset. Extracting metadata...")

            # Get the first layer (FlatGeobuf typically has one layer)
            layer = ds.GetLayer(0)
            if layer is None:
                raise ImportException(f"No layers found in FlatGeobuf: {url}")

            # Get Projection/CRS
            srs = layer.GetSpatialRef()
            if srs:
                authority = srs.GetAuthorityName(None)
                code = srs.GetAuthorityCode(None) or srs.GetAuthorityCode("PROJCS") or srs.GetAuthorityCode("GEOGCS")

                if authority and code:
                    srid = f"{authority}:{code}"
                else:
                    logger.error(f"Could not identify EPSG code for FlatGeobuf: {url}")
                    raise ImportException(
                        "FlatGeobuf does not have a valid EPSG code. "
                        "Please ensure the file has proper spatial reference information."
                    )
            else:
                logger.error(f"No spatial reference system found in FlatGeobuf: {url}")
                raise ImportException(
                    "FlatGeobuf is missing spatial reference system (CRS). Please add CRS information to the file."
                )

            # Get BBox
            try:
                extent = layer.GetExtent()
                bbox = [extent[0], extent[2], extent[1], extent[3]]  # [minx, miny, maxx, maxy]
                logger.debug(f"Extracted bounding box: {bbox}")
            except Exception as e:
                logger.error(f"Could not extract bounding box from FlatGeobuf: {url}. Error: {e}")
                raise ImportException(
                    "Could not extract bounding box from FlatGeobuf. " "The file may be empty or corrupted."
                )

            # Get feature attributes
            layer_defn = layer.GetLayerDefn()
            attribute_map = []
            for i in range(layer_defn.GetFieldCount()):
                field_defn = layer_defn.GetFieldDefn(i)
                attribute_map.append([field_defn.GetName(), field_defn.GetTypeName()])

            logger.debug(f"Extracted schema with {len(attribute_map)} fields")
            logger.debug("OGR operations finished.")

            ds = None  # close dataset
        except Exception as e:
            logger.debug(f"OGR ERROR: {str(e)}")
            logger.exception(e)
            if isinstance(e, ImportException):
                raise e
            raise ImportException(f"Failed to extract metadata from FlatGeobuf: {url}")

        resource = super().create_geonode_resource(layer_name, alternate, execution_id, resource_type, asset)
        resource.set_bbox_polygon(bbox, srid)
        set_attributes(resource, attribute_map)

        return resource

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace, **kwargs):
        payload = super().generate_resource_payload(layer_name, alternate, asset, _exec, workspace, **kwargs)
        payload.update(
            {
                "name": alternate,
                "workspace": getattr(settings, "DEFAULT_WORKSPACE", "geonode"),
                "alternate": alternate,
            }
        )
        return payload
