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
from rest_framework import serializers
from geonode.management_commands_http.models import ManagementCommandJob


class ManagementCommandJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ManagementCommandJob
        fields = [
            'id',
            'command',
            'app_name',
            'user',
            'status',
            'created_at',
            'start_time',
            'end_time',
            'args',
            'kwargs',
            'celery_result_id',
            'output_message',
        ]
