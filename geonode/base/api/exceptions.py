#########################################################################
#
# Copyright (C) 2022 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


def geonode_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    if response is not None and isinstance(exc, APIException):
        # for the upload exception we need a custom response
        detail = _extract_detail(exc)
        response.data = {
            "success": False,
            "errors": [str(detail)],
            "code": exc.code if hasattr(exc, "code") else exc.default_code
        }
    return response


def _extract_detail(exc, loop=False):
    if hasattr(exc, "detail"):
        if isinstance(exc.detail, list):
            return exc.detail[0]
        elif isinstance(exc.detail, dict):
            return _extract_detail(exc.detail, loop=True)
        else:
            return exc.detail
    elif loop:
        try:
            error = exc.get(list(exc)[0])
            if isinstance(error, list):
                return error[0]
        except Exception:
            return exc.default_detail
    return exc.default_detail
