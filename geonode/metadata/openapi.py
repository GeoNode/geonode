import enum
import logging
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.types import OpenApiTypes, OPENAPI_TYPE_MAPPING
from drf_spectacular.plumbing import append_meta
from geonode.base.api.fields import DynamicRelationField
from geonode.base.api.serializers import SimpleHierarchicalKeywordSerializer

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
                logger.exception(e)
                # if the serializer is not set, we can rollback to the default behaviour
                logger.info("Cannot identify type from serializer, rollback to default behaviour")
                pass

        val = super()._map_serializer_field(field, direction, bypass_extensions=bypass_extensions)
        return val
