#########################################################################
#
# Copyright (C) 2026 OSGeo
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
import logging

from django.db import transaction
from django.db.models import Count, Q
from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.sources.api.serializers import DataItemSerializer, SourceConnectionSerializer, SourceProviderSerializer
from geonode.sources.models import DataItem
from geonode.sources.registry import source_provider_registry
from geonode.sources import utils

logger = logging.getLogger(__name__)


class SourceProviderViewSet(viewsets.ViewSet):
    """The installed providers, as known by the registry"""

    permission_classes = [IsAdminUser]
    lookup_field = "key"

    def list(self, request):
        _providers = sorted(source_provider_registry.REGISTRY.values(), key=lambda _provider: _provider.key)
        return Response({"source_providers": SourceProviderSerializer(_providers, many=True).data}, status=200)

    def retrieve(self, request, key=None):
        if not (_provider := source_provider_registry.get(key)):
            raise NotFound()
        return Response({"source_provider": SourceProviderSerializer(_provider).data}, status=200)


class SourceConnectionViewSet(DynamicModelViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = SourceConnectionSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self, queryset=None):
        return (
            utils.source_connections()
            .annotate(data_items_count=Count("data_items", filter=Q(data_items__is_available=True)))
            .order_by("id")
        )

    def create(self, request, *args, **kwargs):
        """Register the connection and discover its data items at once: a source that cannot be read is not saved"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            with transaction.atomic():
                _connection = serializer.save()
                _discovery = utils.discover_connection(_connection, request.user)
        except RuntimeError as e:
            # GDAL or provider errors may expose server details, the client only gets a generic message
            logger.exception(e)
            return Response({"detail": "Could not browse the connection, it was not saved."}, status=502)
        return Response({**self.get_serializer(_connection).data, "discovery": _discovery}, status=201)

    def destroy(self, request, *args, **kwargs):
        _connection = self.get_object()
        # the AuthConfig may also authenticate resources or url patterns, deleting it would silently break them
        if _connection.authconfigresources.exists() or _connection.url_patterns.exists():
            return Response(
                {"detail": "The connection is used by resources or URL patterns and cannot be deleted."}, status=400
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def test(self, request, pk=None, *args, **kwargs):
        _connection = self.get_object()
        success, message = source_provider_registry.get(_connection.type).test_connection(_connection)
        return Response({"success": success, "message": message}, status=200)

    @action(detail=True, methods=["post"])
    def discover(self, request, pk=None, *args, **kwargs):
        """Store what the connection exposes as data items, refreshing the ones already known"""
        try:
            _result = utils.discover_connection(self.get_object(), request.user)
        except utils.EmptyDiscoveryError:
            return Response(
                {"detail": "The connection exposes nothing, check its parameters: the data items were left untouched."},
                status=400,
            )
        except RuntimeError as e:
            # GDAL or provider errors may expose server details, the client only gets a generic message
            logger.exception(e)
            return Response({"detail": "Could not browse the connection."}, status=502)
        return Response(_result, status=200)


class DataItemViewSet(DynamicModelViewSet):
    permission_classes = [IsAdminUser]
    http_method_names = ["get", "delete"]
    serializer_class = DataItemSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self, queryset=None):
        _queryset = DataItem.objects.select_related("created_by").order_by("title", "id")
        if _connection := self.request.query_params.get("connection"):
            if not _connection.isdigit():
                raise ValidationError({"connection": ["The connection must be a numeric id."]})
            _queryset = _queryset.filter(auth_config_id=_connection)
        return _queryset
