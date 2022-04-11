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
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.exceptions import AuthenticationFailed, NotFound
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.layers.api.exceptions import LayerReplaceException
from geonode.layers.models import Layer
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from geonode.layers.views import layer_replace

from .serializers import LayerSerializer
from .permissions import LayerPermissionsFilter

import logging

logger = logging.getLogger(__name__)


class LayerViewSet(DynamicModelViewSet):
    """
    API endpoint that allows layers to be viewed or edited.
    """
    http_method_names = ['get', 'patch', 'put']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, LayerPermissionsFilter
    ]
    queryset = Layer.objects.all().order_by('-last_updated')
    serializer_class = LayerSerializer
    pagination_class = GeoNodeApiPagination

    @extend_schema(
        methods=["put"],
        responses={200},
        description="API endpoint allowing to replace a layer."
    )
    @action(
        detail=False,
        url_path="(?P<layer_id>\d+)/replace",  # noqa
        url_name="replace-layer",
        methods=["put"]
    )
    def replace(self, request, layer_id=None):
        user = request.user
        if not user or not user.is_authenticated:
            raise AuthenticationFailed

        if not self.queryset.filter(id=layer_id).exists():
            raise NotFound(detail=f"Layer with ID {layer_id} is not available")

        alternate = self.queryset.get(id=layer_id).alternate

        response = layer_replace(request=request, layername=alternate)

        if response.status_code != 200:
            raise LayerReplaceException(detail=response.content)

        return response
