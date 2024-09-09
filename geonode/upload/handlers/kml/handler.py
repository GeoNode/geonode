import logging
import os

from geonode.resource.enumerator import ExecutionRequestAction as exa
from geonode.upload.api.exceptions import UploadParallelismLimitException
from geonode.upload.utils import UploadLimitValidator
from osgeo import ogr

from geonode.upload.handlers.common.vector import BaseVectorFileHandler
from geonode.upload.handlers.kml.exceptions import InvalidKmlException
from geonode.upload.utils import ImporterRequestAction as ira

logger = logging.getLogger("importer")



class KMLFileHandler(BaseVectorFileHandler):
    """
    Handler to import KML files into GeoNode data db
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
            "id": "kml",
            "label": "KML/KMZ",
            "format": "vector",
            "ext": ["kml", "kmz"],
        }

    @property
    def can_handle_xml_file(self) -> bool:
        """
        True or false if the handler is able to handle XML file
        By default a common workflow is always defined
        To be override if some expection are needed
        """
        return False

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        base = _data.get("base_file")
        if not base:
            return False
        return (
            base.endswith(".kml") or base.endswith(".kmz")
            if isinstance(base, str)
            else base.name.endswith(".kml") or base.name.endswith(".kmz")
        )

    @staticmethod
    def is_valid(files, user):
        """
        Define basic validation steps:
        Upload limit:
            - raise exception if the layer number of the gpkg is greater than the max upload per user
            - raise exception if the actual upload + the gpgk layer is greater than the max upload limit
        """
        # calling base validation checks
        BaseVectorFileHandler.is_valid(files, user)
        # getting the upload limit validation
        upload_validator = UploadLimitValidator(user)
        upload_validator.validate_parallelism_limit_per_user()
        actual_upload = upload_validator._get_parallel_uploads_count()
        max_upload = upload_validator._get_max_parallel_uploads()

        layers = KMLFileHandler().get_ogr2ogr_driver().Open(files.get("base_file"))

        if not layers:
            raise InvalidKmlException("The kml provided is invalid")

        layers_count = len(layers)

        if layers_count >= max_upload:
            raise UploadParallelismLimitException(
                detail=f"The number of layers in the kml {layers_count} is greater than "
                f"the max parallel upload permitted: {max_upload} "
                f"please upload a smaller file"
            )
        elif layers_count + actual_upload >= max_upload:
            raise UploadParallelismLimitException(
                detail=f"With the provided kml, the number of max parallel upload will exceed the limit of {max_upload}"
            )

        filename = os.path.basename(files.get("base_file"))

        if len(filename.split(".")) > 2:
            # means that there is a dot other than the one needed for the extension
            # if we keep it ogr2ogr raise an error, better to remove it
            raise InvalidKmlException("Please remove the additional dots in the filename")
        return True

    def get_ogr2ogr_driver(self):
        return ogr.GetDriverByName("KML")

    def handle_xml_file(self, saved_dataset, _exec):
        """
        Not implemented for KML, skipping
        """
        pass

    @staticmethod
    def create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate):
        """
        Define the ogr2ogr command to be executed.
        This is a default command that is needed to import a vector file
        """

        base_command = BaseVectorFileHandler.create_ogr2ogr_command(files, original_name, ovverwrite_layer, alternate)
        return f"{base_command } -lco GEOMETRY_NAME={BaseVectorFileHandler().default_geometry_column_name} --config OGR_SKIP LibKML"
