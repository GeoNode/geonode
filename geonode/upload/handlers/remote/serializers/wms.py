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
from geonode.upload.handlers.common.serializer import RemoteResourceSerializer


class RemoteWMSSerializer(RemoteResourceSerializer):
    class Meta:
        model = RemoteResourceSerializer.Meta.model
        ref_name = "RemoteWMSSerializer"
        fields = RemoteResourceSerializer.Meta.fields + (
            "lookup",
            "bbox",
            "parse_remote_metadata",
        )

    lookup = serializers.CharField(required=True)
    bbox = serializers.ListField(required=False)
    parse_remote_metadata = serializers.BooleanField(required=False, default=False)
