import json
import logging
import os
from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.utils import UploadLimitValidator
from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from osgeo import ogr
from geonode.upload.utils import ImporterRequestAction as ira

from geonode.upload.handlers.geojson.exceptions import InvalidGeoJsonException

logger = logging.getLogger("importer")


class GeoJsonFileHandler(BaseVectorFileHandler):
    """
    Handler to import GeoJson files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    ACTIONS = {
        exa.IMPORT.value: (
            "start_import",
            "geonode.upload.import_resource",
            "geonode.upload.publish_resource",
            "geonode.upload.create_geonode_resource",
        ),
        exa.COPY.value: (
            "start_copy",
            "geonode.upload.copy_dynamic_model",
            "geonode.upload.copy_geonode_data_table",
            "geonode.upload.publish_resource",
            "geonode.upload.copy_geonode_resource",
        ),
        ira.ROLLBACK.value: (
            "start_rollback",
            "geonode.upload.rollback",
        ),
    }

    @property
    def supported_file_extension_config(self):
        return {
            "id": "geojson",
            "label": "GeoJSON",
            "format": "vector",
            "ext": ["json", "geojson"],
            "optional": ["xml", "sld"],
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
        if ext in ["json", "geojson"]:
            """
            Check if is a real geojson based on specification
            https://datatracker.ietf.org/doc/html/rfc7946#section-1.4
            """
            try:
                _file = base
                if isinstance(base, str):
                    with open(base, "r") as f:
                        _file = json.loads(f.read())
                else:
                    _file = json.loads(base.read())

                return _file.get("type", None) in ["FeatureCollection", "Feature"]

            except Exception:
                return False
        return False

    @staticmethod
    def is_valid(files, user):
        """
        Define basic validation steps:
        """
        # calling base validation checks
        BaseVectorFileHandler.is_valid(files, user)
        # getting the upload limit validation
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()

        _file = files.get("base_file")
        if not _file:
            raise InvalidGeoJsonException("base file is not provided")

        filename = os.path.basename(_file)

        if len(filename.split(".")) > 2:
            # means that there is a dot other than the one needed for the extension
            # if we keep it ogr2ogr raise an error, better to remove it
            raise InvalidGeoJsonException("Please remove the additional dots in the filename")

        try:
            with open(_file, "r") as _readed_file:
                json.loads(_readed_file.read())
        except Exception:
            raise InvalidGeoJsonException("The provided GeoJson is not valid")

        return True

    def get_ogr2ogr_driver(self):
        return ogr.GetDriverByName("GeoJSON")

    @staticmethod
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate):
        """
        Define the ogr2ogr command to be executed.
        This is a default command that is needed to import a vector file
        """

        base_command = BaseVectorFileHandler.create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate)
        return f"{base_command } -lco GEOMETRY_NAME={BaseVectorFileHandler().default_geometry_column_name}"
