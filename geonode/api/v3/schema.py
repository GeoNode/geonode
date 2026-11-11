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
"""OpenAPI schema generation, scoped to v3.

drf-spectacular's schema generator requires every included view to carry a
compatible ``AutoSchema`` instance, or it raises an assertion error while
walking the endpoint list. Two things keep the scope correct:

1. ``DEFAULT_SCHEMA_CLASS`` is not set globally in ``REST_FRAMEWORK``. Only
   :class:`~geonode.api.v3.viewsets.V3ModelViewSet` carries
   :class:`V3AutoSchema`.
2. :func:`exclude_non_v3_endpoints` runs as a ``PREPROCESSING_HOOK`` and drops
   everything outside ``/api/v3/`` before that assertion runs -- including the
   schema-serving routes themselves, which don't carry a spectacular
   ``AutoSchema`` either.

``test_schema.py`` asserts both properties.
"""
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.utils import OpenApiParameter
from rest_framework.permissions import SAFE_METHODS

from geonode.api.v3.constants import FIELDS_PARAM

V3_PATH_PREFIX = "/api/v3/"
SCHEMA_PATH_PREFIX = "/api/v3/schema/"


def exclude_non_v3_endpoints(endpoints, **kwargs):
    """Drop everything outside ``/api/v3/`` before the generator inspects it.

    The schema-serving routes are excluded too: ``SpectacularAPIView`` lives
    under ``/api/v3/`` but does not carry a spectacular ``AutoSchema``, so
    leaving it in trips the same assertion this function exists to avoid.
    """
    return [
        endpoint
        for endpoint in endpoints
        if endpoint[0].startswith(V3_PATH_PREFIX) and not endpoint[0].startswith(SCHEMA_PATH_PREFIX)
    ]


class V3AutoSchema(AutoSchema):
    """Adds the ``?fields=`` query parameter, which no generator can infer.

    ``fields`` varies the response shape at runtime, so it has to be declared by
    hand. The available field names are read off the serializer, which keeps the
    documented list from drifting away from the implementation.
    """

    def get_override_parameters(self):
        parameters = list(super().get_override_parameters())
        if self.method not in SAFE_METHODS:
            return parameters

        view = self.view
        if not hasattr(view, "get_requested_fields"):
            return parameters

        description = (
            "Comma-separated subset of fields to return. Unknown names are rejected with 400. "
            "Narrowing the field set also drops the joins those fields would have required."
        )
        available = self._available_field_names(view)
        if available:
            description = f"{description} Available: {', '.join(available)}."

        parameters.append(
            OpenApiParameter(
                name=FIELDS_PARAM,
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description=description,
            )
        )
        return parameters

    @staticmethod
    def _available_field_names(view):
        """Best effort: schema generation must never fail over a docstring detail."""
        try:
            serializer_class = view.get_serializer_class()
            return sorted(serializer_class.available_field_names())
        except Exception:  # noqa: BLE001 - generation must not break on introspection
            return []
