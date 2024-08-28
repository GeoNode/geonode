
import enum
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import append_meta
from geonode.base.api.serializers import DownloadArrayLinkField


class GeoNodeOpenApiTypes(enum.Enum):
    #: Converted to ``{"type": "array", "items": {"type": "string"}}}``.
    ARRAY_STRING = enum.auto()


GeoNodeOpenApiMapping = {
    GeoNodeOpenApiTypes.ARRAY_STRING: {"type": "array", "items": {"type": "string"}},
}


class CustomOpenApiSchema(AutoSchema):
    def _map_serializer_field(self, field, direction, bypass_extensions=False):
        meta = self._get_serializer_field_meta(field, direction)

        if isinstance(field, DownloadArrayLinkField):
            return append_meta(dict(GeoNodeOpenApiMapping[GeoNodeOpenApiTypes.ARRAY_STRING]), meta)

        val = super()._map_serializer_field(field, direction, bypass_extensions=bypass_extensions)
        return val
