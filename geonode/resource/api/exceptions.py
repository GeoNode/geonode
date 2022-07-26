from rest_framework.exceptions import APIException


class ExecutionRequestException(APIException):
    status_code = 500
    default_detail = "error during handling the execution request"
    default_code = "executionrequest_exception"
    category = "executionrequest"
