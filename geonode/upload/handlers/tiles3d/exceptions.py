from rest_framework.exceptions import APIException
from rest_framework import status


class Invalid3DTilesException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The 3dtiles provided is invalid"
    default_code = "invalid_3dtiles"
    category = "importer"
