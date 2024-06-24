from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidGeoJsonException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The geojson provided is invalid"
    default_code = "invalid_geojson"
    category = "importer"
