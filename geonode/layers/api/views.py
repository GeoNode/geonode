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
from geonode.thumbs.thumbnails import create_thumbnail
import json
from drf_spectacular.utils import extend_schema
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from rest_framework.decorators import action

from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework.response import Response

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.layers.models import Layer

from .serializers import LayerSerializer
from .permissions import LayerPermissionsFilter

import logging
import ast

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

    @extend_schema(
        methods=["post"], responses={200}, description="API endpoint allowing to set the thumbnail url for an existing dataset."
    )
    @action(
        detail=False,
        url_path="(?P<dataset_id>\d+)/set_thumbnail_from_bbox", # noqa
        url_name="set-thumb-from-bbox",
        methods=["post"],
        permission_classes=[
            IsAuthenticated,
        ],
    )
    def set_thumbnail_from_bbox(self, request, dataset_id):
        try:
            layer = Layer.objects.get(resourcebase_ptr_id=ast.literal_eval(dataset_id))
            request_body = request.data if request.data else json.loads(request.body)
            bbox = request_body["bbox"] + [request_body["srid"]]
            zoom = request_body.get("zoom", None)

            thumbnail_url = create_thumbnail(layer, bbox=bbox, background_zoom=zoom, overwrite=True)
            return Response({"thumbnail_url": thumbnail_url}, status=200)
        except Layer.DoesNotExist:
            logger.error(f"Dataset selected with id {dataset_id} does not exists")
            return Response(data={"message": f"Dataset selected with id {dataset_id} does not exists"}, status=404, exception=True)
        except Exception as e:
            logger.error(e)
            return Response(data={"message": e.args[0]}, status=500, exception=True)
