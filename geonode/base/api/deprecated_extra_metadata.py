# #########################################################################
#
# Copyright (C) 2025 OSGeo
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
# #########################################################################
"""
Deprecated backward-compatible adapters for the ExtraMetadata API.

These adapters re-expose the old ``/extra_metadata/`` endpoint and the
``metadata`` serializer field using :class:`SparseField` as the storage
backend.  They are marked **deprecated** and should be removed after the
deprecation period.

To remove these adapters:
  1. Delete this file.
  2. Remove the ``metadata`` field and import from ``serializers.py``.
  3. Remove the ``extra_metadata`` action and import from ``views.py``.
"""

import json
import logging
import warnings

from deprecated import deprecated
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from dynamic_rest.fields.fields import DynamicComputedField

from geonode.base.models import ResourceBase
from geonode.metadata.models import SparseField

logger = logging.getLogger(__name__)

DEPRECATION_VERSION = "4.4.0"
DEPRECATION_REASON = (
    "The extra_metadata API is deprecated and will be removed in a future "
    "version. Use the sparse fields API instead."
)
SPARSE_FIELD_PREFIX = "extra_metadata_"
# SparseField.value is CharField(max_length=1024); entries exceeding this
# limit cannot be stored and are silently skipped with a log warning.
SPARSE_FIELD_VALUE_MAX_LENGTH = 1024


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sparse_fields_for_resource(resource):
    """Return SparseField entries that represent migrated ExtraMetadata."""
    return SparseField.objects.filter(
        resource=resource,
        name__startswith=SPARSE_FIELD_PREFIX,
    )


def _sparse_to_legacy(sparse_field):
    """Convert a SparseField into the old ExtraMetadata representation.

    Returns ``{"id": <pk>, ...metadata_dict}`` so existing consumers see the
    same shape they used to get.
    """
    try:
        metadata = json.loads(sparse_field.value) if sparse_field.value else {}
    except (json.JSONDecodeError, TypeError):
        metadata = {}
    return {**{"id": sparse_field.pk}, **metadata}


def _next_sparse_name(resource):
    """Generate the next available ``extra_metadata_<N>`` name."""
    existing = (
        SparseField.objects.filter(
            resource=resource,
            name__startswith=SPARSE_FIELD_PREFIX,
        )
        .order_by("-name")
        .values_list("name", flat=True)
    )
    max_n = 0
    for name in existing:
        suffix = name[len(SPARSE_FIELD_PREFIX):]
        try:
            max_n = max(max_n, int(suffix))
        except (ValueError, TypeError):
            pass
    return f"{SPARSE_FIELD_PREFIX}{max_n + 1}"


# ---------------------------------------------------------------------------
# Deprecated serializer field  (for ``metadata`` on ResourceBaseSerializer)
# ---------------------------------------------------------------------------


