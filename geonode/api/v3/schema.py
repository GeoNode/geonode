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
"""
OpenAPI schema generation, scoped to v3.
drf-spectacular asserts that every view it walks carries its ``AutoSchema``: there is no global
``DEFAULT_SCHEMA_CLASS``, and ``exclude_non_v3_endpoints`` keeps only the v3 views
"""
import inspect
import logging

from drf_spectacular.contrib.rest_polymorphic import DjangoPolymorphicSerializerExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter, extend_schema

from geonode.api.v3.constants import FIELDS_PARAM

logger = logging.getLogger(__name__)

V3_PATH_PREFIX = "/api/v3/"
SCHEMA_PATH_PREFIX = "/api/v3/schema/"

# polymorphic.contrib.drf is not installed: the extension would only warn and fail --fail-on-warn
DjangoPolymorphicSerializerExtension.optional = True


def exclude_non_v3_endpoints(endpoints, **kwargs):
    """Keep the views under /api/v3/ carrying V3AutoSchema, any other is left out with a warning"""
    _kept = []
    for _endpoint in endpoints:
        _path, _callback = _endpoint[0], _endpoint[3]
        # the schema views live under /api/v3/ but describe the API, they are not part of it
        if not _path.startswith(V3_PATH_PREFIX) or _path.startswith(SCHEMA_PATH_PREFIX):
            continue
        if not issubclass(_schema_class(_callback), V3AutoSchema):
            logger.warning(f"{_path} is left out of the API v3 schema: its view is not a V3GenericViewSet")
            continue
        _kept.append(_endpoint)
    return _kept


def _schema_class(callback) -> type:
    # an action documented with extend_v3_schema carries its own schema class
    _schema = getattr(callback, "initkwargs", {}).get("schema") or getattr(
        getattr(callback, "cls", None), "schema", None
    )
    return _schema if inspect.isclass(_schema) else type(_schema)


class V3AutoSchema(AutoSchema):
    """Documents the ``?fields=`` parameter, which no generator can infer, and the stability of the endpoint"""

    def get_description(self):
        _description = super().get_description()
        if not (_stability := getattr(self.view, "stability", None)):
            return _description
        return "\n\n".join(_part for _part in (_description, f"Stability: {_stability}.") if _part)

    def get_extensions(self):
        _extensions = super().get_extensions()
        if _stability := getattr(self.view, "stability", None):
            _extensions = {**_extensions, "x-stability": _stability}
        return _extensions

    def get_override_parameters(self):
        _parameters = list(super().get_override_parameters())
        if self.method != "GET" or not hasattr(self.view, "get_requested_fields"):
            return _parameters

        _serializer_class = self.view.get_serializer_class()
        if not hasattr(_serializer_class, "available_field_names"):
            return _parameters

        _description = "Subset of the fields to return, unknown names are rejected with 400."
        if (_default := _serializer_class.default_field_names()) is not None:
            _description = f"{_description} Default: {', '.join(sorted(_default))}."
        _parameters.append(
            OpenApiParameter(
                name=FIELDS_PARAM,
                type=str,
                many=True,
                enum=sorted(_serializer_class.available_field_names()),
                style="form",
                explode=False,
                location=OpenApiParameter.QUERY,
                required=False,
                description=_description,
            )
        )
        return _parameters


def extend_v3_schema(**kwargs):
    """``extend_schema`` for the methods and actions of v3 viewsets"""

    def decorator(f):
        # drf-spectacular extends DEFAULT_SCHEMA_CLASS, which v3 leaves unset so that v2 is never inspected
        if not hasattr(f, "kwargs"):
            f.kwargs = {}
        f.kwargs.setdefault("schema", V3AutoSchema)
        return extend_schema(**kwargs)(f)

    return decorator
