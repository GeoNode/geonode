from rest_framework.views import exception_handler


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
