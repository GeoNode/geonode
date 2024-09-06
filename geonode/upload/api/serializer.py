from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer
from geonode.upload.models import Upload


class ImporterSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "ImporterSerializer"
        model = Upload
        view_name = "importer_upload"
        fields = (
            "base_file",
            "xml_file",
            "sld_file",
            "store_spatial_files",
            "overwrite_existing_layer",
            "skip_existing_layers",
            "source",
        )

    base_file = serializers.FileField()
    xml_file = serializers.FileField(required=False)
    sld_file = serializers.FileField(required=False)
    store_spatial_files = serializers.BooleanField(required=False, default=True)
    overwrite_existing_layer = serializers.BooleanField(required=False, default=False)
    skip_existing_layers = serializers.BooleanField(required=False, default=False)
    source = serializers.CharField(required=False, default="upload")
