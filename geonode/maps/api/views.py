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
from drf_spectacular.utils import extend_schema

from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.layers.api.serializers import LayerSerializer
from geonode.maps.models import Map

from .serializers import MapSerializer, MapLayerSerializer
from .permissions import MapPermissionsFilter

import logging

logger = logging.getLogger(__name__)


class MapViewSet(DynamicModelViewSet):
    """
    API endpoint that allows maps to be viewed or edited.
    """

    http_method_names = ['get', 'patch', 'post', 'put']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        MapPermissionsFilter,
    ]
    queryset = Map.objects.all().order_by('-last_updated')
    serializer_class = MapSerializer
    pagination_class = GeoNodeApiPagination

    @extend_schema(methods=['get'], responses={200: MapLayerSerializer(many=True)},
                   description="API endpoint allowing to retrieve the MapLayers list.")
    @action(detail=True, methods=['get'])
    def layers(self, request, pk=None):
        map = self.get_object()
        resources = map.layers
        return Response(MapLayerSerializer(embed=True, many=True).to_representation(resources))

    @extend_schema(methods=['get'], responses={200: LayerSerializer(many=True)},
                   description="API endpoint allowing to retrieve the local MapLayers.")
    @action(detail=True, methods=['get'])
    def local_layers(self, request, pk=None):
        map = self.get_object()
        resources = map.local_layers
        return Response(LayerSerializer(embed=True, many=True).to_representation(resources))
