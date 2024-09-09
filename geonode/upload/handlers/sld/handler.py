import logging

from geonode.resource.manager import resource_manager
from geonode.upload.handlers.common.metadata import MetadataFileHandler
from geonode.upload.handlers.sld.exceptions import InvalidSldException
from owslib.etree import etree as dlxml

logger = logging.getLogger("importer")



class SLDFileHandler(MetadataFileHandler):
    """
    Handler to import SLD files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    @property
    def supported_file_extension_config(self):
        return {
            "id": "sld",
            "label": "Styled Layer Descriptor (SLD)",
            "format": "metadata",
            "ext": ["sld"],
            "mimeType": ["application/json"],
            "needsFiles": [
                "shp",
                "prj",
                "dbf",
                "shx",
                "csv",
                "tiff",
                "zip",
                "xml",
                "geojson",
            ],
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
        return base.endswith(".sld") if isinstance(base, str) else base.name.endswith(".sld")

    @staticmethod
    def is_valid(files, user):
        """
        Define basic validation steps
        """
        # calling base validation checks

        try:
            with open(files.get("base_file")) as _xml:
                dlxml.fromstring(_xml.read().encode())
        except Exception as err:
            raise InvalidSldException(f"Uploaded document is not SLD or is invalid: {str(err)}")
        return True

    def handle_metadata_resource(self, _exec, dataset, original_handler):
        if original_handler.can_handle_sld_file:
            original_handler.handle_sld_file(dataset, _exec)
        else:
            _path = _exec.input_params.get("files", {}).get("sld_file", _exec.input_params.get("base_file", {}))
            resource_manager.exec(
                "set_style",
                None,
                instance=dataset,
                sld_file=_exec.input_params.get("files", {}).get("sld_file", ""),
                sld_uploaded=True if _path else False,
                vals={"dirty_state": True},
            )
