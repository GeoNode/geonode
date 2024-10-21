from rest_framework import serializers
from geonode.base.models import ResourceBase

class MetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceBase
        fields = [
                  "title",
                  "abstract",
                  "purpose",
                  "alternate",
                  "date_type",
                  "edition",
                  "attribution",
                  "doi",
                  "maintenance_frequency",
                  "constraints_other",
                  "language",
                  "supplemental_information",
                  "data_quality_statement",
                  "srid",
                  "metadata_uploaded",
                  "metadata_uploaded_preserve",
                  "featured",
                  "was_published",
                  "is_published",
                  "was_approved",
                  "is_approved",
                  "advertised",
                  "thumbnail_url",
                  "thumbnail_path",
                  "state",
                  "sourcetype",
                  "remote_typename",
                  "dirty_state",
                  "resource_type",
                  "metadata_only",
                  "subtype",
                  ]