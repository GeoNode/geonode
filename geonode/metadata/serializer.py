from rest_framework import serializers

from geonode.base.api.serializers import ResourceSettingsField, user_serializer
from dynamic_rest.fields.fields import DynamicRelationField

class MetadataModelSerializer(serializers.Serializer):

    def get_fields(self):
        """
        Dynamically retrieve fields
        """
        return {
            "title": serializers.CharField(),
            "abstract": serializers.CharField(required=False),
            "date": serializers.DateTimeField(required=False),
            #"owner": DynamicRelationField(user_serializer(), embed=True, read_only=True),
            "featured": ResourceSettingsField(required=False, read_only=False),
            "is_published": ResourceSettingsField(required=False, read_only=False),
            "is_approved": ResourceSettingsField(required=False, read_only=False),
        }
