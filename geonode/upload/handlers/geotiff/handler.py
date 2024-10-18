#########################################################################
#
# Copyright (C) 2024 OSGeo
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
import os

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.handlers.common.raster import BaseRasterFileHandler
from geonode.upload.handlers.geotiff.exceptions import InvalidGeoTiffException
from geonode.upload.utils import ImporterRequestAction as ira

logger = logging.getLogger("importer")


class GeoTiffFileHandler(BaseRasterFileHandler):
    """
    Handler to import GeoTiff files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    TASKS = {
        exa.UPLOAD.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        ),
        exa.COPY.value: (
            "start_copy",
            "geonode.upload.copy_raster_file",
            "geonode.upload.publish_resource",
            "geonode.upload.copy_geonode_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
        ira.REPLACE.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        ),
    }

    @property
    def supported_file_extension_config(self):
        return {
            "id": "tiff",
            "formats": [
                {
                    "label": "TIFF",
                    "required_ext": ["tiff"],
                    "optional_ext": ["xml", "sld"],
                },
                {
                    "label": "TIF",
                    "required_ext": ["tif"],
                    "optional_ext": ["xml", "sld"],
                },
                {
                    "label": "GeoTIFF",
                    "required_ext": ["geotiff"],
                    "optional_ext": ["xml", "sld"],
                },
                {
                    "label": "GeoTIF",
                    "required_ext": ["geotif"],
                    "optional_ext": ["xml", "sld"],
                },
            ],
            "actions": list(self.TASKS.keys()),
            "type": "raster",
        }

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        base = _data.get("base_file")
        if not base:
            return False
        ext = base.split(".")[-1] if isinstance(base, str) else base.name.split(".")[-1]
        return ext in ["tiff", "geotiff", "tif", "geotif"] and _data.get("action", None) in GeoTiffFileHandler.TASKS

    @staticmethod
    def is_valid(files, user, **kwargs):
        """
        Define basic validation steps:
        """
        # calling base validation checks
        BaseRasterFileHandler.is_valid(files, user)
        # getting the upload limit validation
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()

        _file = files.get("base_file")
        if not _file:
            raise InvalidGeoTiffException("base file is not provided")

        filename = os.path.basename(_file)

        if len(filename.split(".")) > 2:
            # means that there is a dot other than the one needed for the extension
            # if we keep it ogr2ogr raise an error, better to remove it
            raise InvalidGeoTiffException("Please remove the additional dots in the filename")
        return True
