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

import requests
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema_view, inline_serializer
from rest_framework import mixins, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from geoserver.catalog import FailedRequestError

from geonode.api.v3.exceptions import Conflict
from geonode.api.v3.schema import extend_v3_schema
from geonode.api.v3.viewsets import V3GenericViewSet, V3ModelViewSet
from geonode.sources.api.v3.exceptions import GeoServerUnavailable, SourceUnavailable
from geonode.sources.api.v3.filters import DataItemFilterSet
from geonode.sources.api.v3.serializers import (
    PublishResultSerializer,
    PublishSerializer,
    BrowseEntrySerializer,
    DataItemSerializer,
    SourceConnectionSerializer,
    SourceProviderSerializer,
)
from geonode.sources.models import DataItem
from geonode.sources.registry import source_provider_registry
from geonode.sources import utils

logger = logging.getLogger(__name__)


def unpublish(data_items):
    for _item in data_items:
        # an uninstalled provider has nothing published anymore, the row only goes
        if _provider := source_provider_registry.get(_item.source_provider):
            try:
                _provider.unpublish(_item)
            except (FailedRequestError, requests.RequestException) as e:
                # the data items stay: removing them would leave their layers behind
                logger.exception(e)
                raise GeoServerUnavailable("Could not remove the layer from GeoServer.") from e


@extend_schema_view(retrieve=extend_v3_schema(parameters=[OpenApiParameter("key", str, OpenApiParameter.PATH)]))
class SourceProviderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, V3GenericViewSet):
    """The installed providers, as known by the registry"""

    permission_classes = [IsAdminUser]
    serializer_class = SourceProviderSerializer
    lookup_field = "key"

    def get_base_queryset(self):
        # a list, not a queryset: providers are code
        return sorted(source_provider_registry.REGISTRY.values(), key=lambda _provider: _provider.key)

    def get_object(self):
        if not (_provider := source_provider_registry.get(self.kwargs[self.lookup_field])):
            raise NotFound()
        self.check_object_permissions(self.request, _provider)
        return _provider


class SourceConnectionViewSet(V3ModelViewSet):
    """Connections to the sources: each one is an AuthConfig whose type is a provider key"""

    permission_classes = [IsAdminUser]
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = SourceConnectionSerializer

    def get_base_queryset(self):
        return utils.source_connections().order_by("id")

    def perform_create(self, serializer):
        # the connection is registered only if its source can be reached: raising rolls the save back
        with transaction.atomic():
            _connection = serializer.save()
            _reachable, _reason = source_provider_registry.get(_connection.type).test_connection(_connection)
            if not _reachable:
                raise SourceUnavailable("Could not reach the source, the connection was not saved.")

    def perform_destroy(self, instance):
        # the AuthConfig may also authenticate resources or url patterns, deleting it would silently break them
        if instance.authconfigresources.exists() or instance.url_patterns.exists():
            raise Conflict("The connection is used by resources or URL patterns and cannot be deleted.")
        # the data items go with the connection: their layers first, the store with the last one
        unpublish(instance.data_items.all())
        instance.delete()

    @extend_v3_schema(
        request=None,
        responses=inline_serializer(
            "SourceConnectionTest", {"success": serializers.BooleanField(), "message": serializers.CharField()}
        ),
    )
    @action(detail=True, methods=["post"])
    def test(self, request, pk=None, *args, **kwargs):
        """Check that the source of the connection can be reached"""
        _connection = self.get_object()
        success, message = source_provider_registry.get(_connection.type).test_connection(_connection)
        return Response({"success": success, "message": message}, status=200)

    @extend_v3_schema(responses=BrowseEntrySerializer(many=True))
    @action(detail=True, methods=["get"], serializer_class=BrowseEntrySerializer)
    def browse(self, request, pk=None, *args, **kwargs):
        """What the connection exposes right now, nothing is stored"""
        try:
            # live: every page lists the source again, nothing is cached between pages
            _page = self.paginate_queryset(utils.browse_connection(self.get_object()))
        except RuntimeError as e:
            # GDAL or provider errors may expose server details, the client only gets a generic message
            logger.exception(e)
            raise SourceUnavailable("Could not browse the connection.") from e
        return self.get_paginated_response(self.get_serializer(_page, many=True).data)

    @extend_v3_schema(
        request=PublishSerializer,
        responses={201: DataItemSerializer(many=True), 202: PublishResultSerializer(many=True)},
    )
    # answers with the published items, never a page of them
    @action(detail=True, methods=["post"], pagination_class=None)
    def publish(self, request, pk=None, *args, **kwargs):
        """
        Publish the chosen entries as data items: 201 with the items, or 202 when the provider publishes some first
        (a PostgreSQL table becomes a data item once the local GeoServer serves it), listing each entry with its
        data item or the execution still publishing it
        """
        _connection = self.get_object()
        serializer = PublishSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            _items, _executions = utils.publish_entries(_connection, serializer.validated_data["uris"], request.user)
        except utils.UnknownEntryError:
            raise ValidationError({"uris": ["Some entries are not exposed by the connection."]})
        except RuntimeError as e:
            # GDAL or provider errors may expose server details, the client only gets a generic message
            logger.exception(e)
            raise SourceUnavailable("Could not browse the connection.") from e
        if _executions:
            _published = dict(_items.values_list("uri", "pk"))
            _data = [
                {"uri": _uri, "data_item": _published.get(_uri), "execution_id": _executions.get(_uri)}
                for _uri in sorted(set(serializer.validated_data["uris"]))
            ]
            return Response(PublishResultSerializer(_data, many=True).data, status=202)
        _fields = DataItemSerializer.default_field_names()
        _items = DataItemSerializer.setup_queryset(_items, _fields, request)
        return Response(DataItemSerializer(_items, many=True, only_fields=_fields).data, status=201)


class DataItemViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.DestroyModelMixin, V3GenericViewSet):
    """
    Data items published from the connections: the API reads and removes them.
    Removing one also removes its layer from the local GeoServer, never the upstream data
    """

    permission_classes = [IsAdminUser]
    serializer_class = DataItemSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_class = DataItemFilterSet

    def get_base_queryset(self):
        return DataItem.objects.order_by("title", "id")

    def perform_destroy(self, instance):
        unpublish([instance])
        instance.delete()
