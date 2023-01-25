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
import rest_framework.permissions

from dynamic_rest.viewsets import DynamicModelViewSet, WithDynamicViewSetMixin
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from geonode.base.api.pagination import GeoNodeApiPagination

from .. import models
from . import serializers
from .mixins import UpdateListModelMixin

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


class HarvesterViewSet(NestedViewSetMixin, DynamicModelViewSet):
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


class HarvestableResourceViewSet(
    UpdateListModelMixin,
    NestedViewSetMixin,
    WithDynamicViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = models.HarvestableResource.objects.all()
    pagination_class = GeoNodeApiPagination
    serializer_class = serializers.HarvestableResourceSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        logger.debug(f"serializer_context: {context}")
        logger.debug(f"self.request: {self.request}")
        harvester = models.Harvester.objects.get(pk=self.kwargs["harvester_id"])
        context["harvester"] = harvester
        return context


class AsynchronousHarvestingSessionViewSet(WithDynamicViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = models.AsynchronousHarvestingSession.objects.all()
    serializer_class = serializers.BriefAsynchronousHarvestingSessionSerializer
    pagination_class = GeoNodeApiPagination
