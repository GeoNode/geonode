#########################################################################
#
# Copyright (C) 2024 OSGeo
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

import enum
import logging
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.generators import SchemaGenerator
from drf_spectacular.types import OpenApiTypes, OPENAPI_TYPE_MAPPING
from drf_spectacular.plumbing import append_meta
from geonode.base.api.fields import DynamicRelationField
from geonode.base.api.serializers import SimpleHierarchicalKeywordSerializer
from django.core.cache import caches

logger = logging.getLogger(__file__)


class GeoNodeOpenApiTypes(enum.Enum):
    #: Converted to ``{"type": "array", "items": {"type": "string"}}}``.
    ARRAY_STRING = enum.auto()
    #: Converted to ``{"type": "array", "items": {"type": "object"}}}``.
    ARRAY_OBJECT = enum.auto()


GeoNodeOpenApiMapping = {
    GeoNodeOpenApiTypes.ARRAY_STRING: {"type": "array", "items": {"type": "string"}},
    GeoNodeOpenApiTypes.ARRAY_OBJECT: {"type": "array", "items": {"type": "object"}},
}


class CustomOpenApiSchema(AutoSchema):
    def _map_serializer_field(self, field, direction, bypass_extensions=False):
        meta = self._get_serializer_field_meta(field, direction)

        if isinstance(field, DynamicRelationField):
            try:
                # we check if is a complex field with a specific serializer
                serializer = field.serializer
                # if the serializer has more than one field, we assume that
                # returns an object (dict, list)
                if isinstance(serializer, SimpleHierarchicalKeywordSerializer) or len(serializer.fields.keys()) > 1:
                    return append_meta(dict(GeoNodeOpenApiMapping[GeoNodeOpenApiTypes.ARRAY_OBJECT]), meta)
                else:
                    # otherwise we can assume that is a string
                    return append_meta(dict(OPENAPI_TYPE_MAPPING[OpenApiTypes.STR]), meta)
            except Exception as e:
                # logger.exception(e)
                # if the serializer is not set, we can rollback to the default behaviour
                logger.info("Cannot identify type from serializer, rollback to default behaviour")
                pass

        val = super()._map_serializer_field(field, direction, bypass_extensions=bypass_extensions)
        return val


class CustomSchemaGenerator(SchemaGenerator):
    def get_schema(self, request=None, public=False):
        # TODO a signal or something should be implemented to clear the cache
        # if the metadata model is changed
        schema_cache = caches["openapi"]
        openapi_schema = schema_cache.get("openapi_schema")
        if openapi_schema is None:
            openapi_schema = super().get_schema(request, public)
            schema_cache.set("openapi_schema", openapi_schema, 3600)
        return openapi_schema
