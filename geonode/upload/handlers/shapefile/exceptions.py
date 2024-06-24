from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidShapeFileException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The shapefile provided is invalid"
    default_code = "invalid_shapefile"
    category = "importer"
