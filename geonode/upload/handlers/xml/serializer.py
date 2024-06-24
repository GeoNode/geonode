from rest_framework import serializers
from rest_framework import serializers


class MetadataFileSerializer(serializers.Serializer):
    class Meta:
        ref_name = "MetadataFileSerializer"
        view_name = "importer_upload"
        fields = ("dataset_title", "base_file", "source")

    base_file = serializers.FileField()
    dataset_title = serializers.CharField(required=True)
    source = serializers.CharField(required=False, default="resource_file_upload")
