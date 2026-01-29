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
from osgeo import gdal

from geonode.layers.models import Dataset
from geonode.upload.handlers.common.remote import BaseRemoteResourceHandler
from geonode.upload.api.exceptions import ImportException
from geonode.upload.orchestrator import orchestrator

logger = logging.getLogger("importer")


class RemoteCOGResourceHandler(BaseRemoteResourceHandler):

    @property
    def supported_file_extension_config(self):
        return {}

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        if "url" in _data and "cog" in _data.get("type", "").lower():
            return True
        return False

    @staticmethod
    def is_valid_url(url, **kwargs):
        """
        Check if the URL is reachable and supports HTTP Range requests
        """
        logger.debug(f"Checking COG URL validity (HEAD): {url}")
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
                        "The remote server does not support HTTP Range requests, which are required for COG."
                    )
            finally:
                range_res.close()
        except Exception as e:
            logger.debug(f"is_valid_url ERROR: {str(e)}")
            logger.exception(e)
            if isinstance(e, ImportException):
                raise e
            raise ImportException("Error checking COG URL")

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
        """
        logger.debug(f"Entering create_geonode_resource for {layer_name}")
        _exec = orchestrator.get_execution_object(execution_id)
        params = _exec.input_params.copy()
        url = params.get("url")

        # Extract metadata via GDAL VSICURL
        gdal.UseExceptions()
        logger.debug(f"Attempting to open COG with GDAL: /vsicurl/{url}")
        try:
            # Set GDAL config options for faster failure
            gdal.SetConfigOption("GDAL_HTTP_TIMEOUT", "15")
            gdal.SetConfigOption("GDAL_HTTP_MAX_RETRY", "1")

            vsiurl = f"/vsicurl/{url}"
            ds = gdal.OpenEx(vsiurl)
            if ds is None:
                logger.debug(f"GDAL failed to open dataset: {vsiurl}")
                raise ImportException(f"Could not open remote COG: {url}")

            if not ds.GetSpatialRef():
                raise ImportException(f"Could not extract spatial reference from COG: {url}")

            srid = self.identify_authority(ds)

            # Get BBox
            gt = ds.GetGeoTransform()
            width = ds.RasterXSize
            height = ds.RasterYSize

            # Check for rotation
            is_rotated = gt[2] != 0 or gt[4] != 0

            if is_rotated:
                logger.info("COG has rotation/skew - calculating envelope bbox")
                # Calculate all four corners
                corners = [
                    (gt[0], gt[3]),
                    (gt[0] + width * gt[1], gt[3] + width * gt[4]),
                    (gt[0] + width * gt[1] + height * gt[2], gt[3] + width * gt[4] + height * gt[5]),
                    (gt[0] + height * gt[2], gt[3] + height * gt[5]),
                ]
                xs = [x for x, y in corners]
                ys = [y for x, y in corners]
                bbox = [min(xs), min(ys), max(xs), max(ys)]
            else:
                # Simple calculation for north-up images
                minx = gt[0]
                maxy = gt[3]
                maxx = gt[0] + width * gt[1]
                miny = gt[3] + height * gt[5]
                bbox = [minx, miny, maxx, maxy]

            ds = None  # close dataset
            logger.debug("GDAL operations finished.")
        except Exception as e:
            logger.debug(f"GDAL ERROR: {str(e)}")
            logger.exception(e)
            if isinstance(e, ImportException):
                raise e
            raise ImportException(f"Failed to extract metadata from COG: {url}")
        resource = super().create_geonode_resource(layer_name, alternate, execution_id, resource_type, asset)
        resource.set_bbox_polygon(bbox, srid)
        return resource

    def generate_resource_payload(self, layer_name, alternate, asset, _exec, workspace, **kwargs):
        payload = super().generate_resource_payload(layer_name, alternate, asset, _exec, workspace, **kwargs)
        payload.update(
            {
                "name": alternate,
            }
        )
        return payload
