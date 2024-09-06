from rest_framework import serializers
from geonode.upload.handlers.common.serializer import RemoteResourceSerializer


class RemoteWMSSerializer(RemoteResourceSerializer):
    class Meta:
        model = RemoteResourceSerializer.Meta.model
        ref_name = "RemoteWMSSerializer"
        fields = RemoteResourceSerializer.Meta.fields + (
            "lookup",
            "bbox",
            "parse_remote_metadata",
        )

    lookup = serializers.CharField(required=True)
    bbox = serializers.ListField(required=False)
    parse_remote_metadata = serializers.BooleanField(required=False, default=False)
