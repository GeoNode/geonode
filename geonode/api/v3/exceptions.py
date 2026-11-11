#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from http import HTTPStatus

from django.core.exceptions import PermissionDenied
from django.http import Http404
from rest_framework import exceptions
from rest_framework.views import exception_handler

PROBLEM_CONTENT_TYPE = "application/problem+json"


class Conflict(exceptions.APIException):
    status_code = 409
    default_detail = "The request conflicts with the current state of the resource."
    default_code = "conflict"


def problem_details_handler(exc, context):
    """
    Renders the errors raised in v3 views as RFC 9457 Problem Details.
    Errors raised outside DRF (middlewares, unhandled exceptions) keep the Django rendering
    """
    # the Http404 message names the model, the client only gets the generic one
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied(*exc.args)
    response = exception_handler(exc, context)
    if response is None:
        return None
    # as in v2: with a Basic challenge the browser pops its login dialog on an expired session
    response.headers.pop("WWW-Authenticate", None)
    _problem = {"type": "about:blank", "title": HTTPStatus(response.status_code).phrase, "status": response.status_code}
    if isinstance(exc, exceptions.ValidationError):
        _problem |= {"detail": str(exceptions.ValidationError.default_detail), "code": "invalid", "errors": exc.detail}
    else:
        _problem |= {"detail": str(exc.detail), "code": exc.get_codes()}
    response.data = _problem
    _request = context.get("request")
    # the browsable API keeps its HTML, only JSON clients get the problem media type
    if getattr(getattr(_request, "accepted_renderer", None), "format", None) == "json":
        response.content_type = PROBLEM_CONTENT_TYPE
    return response
