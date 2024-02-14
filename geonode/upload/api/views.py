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
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from django.utils.translation import gettext_lazy as _

from geonode.base.api.filters import DynamicSearchFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly, IsSelfOrAdminOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination


from .serializers import (
    UploadSerializer,
    UploadParallelismLimitSerializer,
    UploadSizeLimitSerializer,
)
from .permissions import UploadPermissionsFilter

from ..models import Upload, UploadParallelismLimit, UploadSizeLimit

import logging

logger = logging.getLogger(__name__)


class UploadViewSet(DynamicModelViewSet):
    """
    API endpoint that allows uploads to be viewed or edited.
    """

    parser_class = [
        FileUploadParser,
    ]

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter, UploadPermissionsFilter]
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer
    pagination_class = GeoNodeApiPagination
    http_method_names = ["get", "post"]

    @extend_schema(
        methods=["post"],
        responses={201: None},
    )
    @action(detail=False, methods=["post"])
    def upload(self, request, format=None):
        return []


class UploadSizeLimitViewSet(DynamicModelViewSet):
    http_method_names = ["get", "post"]
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly]
    queryset = UploadSizeLimit.objects.all()
    serializer_class = UploadSizeLimitSerializer
    pagination_class = GeoNodeApiPagination

    def destroy(self, request, *args, **kwargs):
        protected_objects = [
            "dataset_upload_size",
            "document_upload_size",
            "file_upload_handler",
        ]
        instance = self.get_object()
        if instance.slug in protected_objects:
            detail = _(f"The limit `{instance.slug}` should not be deleted.")
            raise ValidationError(detail)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UploadParallelismLimitViewSet(DynamicModelViewSet):
    http_method_names = ["get", "post"]
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly]
    queryset = UploadParallelismLimit.objects.all()
    serializer_class = UploadParallelismLimitSerializer
    pagination_class = GeoNodeApiPagination

    def get_serializer(self, *args, **kwargs):
        serializer = super(UploadParallelismLimitViewSet, self).get_serializer(*args, **kwargs)
        if self.action == "create":
            serializer.fields["slug"].read_only = False
        return serializer

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.slug == "default_max_parallel_uploads":
            detail = _("The limit `default_max_parallel_uploads` should not be deleted.")
            raise ValidationError(detail)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
