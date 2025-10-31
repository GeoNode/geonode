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
from geonode.resource.enumerator import ExecutionRequestAction as exa

from geonode.base.models import ResourceBase


class EmptyDatasetSerializer(DynamicModelSerializer):
    class Meta:
        ref_name = "EmptyDatasetSerializer"
        model = ResourceBase
        view_name = "importer_upload"
        fields = ("title", "geom", "attributes", "action", "is_empty", "is_dynamic_model_managed")

    title = serializers.CharField()
    geom = serializers.CharField()
    attributes = serializers.JSONField()
    action = serializers.CharField(required=False, default=exa.CREATE.value)
    is_empty = serializers.BooleanField(default=True, read_only=True, required=False)
    is_dynamic_model_managed = serializers.BooleanField(default=True, read_only=True, required=False)
