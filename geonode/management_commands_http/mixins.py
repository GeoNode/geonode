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
from rest_framework import status
from rest_framework.response import Response

from geonode.management_commands_http.serializers import ManagementCommandJobSerializer
from geonode.management_commands_http.utils.jobs import start_task


class CreateJobMixin:
    def create(self, request, *args, **kwargs):
        # Inject "command" data from url kwargs
        serializer_data = {**request.data}
        if "command" not in serializer_data:
            serializer_data["command"] = self.kwargs.pop("cmd_name", None)

        # Create the job
        serializer = self.get_serializer(data=serializer_data)
        serializer.is_valid(raise_exception=True)
        job = self.perform_create(serializer)

        # Get latest job state from database. Some jobs can be already finished.
        job.refresh_from_db()

        # Response
        return Response(
            {
                "success": True,
                "error": None,
                "data": ManagementCommandJobSerializer(instance=job).data,
            },
            status=status.HTTP_201_CREATED,
        )

    def perform_create(self, serializer):
        autostart = serializer.validated_data.get("autostart", True)
        job = serializer.save()
        if autostart:
            start_task(job)
        return job
