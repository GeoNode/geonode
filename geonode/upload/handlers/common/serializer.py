from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer
from geonode.upload.models import Upload


class RemoteResourceSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "RemoteResourceSerializer"
        model = Upload
        view_name = "importer_upload"
        fields = ("url", "title", "type", "source", "overwrite_existing_layer")

    url = serializers.URLField(required=True, help_text="URL of the remote service / resource")
    title = serializers.CharField(required=True, help_text="Title of the resource. Can be None or Empty")
    type = serializers.CharField(
        required=True,
        help_text="Remote resource type, for example wms or 3dtiles. Is used by the handler to understand if can handle the resource",
    )
    source = serializers.CharField(required=False, default="upload")

    overwrite_existing_layer = serializers.BooleanField(required=False, default=False)