class DeprecatedExtraMetadataField(DynamicComputedField):
    """Deferred computed field that reconstructs the legacy ``metadata``
    representation from :class:`SparseField` entries.

    .. deprecated:: 4.4.0
       Use the sparse fields API instead.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @deprecated(version=DEPRECATION_VERSION, reason=DEPRECATION_REASON)
    def get_attribute(self, instance):
        warnings.warn(DEPRECATION_REASON, DeprecationWarning, stacklevel=2)
        try:
            qs = _sparse_fields_for_resource(instance)
            return [_sparse_to_legacy(sf) for sf in qs]
        except Exception as e:
            logger.exception(e)
            return []


# ---------------------------------------------------------------------------
# Deprecated extra_metadata view action mixin
# ---------------------------------------------------------------------------


class DeprecatedExtraMetadataMixin:
    """Mixin that adds the deprecated ``extra_metadata`` action back to a
    ``ViewSet``.

    Import this mixin and add it to your ViewSet's bases to restore the
    old ``/{pk}/extra_metadata/`` endpoint backed by SparseFields.

    .. deprecated:: 4.4.0
       Use the sparse fields API instead.
    """

    @extend_schema(
        methods=["get", "put", "delete", "post"],
        description=(
            "[DEPRECATED] Get/Update/Delete/Add extra metadata for a resource. "
            "Use the sparse fields API instead."
        ),
        deprecated=True,
    )
    @action(
        detail=True,
        methods=["get", "put", "delete", "post"],
        url_path=r"extra_metadata",
        url_name="extra-metadata",
    )
    def extra_metadata(self, request, pk, *args, **kwargs):
        """Deprecated endpoint – delegates to SparseField storage."""
        warnings.warn(DEPRECATION_REASON, DeprecationWarning, stacklevel=2)
        logger.warning(DEPRECATION_REASON)

        resource = ResourceBase.objects.filter(pk=pk).first()
        if resource is None:
            return Response({"detail": "Not found."}, status=404)

        if request.method == "GET":
            return self._extra_metadata_get(request, resource)
        elif request.method == "POST":
            return self._extra_metadata_post(request, resource)
        elif request.method == "PUT":
            return self._extra_metadata_put(request, resource)
        elif request.method == "DELETE":
            return self._extra_metadata_delete(request, resource)

    # -- GET ----------------------------------------------------------------

    @staticmethod
    def _extra_metadata_get(request, resource):
        qs = _sparse_fields_for_resource(resource)
        # Support the old query-param filtering (e.g. ?field_name=value)
        for key, value in request.query_params.items():
            # Old API used metadata__<key>=value JSONField lookups.
            # We approximate this by filtering on the JSON string.
            filtered = []
            for sf in qs:
                try:
                    meta = json.loads(sf.value) if sf.value else {}
                except (json.JSONDecodeError, TypeError):
                    continue
                if str(meta.get(key)) == str(value):
                    filtered.append(sf)
            qs = filtered
            break  # Old API only used the first filter pair

        if isinstance(qs, list):
            return Response([_sparse_to_legacy(sf) for sf in qs])
        return Response([_sparse_to_legacy(sf) for sf in qs.iterator()])

    # -- POST ---------------------------------------------------------------

    @staticmethod
    def _extra_metadata_post(request, resource):
        data = request.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return Response(
                    {"detail": "Invalid JSON payload."},
                    status=400,
                )

        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a JSON list of metadata objects."},
                status=400,
            )

        for meta_dict in data:
            if not isinstance(meta_dict, dict):
                continue
            meta_dict.pop("id", None)
            value = json.dumps(meta_dict)
            if len(value) > SPARSE_FIELD_VALUE_MAX_LENGTH:
                logger.warning(
                    "extra_metadata entry skipped: serialized value exceeds "
                    f"{SPARSE_FIELD_VALUE_MAX_LENGTH} characters"
                )
                continue
            name = _next_sparse_name(resource)
            SparseField.objects.create(
                resource=resource, name=name, value=value
            )

        result = [_sparse_to_legacy(sf) for sf in _sparse_fields_for_resource(resource)]
        return Response(result, status=201)

    # -- PUT ----------------------------------------------------------------

    @staticmethod
    def _extra_metadata_put(request, resource):
        data = request.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return Response(
                    {"detail": "Invalid JSON payload."},
                    status=400,
                )

        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a JSON list of metadata objects."},
                status=400,
            )

        for meta_dict in data:
            if not isinstance(meta_dict, dict):
                continue
            sf_id = meta_dict.pop("id", None)
            if sf_id is None:
                continue
            value = json.dumps(meta_dict)
            if len(value) > SPARSE_FIELD_VALUE_MAX_LENGTH:
                logger.warning(
                    "extra_metadata entry skipped: serialized value exceeds "
                    f"{SPARSE_FIELD_VALUE_MAX_LENGTH} characters"
                )
                continue
            SparseField.objects.filter(
                pk=sf_id,
                resource=resource,
                name__startswith=SPARSE_FIELD_PREFIX,
            ).update(value=value)

        result = [_sparse_to_legacy(sf) for sf in _sparse_fields_for_resource(resource)]
        return Response(result)

    # -- DELETE -------------------------------------------------------------

    @staticmethod
    def _extra_metadata_delete(request, resource):
        data = request.data
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return Response(
                    {"detail": "Invalid JSON payload."},
                    status=400,
                )

        if not isinstance(data, list):
            return Response(
                {"detail": "Expected a JSON list of IDs."},
                status=400,
            )

        ids = [int(i) for i in data if isinstance(i, (int, str)) and str(i).isdigit()]
        SparseField.objects.filter(
            pk__in=ids,
            resource=resource,
            name__startswith=SPARSE_FIELD_PREFIX,
        ).delete()

        result = [_sparse_to_legacy(sf) for sf in _sparse_fields_for_resource(resource)]
        return Response(result)
