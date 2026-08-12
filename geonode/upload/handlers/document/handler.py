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

from django.conf import settings

from geonode.documents.enumerations import DOCUMENT_MAGIC_MIMETYPE_MAP
from geonode.upload.handlers.common.document import BaseDocumentFileHandler
from geonode.upload.handlers.document.serializer import DocumentImporterSerializer
from geonode.upload.utils import ImporterRequestAction as ira

logger = logging.getLogger("importer")


class DocumentFileHandler(BaseDocumentFileHandler):
    """
    Handler to import documents into GeoNode
    It must provide the task_lists required to complete the upload
    """

    @property
    def supported_file_extension_config(self):
        # a document is not a dataset file type, nothing to expose to the client
        return {}

    @property
    def upload_validation_config(self):
        return {
            extension: {"mimes": mimes}
            for extension, mimes in DOCUMENT_MAGIC_MIMETYPE_MAP.items()
            if extension in settings.ALLOWED_DOCUMENT_TYPES
        }

    @staticmethod
    def can_handle(_data) -> bool:
        """
        This endpoint will return True or False if with the info provided
        the handler is able to handle the file or not
        """
        # a clone carries no file: it must go through the copy endpoint like every other resource,
        # never through this generic upload endpoint
        action = _data.get("action")
        return action in DocumentFileHandler.TASKS and action != ira.DOCUMENT_COPY.value

    @staticmethod
    def has_serializer(_data) -> bool:
        """
        This endpoint should return (if set) the custom serializer used in the API
        to validate the input resource
        """
        if DocumentFileHandler.can_handle(_data):
            return DocumentImporterSerializer
