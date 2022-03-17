from rest_framework.exceptions import APIException


class DatasetReplaceException(APIException):
    status_code = 500
    default_detail = 'Error during dataset replace.'
    default_code = 'dataset_replace_exception'
    category = 'dataset_api'


class InvalidDatasetException(APIException):
    status_code = 500
    default_detail = "Input payload is not valid"
    default_code = "invalid_dataset_exception"
    category = 'dataset_api'
