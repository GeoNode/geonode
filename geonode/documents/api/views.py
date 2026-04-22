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

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter, AdvertisedFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.base.api.views import base_linked_resources, ApiPresetsInitializer
from geonode.documents.models import Document
from geonode.metadata.multilang.views import MultiLangViewMixin

from .serializers import DocumentSerializer
from .permissions import DocumentPermissionsFilter

import logging


logger = logging.getLogger(__name__)


class DocumentViewSet(ApiPresetsInitializer, MultiLangViewMixin, DynamicModelViewSet):
    """
    API endpoint that allows documents to be viewed or partially updated.

    Document creation is intentionally not exposed here -- use the
    /documents/upload/ endpoint (DocumentUploadView) so that uploads go
    through the FileValidationUploadHandler magic-byte check. Full PUT
    replacement is disabled; only PATCH metadata edits are allowed.
    """

    http_method_names = ["get", "patch"]
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        AdvertisedFilter,
        ExtentFilter,
        DocumentPermissionsFilter,
    ]
    queryset = Document.objects.all().order_by("-created")
    serializer_class = DocumentSerializer
    pagination_class = GeoNodeApiPagination

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve linked resources",
    )
    @action(detail=True, methods=["get"])
    def linked_resources(self, request, pk=None, *args, **kwargs):
        return base_linked_resources(self.get_object().get_real_instance(), request.user, request.GET)
