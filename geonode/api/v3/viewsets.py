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
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import SAFE_METHODS

from geonode.api.v3.constants import CONTEXT_KEY, FIELDS_PARAM
from geonode.api.v3.pagination import V3Pagination
from geonode.api.v3.schema import V3AutoSchema

_UNSET = object()


class FieldSelectionMixin:
    """Implements the ``?fields=`` contract on both the serializer and the queryset.

    Subclasses describe what each serializer field costs to produce::

        field_query_hints = {
            "members": {"prefetch": ["groupmember_set__user"]},
            "group": {"select": ["group"]},
        }

    Joins listed here are applied only when the field is actually being
    returned. ``base_select_related`` / ``base_prefetch_related`` are applied
    unconditionally, for relations the serializer always needs.

    Pruning the serializer alone would leave the joins in place, which is the
    problem v3 exists to solve, so the two are deliberately driven from one map.
    """

    field_query_hints = {}
    base_select_related = ()
    base_prefetch_related = ()

    _requested_fields_cache = _UNSET

    def get_requested_fields(self):
        """The validated ``?fields=`` set, or ``None`` when it does not apply.

        Returns ``None`` for unsafe methods so that writes always see the full
        serializer and keep validating required fields.
        """
        if self._requested_fields_cache is not _UNSET:
            return self._requested_fields_cache

        self._requested_fields_cache = self._parse_requested_fields()
        return self._requested_fields_cache

    def _parse_requested_fields(self):
        request = getattr(self, "request", None)
        if request is None or request.method not in SAFE_METHODS:
            return None

        raw = request.query_params.get(FIELDS_PARAM)
        if not raw:
            return None

        requested = {name.strip() for name in raw.split(",") if name.strip()}
        if not requested:
            return None

        serializer_class = self.get_serializer_class()
        if not hasattr(serializer_class, "available_field_names"):
            return None

        available = serializer_class.available_field_names()
        unknown = sorted(requested - available)
        if unknown:
            # The message must be wrapped in a list. geonode_exception_handler's
            # _extract_detail() walks a dict detail and calls .default_detail on
            # the dict itself when the value is a bare string, raising
            # AttributeError and turning a 400 into a 500.
            raise ValidationError(
                {FIELDS_PARAM: [f"Unknown field(s): {', '.join(unknown)}. Available: {', '.join(sorted(available))}."]}
            )
        return requested

    def get_serializer_context(self):
        context = super().get_serializer_context()
        requested = self.get_requested_fields()
        if requested is not None:
            context[CONTEXT_KEY] = requested
        return context

    def optimize_queryset(self, queryset):
        """Apply only the joins the current response actually needs."""
        if getattr(self, "action", None) not in ("list", "retrieve"):
            return queryset

        requested = self.get_requested_fields()
        select = set(self.base_select_related)
        prefetch = set(self.base_prefetch_related)

        for name, hints in self.field_query_hints.items():
            if requested is not None and name not in requested:
                continue
            select.update(hints.get("select", ()))
            prefetch.update(hints.get("prefetch", ()))

        if select:
            queryset = queryset.select_related(*sorted(select))
        if prefetch:
            queryset = queryset.prefetch_related(*sorted(prefetch))
        return queryset


class V3ModelViewSet(FieldSelectionMixin, viewsets.ModelViewSet):
    """Base viewset for v3.

    Subclasses override :meth:`get_base_queryset` rather than ``get_queryset``,
    so that the ``?fields=`` optimisation is never accidentally skipped.

    ``permission_classes`` is intentionally not defaulted here. ``REST_FRAMEWORK``
    sets no ``DEFAULT_PERMISSION_CLASSES``, so DRF would fall back to ``AllowAny``
    and a viewset that forgets to declare them would ship world-writable. Every
    v3 viewset must set it explicitly; :mod:`geonode.api.v3.tests.test_infrastructure`
    asserts that none is left unset.

    ``schema`` is set here rather than through DRF's ``DEFAULT_SCHEMA_CLASS``, so
    that drf-spectacular only applies where this class is used. See
    :mod:`geonode.api.v3.schema`.
    """

    pagination_class = V3Pagination
    schema = V3AutoSchema()

    def get_base_queryset(self):
        return super().get_queryset()

    def get_queryset(self):
        return self.optimize_queryset(self.get_base_queryset())
