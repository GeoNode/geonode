from rest_framework import serializers

from geonode.base.api.serializers import BaseDynamicModelSerializer
from geonode.upload.models import UploadParallelismLimit, UploadSizeLimit
from dynamic_rest.serializers import DynamicModelSerializer


#class ImporterSerializer(DynamicModelSerializer):
class ImporterSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "ImporterSerializer"
        model = UploadParallelismLimit
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



class UploadSizeLimitSerializer(BaseDynamicModelSerializer):
    class Meta:
        model = UploadSizeLimit
        name = "upload-size-limit"
        view_name = "upload-size-limits-list"
        fields = (
            "slug",
            "description",
            "max_size",
            "max_size_label",
        )


class UploadParallelismLimitSerializer(BaseDynamicModelSerializer):
    class Meta:
        model = UploadParallelismLimit
        name = "upload-parallelism-limit"
        view_name = "upload-parallelism-limits-list"
        fields = (
            "slug",
            "description",
            "max_number",
        )
        read_only_fields = ("slug",)
