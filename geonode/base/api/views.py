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
from django.contrib.auth import get_user_model

from dynamic_rest.viewsets import DynamicModelViewSet
from rest_framework.permissions import IsAdminUser, IsAuthenticated  # noqa
from rest_framework.authentication import SessionAuthentication, BasicAuthentication

from geonode.base.models import ResourceBase
from .serializers import (
    UserSerializer,
    ResourceBaseSerializer
)
from .pagination import GeoNodeApiPagination

import logging

logger = logging.getLogger(__name__)


class UserViewSet(DynamicModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAdminUser,)
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer
    pagination_class = GeoNodeApiPagination

    def get_queryset(self):
        queryset = get_user_model().objects.all()
        # Set up eager loading to avoid N+1 selects
        queryset = self.get_serializer_class().setup_eager_loading(queryset)
        return queryset


class ResourceBaseViewSet(DynamicModelViewSet):
    """
    API endpoint that allows base resources to be viewed or edited.
    """
    authentication_classes = (SessionAuthentication, BasicAuthentication)
    permission_classes = (IsAdminUser,)
    queryset = ResourceBase.objects.all()
    serializer_class = ResourceBaseSerializer
    pagination_class = GeoNodeApiPagination
