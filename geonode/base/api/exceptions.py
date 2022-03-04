from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler
from rest_framework import status


class GeneralUploadException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Upload error during resource upload'
    default_code = 'upload_exception'


class FileUploadLimitException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Total upload size exceeded. Please try again with smaller files.'
    default_code = 'total_upload_size_exceeded'


def geonode_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    response.data = {
        "success": False,
        "errors": [str(exc.detail) if hasattr(exc, "detail") else exc.default_detail],
        "code": exc.code if hasattr(exc, "code") else exc.default_code
    }
    return response
