from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidSldException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The sld provided is invalid"
    default_code = "invalid_sld"
    category = "importer"
