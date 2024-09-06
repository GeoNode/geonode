from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer
from geonode.upload.models import Upload


class MetadataFileSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "MetadataFileSerializer"
        model = Upload
        view_name = "importer_upload"
        fields = ("dataset_title", "base_file", "source")

    base_file = serializers.FileField()
    dataset_title = serializers.CharField(required=True)
    source = serializers.CharField(required=False, default="resource_file_upload")
