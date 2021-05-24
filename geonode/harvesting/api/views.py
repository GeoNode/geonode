#########################################################################
#
# Copyright (C) 2020 OSGeo
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

import rest_framework.permissions
from dynamic_rest.viewsets import (
    DynamicModelViewSet,
    WithDynamicViewSetMixin
)
from rest_framework.authentication import (
    BasicAuthentication,
    SessionAuthentication
)
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from geonode.base.api.pagination import GeoNodeApiPagination

from .. import models
from ..harvesters.base import BriefRemoteResource
from . import serializers

import logging

logger = logging.getLogger(__name__)


class IsAdminOrListOnly(rest_framework.permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_superuser:
            result = True
        elif view.action == "list":
            result = True
        else:
            result = False
        return result


class HarvesterViewSet(DynamicModelViewSet):
    authentication_classes = [
        BasicAuthentication,
        SessionAuthentication,
        OAuth2Authentication,
    ]
    permission_classes = [
        IsAdminOrListOnly,
    ]
    queryset = models.Harvester.objects.all()
    serializer_class = serializers.HarvesterSerializer
    pagination_class = GeoNodeApiPagination

    def get_serializer_class(self):
        if self.action == "list":
            result = serializers.BriefHarvesterSerializer
        else:
            result = serializers.HarvesterSerializer
        return result

    @action(
        detail=True,
        methods=["get",],
        url_name="harvestable-resources",
        url_path="harvestable-resources"
    )
    def harvestable_resources(self, request: Request, pk=None):
        """List harvestable resources for this harvester"""
        limit=request.query_params.get("limit")
        harvester = self.get_object()
        tracked_resources = harvester.harvestable_resources.values_list(
            "unique_identifier", flat=True)
        worker = harvester.get_harvester_worker()
        remote_resources = worker.list_resources()
        for resource in remote_resources:
            if resource.unique_identifier in tracked_resources:
                resource.should_be_harvested = True
        context = self.get_serializer_context()
        context["harvester"] = harvester
        logger.debug(f"Context before entering serializers: {context}")
        serializer = serializers.HarvestableResourceListSerializer(
            {"resources": remote_resources}, context=context)
        # serializer = serializers.HarvestableResourceSerializer(
        #     remote_resources, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @harvestable_resources.mapping.patch
    def modify_harvestable_resources(self, request: Request, pk=None):
        """Update the list of harvestable resources for this harvester"""
        harvester = self.get_object()
        logger.debug(f"request.data: {request.data}")
        context = self.get_serializer_context()
        context["harvester"] = harvester
        logger.debug(f"Context before entering serializers: {context}")
        serializer = serializers.HarvestableResourceListSerializer(
            data=request.data,
            context=context
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class HarvestingSessionViewSet(WithDynamicViewSetMixin, ReadOnlyModelViewSet):
    queryset = models.HarvestingSession.objects.all()
    serializer_class = serializers.BriefHarvestingSessionSerializer
    pagination_class = GeoNodeApiPagination