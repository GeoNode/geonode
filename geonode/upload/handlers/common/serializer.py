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


class RemoteResourceSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "RemoteResourceSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ("url", "title", "type", "action", "overwrite_existing_layer")

    url = serializers.URLField(required=True, help_text="URL of the remote service / resource")
    title = serializers.CharField(required=True, help_text="Title of the resource. Can be None or Empty")
    type = serializers.CharField(
        required=True,
        help_text="Remote resource type, for example wms or 3dtiles. Is used by the handler to understand if can handle the resource",
    )
    action = serializers.CharField(required=True)

    overwrite_existing_layer = serializers.BooleanField(required=False, default=False)
