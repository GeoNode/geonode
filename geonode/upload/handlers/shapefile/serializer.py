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
from geonode.base.models import ResourceBase


class ShapeFileSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "ShapeFileSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = (
            "base_file",
            "dbf_file",
            "shx_file",
            "prj_file",
            "xml_file",
            "sld_file",
            "store_spatial_files",
            "overwrite_existing_layer",
            "skip_existing_layers",
            "action",
        )

    base_file = serializers.FileField()
    dbf_file = serializers.FileField()
    shx_file = serializers.FileField()
    prj_file = serializers.FileField()
    xml_file = serializers.FileField(required=False)
    sld_file = serializers.FileField(required=False)
    store_spatial_files = serializers.BooleanField(required=False, default=True)
    overwrite_existing_layer = serializers.BooleanField(required=False, default=False)
    skip_existing_layers = serializers.BooleanField(required=False, default=False)
    action = serializers.CharField(required=True)


class OverwriteShapeFileSerializer(ShapeFileSerializer):
    class Meta:
        ref_name = "ShapeFileSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ShapeFileSerializer.Meta.fields + (
            "overwrite_existing_layer",
            "resource_pk",
        )

    overwrite_existing_layer = serializers.BooleanField(required=True)
    resource_pk = serializers.IntegerField(required=True)
