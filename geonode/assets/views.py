#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from django.shortcuts import get_object_or_404
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from geonode.assets.handlers import asset_handler_registry
from geonode.assets.serializers import AssetSerializer
from geonode.assets.utils import get_perms_response, create_asset, create_asset_and_link
from geonode.assets.models import Asset

from geonode.base.api.filters import (
    DynamicSearchFilter,
)
from geonode.base.api.pagination import GeoNodeApiPagination

from geonode.base.models import ResourceBase
from geonode.base.api.permissions import UserHasPerms
from geonode.storage.manager import storage_manager
from rest_framework import status

logger = logging.getLogger(__name__)


class AssetViewSet(DynamicModelViewSet):
    """
    API endpoint that allows Assets to be viewed or edited.
    """

    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        # TODO: add filtering by owner / admin
    ]
    queryset = Asset.objects.all().order_by("-created")
    serializer_class = AssetSerializer  # TODO: appropriate Serializer should be switched for each Asset instance
    pagination_class = GeoNodeApiPagination

    def get_permissions(self):
        if self.action == "create":
            return [
                IsAuthenticatedOrReadOnly(),
                UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}}),
            ]
        return [IsAuthenticatedOrReadOnly()]

    def list(self, request, *args, **kwargs):
        """
        Only for lists, allows access to Assets only to owned ones, or to all of them if the user is an admin
        """
        queryset = self.filter_queryset(self.get_queryset())

        user = request.user
        is_admin = user.is_superuser if user and user.is_authenticated else False

        if is_admin:
            pass
        elif user and user.is_authenticated:
            queryset = queryset.filter(owner=user)
        else:
            queryset = queryset.none()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        file = data.get("file")
        resource_id = data.get("resource_id")
        asset = None
        try:
            file_name = storage_manager.save(file.name, file)
            file_path = storage_manager.path(file_name)
            if resource_id:
                resource = get_object_or_404(ResourceBase, pk=resource_id)
                asset, _ = create_asset_and_link(resource, request.user, [file_path])
            else:
                asset = create_asset(request.user, [file_path])
        except Exception as e:
            logger.error(f"An error occurred while creating the asset: {e}")
            return Response(
                {"error": "An internal error occurred while creating the asset"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if asset:
            serializer = self.get_serializer(asset)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({"error": "Could not create asset"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_file(self, request, pk, attachment: bool = False, path=None):
        asset = get_object_or_404(Asset, pk=pk)
        if bad_response := get_perms_response(request, asset):
            return bad_response
        asset_handler = asset_handler_registry.get_handler(asset)
        # TODO: register_event(request, EventType.EVENT_DOWNLOAD, asset)
        return asset_handler.get_download_handler(asset).create_response(asset, path=path, attachment=attachment)

    @action(
        detail=False,
        url_path="(?P<pk>\d+)/download(?:/(?P<path>.*))?",  # noqa
        # url_name="asset-download",
        methods=["get"],
    )
    def download(self, request, pk=None, path=None, *args, **kwargs):
        return self._get_file(request, pk, attachment=True, path=path)

    @action(
        detail=False,
        url_path="(?P<pk>\d+)/link(?:/(?P<path>.*))?",  # noqa
        # url_name="asset-link",
        methods=["get"],
    )
    def link(self, request, pk=None, path=None, *args, **kwargs):
        logger.warning(f"REQUESTED ASSET LINK FOR PK:{pk} PATH:{path}")
        return self._get_file(request, pk, attachment=False, path=path)
