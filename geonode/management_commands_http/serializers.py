#########################################################################
#
# Copyright (C) 2021 OSGeo
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
import json

from rest_framework import serializers
from geonode.management_commands_http.models import ManagementCommandJob
from geonode.management_commands_http.utils.commands import (
    get_management_commands_apps,
)


class ManagementCommandJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementCommandJob
        fields = [
            "id",
            "command",
            "app_name",
            "user",
            "status",
            "created_at",
            "start_time",
            "end_time",
            "args",
            "kwargs",
            "celery_result_id",
            "output_message",
        ]


class ManagementCommandJobListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementCommandJob
        fields = [
            "id",
            "command",
            "app_name",
            "user",
            "status",
            "created_at",
        ]


class ManagementCommandJobCreateSerializer(serializers.ModelSerializer):
    args = serializers.JSONField(required=False, default=[])
    kwargs = serializers.JSONField(required=False, default={})
    autostart = serializers.BooleanField(required=False, default=True)
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = ManagementCommandJob
        fields = [
            "command",
            "user",
            "args",
            "kwargs",
            "autostart",
        ]

    def __init__(self, *args, **kwargs):
        self.available_commands = get_management_commands_apps()
        super().__init__(*args, **kwargs)

    def validate_args(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('args must be a list')

        if "--help" in value:
            raise serializers.ValidationError('Forbidden argument: "--help"')

        value = json.dumps(value)
        return value

    def validate_kwargs(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError('kwargs must be a dict')

        value = json.dumps(value)
        return value

    def validate_command(self, value):
        if value not in self.available_commands:
            raise serializers.ValidationError("Command not found")

        return value

    def create(self, validated_data):
        validated_data.pop("autostart")
        validated_data["app_name"] = self.available_commands[validated_data["command"]]
        return super().create(validated_data)
