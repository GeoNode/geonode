import logging

from geonode.resource.manager import resource_manager
from geonode.upload.handlers.common.metadata import MetadataFileHandler
from geonode.upload.handlers.xml.exceptions import InvalidXmlException
from owslib.etree import etree as dlxml

logger = logging.getLogger(__name__)


class XMLFileHandler(MetadataFileHandler):
    """
    Handler to import XML files into GeoNode data db
    It must provide the task_lists required to comple the upload
    """

    @property
    def supported_file_extension_config(self):
        return {
            "id": "xml",
            "label": "XML Metadata File",
            "format": "metadata",
            "ext": ["xml"],
            "mimeType": ["application/json"],
            "needsFiles": [
                "shp",
                "prj",
                "dbf",
                "shx",
                "csv",
                "tiff",
                "zip",
                "sld",
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
        return base.endswith(".xml") if isinstance(base, str) else base.name.endswith(".xml")

    @staticmethod
    def is_valid(files, user=None):
        """
        Define basic validation steps
        """
        # calling base validation checks
        try:
            with open(files.get("base_file")) as _xml:
                dlxml.fromstring(_xml.read().encode())
        except Exception as err:
            raise InvalidXmlException(f"Uploaded document is not XML or is invalid: {str(err)}")
        return True

    def handle_metadata_resource(self, _exec, dataset, original_handler):
        if original_handler.can_handle_xml_file:
            original_handler.handle_xml_file(dataset, _exec)
        else:
            _path = _exec.input_params.get("files", {}).get("xml_file", _exec.input_params.get("base_file", {}))
            resource_manager.update(
                None,
                instance=dataset,
                xml_file=_path,
                metadata_uploaded=True if _path else False,
                vals={"dirty_state": True},
            )
