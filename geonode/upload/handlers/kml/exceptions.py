from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidKmlException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The kml provided is invalid"
    default_code = "invalid_kml"
    category = "importer"
