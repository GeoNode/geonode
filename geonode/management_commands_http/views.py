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
from rest_framework import permissions, status, views, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from geonode.base.api.pagination import GeoNodeApiPagination

from geonode.management_commands_http.mixins import CreateJobMixin
from geonode.management_commands_http.models import ManagementCommandJob
from geonode.management_commands_http.filters import ManagementCommandJobFilterSet
from geonode.management_commands_http.serializers import (
    ManagementCommandJobSerializer,
    ManagementCommandJobListSerializer,
    ManagementCommandJobCreateSerializer,
)
from geonode.management_commands_http.utils.commands import (
    get_management_command_details,
    get_management_commands,
)
from geonode.management_commands_http.utils.jobs import (
    start_task,
    stop_task,
    get_celery_task_meta,
)


class ManagementCommandView(views.APIView, CreateJobMixin):
    """
    Handle the exposed management commands usage:
      - GET: List of exposed commands
      - GET detail: Help for a specific command
      - POST: Create a job (and automatic runs) for a specific command.
    """

    permission_classes = [permissions.IsAdminUser]
    allowed_methods = ["GET", "POST"]

    def retrieve_details(self, cmd_name):
        # Object not found
        if cmd_name not in self.available_commands:
            return Response({"success": False, "error": "Command not found"}, status=status.HTTP_404_NOT_FOUND)

        # Object Details: fetch help text of the Command
        cmd_details = get_management_command_details(cmd_name)
        return Response({"success": True, "error": None, "data": cmd_details})

    def list(self):
        return Response({"success": True, "error": None, "data": self.available_commands})

    def get(self, request, cmd_name=None):
        self.available_commands = get_management_commands()
        # List
        if cmd_name is None:
            return self.list()
        # Retrieve
        return self.retrieve_details(cmd_name)

    def post(self, request, cmd_name=None):
        """
        Creates and runs a management command job.
        Expects application/json content type in a following shape:
        {
            "args": [<arg1>, <arg2>],
            "kwargs: {<key1>: <val1>, <key2>: <val2>},
            "autostart": bool
        }
        By default, autostart is set to true.
        """
        return self.create(request)

    def get_serializer(self, *args, **kwargs):
        kwargs["context"] = {"request": self.request, "view": self}
        return ManagementCommandJobCreateSerializer(*args, **kwargs)


class ManagementCommandJobViewSet(CreateJobMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Create, List, Retrieve, Start, Stop and Get Status of a Management Command Job.
    """

    permission_classes = [permissions.IsAdminUser]
    queryset = ManagementCommandJob.objects.all().order_by("-created_at")
    serializer_class = ManagementCommandJobSerializer
    filter_class = ManagementCommandJobFilterSet
    filter_backends = (DjangoFilterBackend,)
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        cmd_name = self.kwargs.pop("cmd_name", None)
        if cmd_name:
            queryset = queryset.filter(command=cmd_name)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            serializer = ManagementCommandJobListSerializer
        elif self.action in ("create", "metadata"):
            serializer = ManagementCommandJobCreateSerializer
        else:
            serializer = super().get_serializer_class()
        return serializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response({"data": serializer.data})

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["PATCH"])
    def start(self, request, pk=None, **kwargs):
        job = self.get_object()
        try:
            start_task(job)
        except ValueError as exc:
            error_message = str(exc)
            response = {"success": False, "error": error_message, "data": self.get_serializer().data}
            return Response(response, status=status.HTTP_400_BAD_REQUEST)
        job.refresh_from_db()
        serializer = self.get_serializer(instance=job)
        response = {"success": True, "error": None, "data": serializer.data}
        return Response(response)

    @action(detail=True, methods=["PATCH"])
    def stop(self, request, pk=None, **kwargs):
        job = self.get_object()
        stop_task(job)
        serializer = self.get_serializer(instance=job)
        response = {"success": True, "error": None, "data": serializer.data}
        return Response(response)

    @action(detail=True, methods=["GET"])
    def status(self, request, pk=None, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance)
        celery_task_meta = get_celery_task_meta(instance)
        celery_data = {
            "celery_task_meta": {
                "date_done": celery_task_meta.get("date_done"),
                "status": celery_task_meta.get("status"),
                "traceback": celery_task_meta.get("traceback"),
                "worker": celery_task_meta.get("worker"),
            }
        }
        return Response({**serializer.data, **celery_data})
