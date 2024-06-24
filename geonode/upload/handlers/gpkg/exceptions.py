from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidGeopackageException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The geopackage provided is invalid"
    default_code = "invalid_gpkg"
    category = "importer"
