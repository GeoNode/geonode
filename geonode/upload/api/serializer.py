#########################################################################
#
# Copyright (C) 2024 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################
from rest_framework import serializers
from dynamic_rest.serializers import DynamicModelSerializer
from geonode.base.api.serializers import BaseDynamicModelSerializer
from geonode.base.models import ResourceBase
from geonode.upload.models import UploadParallelismLimit, UploadSizeLimit


class ImporterSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "ImporterSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = (
            "base_file",
            "xml_file",
            "sld_file",
            "store_spatial_files",
            "skip_existing_layers",
            "action",
        )

    base_file = serializers.FileField()
    xml_file = serializers.FileField(required=False)
    sld_file = serializers.FileField(required=False)
    store_spatial_files = serializers.BooleanField(required=False, default=True)
    skip_existing_layers = serializers.BooleanField(required=False, default=False)
    action = serializers.CharField(required=True)


class OverwriteImporterSerializer(ImporterSerializer):
    class Meta:
        ref_name = "OverwriteImporterSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ImporterSerializer.Meta.fields + (
            "overwrite_existing_layer",
            "resource_pk",
        )

    overwrite_existing_layer = serializers.BooleanField(required=True)
    resource_pk = serializers.IntegerField(required=True)


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
