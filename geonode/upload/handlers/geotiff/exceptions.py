from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidGeoTiffException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The tiff provided is invalid"
    default_code = "invalid_tiff"
    category = "importer"
