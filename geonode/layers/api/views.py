# -*- coding: utf-8 -*-
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

from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.layers.models import Layer

from .serializers import LayerSerializer
from .permissions import LayerPermissionsFilter

import logging

logger = logging.getLogger(__name__)


class LayerViewSet(DynamicModelViewSet):
    """
    API endpoint that allows layers to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, LayerPermissionsFilter
    ]
    queryset = Layer.objects.all()
    serializer_class = LayerSerializer
    pagination_class = GeoNodeApiPagination
