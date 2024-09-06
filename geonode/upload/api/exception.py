from rest_framework import status
from rest_framework.exceptions import APIException


class ImportException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Exception during resource upload"
    default_code = "importer_exception"
    category = "importer"


class InvalidInputFileException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The provided files are invalid"
    default_code = "importer_exception"
    category = "importer"


class PublishResourceException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Error during the resource publishing"
    default_code = "publishing_exception"
    category = "importer"


class ResourceCreationException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Error during the creation of the geonode resource"
    default_code = "gn_resource_exception"
    category = "importer"


class CopyResourceException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Error during the copy of the geonode resource"
    default_code = "gn_resource_exception"
    category = "importer"


class StartImportException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Error during start of the import session"
    default_code = "start_import_exception"
    category = "importer"


class HandlerException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "base handler exception"
    default_code = "handler_exception"
    category = "handler"
