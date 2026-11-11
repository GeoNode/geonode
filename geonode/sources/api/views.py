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
from django.db.models import Count
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from rest_framework.response import Response

from geonode.sources.api.serializers import (
    AdoptSerializer,
    DataItemSerializer,
    SourceConnectionSerializer,
    SourceProviderSerializer,
)
from geonode.sources.models import DataItem
from geonode.sources.registry import source_provider_registry
from geonode.sources import utils

logger = logging.getLogger(__name__)


class SourcesPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class SourcesViewSetMixin:
    permission_classes = [IsAdminUser]
    # the global default browsable renderer comes from dynamic-rest, this API is plain DRF
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]


class SourceProviderViewSet(SourcesViewSetMixin, viewsets.ViewSet):
    """The installed providers, as known by the registry"""

    lookup_field = "key"

    def list(self, request):
        _providers = sorted(source_provider_registry.REGISTRY.values(), key=lambda _provider: _provider.key)
        return Response(SourceProviderSerializer(_providers, many=True).data, status=200)

    def retrieve(self, request, key=None):
        if not (_provider := source_provider_registry.get(key)):
            raise NotFound()
        return Response(SourceProviderSerializer(_provider).data, status=200)


class SourceConnectionViewSet(SourcesViewSetMixin, viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = SourceConnectionSerializer
    pagination_class = SourcesPagination

    def get_queryset(self):
        return utils.source_connections().annotate(data_items_count=Count("data_items")).order_by("id")

    def create(self, request, *args, **kwargs):
        """Register the connection only if its source can be reached"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            _connection = serializer.save()
            _reachable, _reason = source_provider_registry.get(_connection.type).test_connection(_connection)
            if not _reachable:
                transaction.set_rollback(True)
                return Response({"detail": "Could not reach the source, the connection was not saved."}, status=502)
        return Response(self.get_serializer(_connection).data, status=201)

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

    @action(detail=True, methods=["get"])
    def browse(self, request, pk=None, *args, **kwargs):
        """What the connection exposes right now, nothing is stored"""
        try:
            return Response(utils.browse_connection(self.get_object()), status=200)
        except RuntimeError as e:
            # GDAL or provider errors may expose server details, the client only gets a generic message
            logger.exception(e)
            return Response({"detail": "Could not browse the connection."}, status=502)

    @action(detail=True, methods=["post"])
    def adopt(self, request, pk=None, *args, **kwargs):
        """Store the chosen entries of the connection as data items"""
        _connection = self.get_object()
        serializer = AdoptSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            _items = utils.adopt_entries(_connection, serializer.validated_data["uris"], request.user)
        except utils.UnknownEntryError:
            return Response({"uris": ["Some entries are not exposed by the connection."]}, status=400)
        except RuntimeError as e:
            # GDAL or provider errors may expose server details, the client only gets a generic message
            logger.exception(e)
            return Response({"detail": "Could not browse the connection."}, status=502)
        return Response(DataItemSerializer(_items, many=True).data, status=201)


class DataItemViewSet(
    SourcesViewSetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = DataItemSerializer
    pagination_class = SourcesPagination

    def get_queryset(self):
        _queryset = DataItem.objects.select_related("created_by").order_by("title", "id")
        if _connection := self.request.query_params.get("connection"):
            if not _connection.isdigit():
                raise ValidationError({"connection": ["The connection must be a numeric id."]})
            _queryset = _queryset.filter(auth_config_id=_connection)
        return _queryset
