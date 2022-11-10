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
from pathlib import Path
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from geonode import settings

from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.documents.api.exceptions import DocumentException
from geonode.documents.models import Document

from geonode.base.models import ResourceBase
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.resource.utils import resourcebase_post_save
from geonode.storage.manager import StorageManager
from geonode.resource.manager import resource_manager

from .serializers import DocumentSerializer
from .permissions import DocumentPermissionsFilter

import logging

logger = logging.getLogger(__name__)


class DocumentViewSet(DynamicModelViewSet):
    """
    API endpoint that allows documents to be viewed or edited.
    """
    http_method_names = ['get', 'patch', 'put', 'post']
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}})]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        ExtentFilter, DocumentPermissionsFilter
    ]
    queryset = Document.objects.all().order_by('-created')
    serializer_class = DocumentSerializer
    pagination_class = GeoNodeApiPagination

    def perform_create(self, serializer):
        '''
        Function to create document via API v2.
        file_path: path to the file
        doc_file: the open file

        The API expect this kind of JSON:
        {
            "document": {
                "title": "New document",
                "metadata_only": true,
                "file_path": "/home/mattia/example.json"
            }
        }
        File path rappresent the filepath where the file to upload is saved.

        or can be also a form-data:
        curl --location --request POST 'http://localhost:8000/api/v2/documents' \
        --form 'title="Super Title2"' \
        --form 'doc_file=@"/C:/Users/user/Pictures/BcMc-a6T9IM.jpg"' \
        --form 'metadata_only="False"'
        '''
        manager = None
        serializer.is_valid(raise_exception=True)
        _has_file = serializer.validated_data.pop("file_path", None) or serializer.validated_data.pop("doc_file", None)
        extension = serializer.validated_data.pop("extension", None)

        if not _has_file:
            raise DocumentException(detail="A file path or a file must be speficied")

        if not extension:
            filename = _has_file if isinstance(_has_file, str) else _has_file.name
            extension = Path(filename).suffix.replace(".", "")

        if extension not in settings.ALLOWED_DOCUMENT_TYPES:
            raise DocumentException("The file provided is not in the supported extension file list")

        try:
            manager = StorageManager(remote_files={"base_file": _has_file})
            manager.clone_remote_files()
            files = manager.get_retrieved_paths()

            resource = serializer.save(
                **{
                    "owner": self.request.user,
                    "extension": extension,
                    "files": [files.get("base_file")],
                    "resource_type": "document"
                }
            )

            resource.set_missing_info()
            resourcebase_post_save(resource.get_real_instance())
            resource_manager.set_permissions(None, instance=resource, permissions=None, created=True)
            resource.handle_moderated_uploads()
            resource_manager.set_thumbnail(resource.uuid, instance=resource, overwrite=False)
            return resource
        except Exception as e:
            if manager:
                manager.delete_retrieved_paths()
            raise e

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
