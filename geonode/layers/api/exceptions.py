from rest_framework.exceptions import APIException


class LayerReplaceException(APIException):
    status_code = 500
    default_detail = 'Error during layer replace.'
    default_code = 'layer_replace_exception'
