from rest_framework.exceptions import APIException, _get_error_details
from rest_framework import status


class GeneralUploadException(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = 'Upload error during resource upload'
    default_code = 'upload_exception'

    def __init__(self, detail=None, code=None):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code

        if not isinstance(detail, dict) and not isinstance(detail, list):
            detail = [detail]

        self.detail = _get_error_details(detail, code)


class FileUploadLimitException(GeneralUploadException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Total upload size exceeded. Please try again with smaller files.'
    default_code = 'total_upload_size_exceeded'
