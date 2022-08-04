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
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.documents.models import Document

from geonode.base.models import ResourceBase
from geonode.base.api.serializers import ResourceBaseSerializer

from .serializers import DocumentSerializer
from .permissions import DocumentPermissionsFilter

import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(DynamicModelViewSet):
    """
    API endpoint that allows documents to be viewed or edited.
    """
    http_method_names = ['get', 'patch', 'put']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, UserHasPerms]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, DocumentPermissionsFilter
    ]
    queryset = Document.objects.all().order_by('-last_updated')
    serializer_class = DocumentSerializer
    pagination_class = GeoNodeApiPagination

    @extend_schema(methods=['get'], responses={200: ResourceBaseSerializer(many=True)},
                   description="API endpoint allowing to retrieve the DocumentResourceLink(s).")
    @action(detail=True, methods=['get'])
    def linked_resources(self, request, pk=None):
        document = self.get_object()
        resources_id = document.links.all().values('object_id')
        resources = ResourceBase.objects.filter(id__in=resources_id)
        exclude = []
        for resource in resources:
            if not request.user.is_superuser and \
                    not request.user.has_perm('view_resourcebase', resource.get_self_resource()):
                exclude.append(resource.id)
        resources = resources.exclude(id__in=exclude)
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get('page_size', 10)
        result_page = paginator.paginate_queryset(resources, request)
        serializer = ResourceBaseSerializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"resources": serializer.data})
