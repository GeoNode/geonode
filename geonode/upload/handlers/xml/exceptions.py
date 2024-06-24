from rest_framework.exceptions import APIException
from rest_framework import status


class InvalidXmlException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "The xml provided is invalid"
    default_code = "invalid_xml"
    category = "importer"
