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

from geonode.assets.utils import create_asset_and_link
from geonode.base.api.filters import DynamicSearchFilter, ExtentFilter
from geonode.base.api.mixins import AdvertisedListMixin
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import UserHasPerms
from geonode.base.api.views import base_linked_resources, ApiPresetsInitializer
from geonode.base import enumerations
from geonode.documents.api.exceptions import DocumentException
from geonode.documents.models import Document

from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.resource.utils import resourcebase_post_save
from geonode.storage.manager import StorageManager
from geonode.resource.manager import resource_manager

from .serializers import DocumentSerializer
from .permissions import DocumentPermissionsFilter

import logging


logger = logging.getLogger(__name__)


class DocumentViewSet(ApiPresetsInitializer, DynamicModelViewSet, AdvertisedListMixin):
    """
    API endpoint that allows documents to be viewed or edited.
    """

    http_method_names = ["get", "patch", "put", "post"]
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [
        IsAuthenticatedOrReadOnly,
        UserHasPerms(perms_dict={"default": {"POST": ["base.add_resourcebase"]}}),
    ]
    filter_backends = [
        DynamicFilterBackend,
        DynamicSortingFilter,
        DynamicSearchFilter,
        ExtentFilter,
        DocumentPermissionsFilter,
    ]
    queryset = Document.objects.all().order_by("-created")
    serializer_class = DocumentSerializer
    pagination_class = GeoNodeApiPagination

    def perform_create(self, serializer):
        """
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
        """
        manager = None
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data.pop("file_path", None) or serializer.validated_data.pop("doc_file", None)
        doc_url = serializer.validated_data.pop("doc_url", None)
        extension = serializer.validated_data.pop("extension", None)

        if not file and not doc_url:
            raise DocumentException(detail="A file, file path or URL must be speficied")

        if file and doc_url:
            raise DocumentException(detail="Either a file or a URL must be specified, not both")

        if not extension:
            filename = file if isinstance(file, str) else file.name
            extension = Path(filename).suffix.replace(".", "")

        if extension not in settings.ALLOWED_DOCUMENT_TYPES:
            raise DocumentException("The file provided is not in the supported extensions list")

        try:
            payload = {
                "owner": self.request.user,
                "extension": extension,
                "resource_type": "document",
            }
            if doc_url:
                payload["doc_url"] = doc_url
                payload["sourcetype"] = enumerations.SOURCE_TYPE_REMOTE

            resource = serializer.save(**payload)

            if file:
                manager = StorageManager(remote_files={"base_file": file})
                manager.clone_remote_files()
                create_asset_and_link(
                    resource, self.request.user, [manager.get_retrieved_paths().get("base_file")], clone_files=True
                )
                manager.delete_retrieved_paths(force=True)

            resource.set_missing_info()
            resourcebase_post_save(resource.get_real_instance())
            resource_manager.set_permissions(None, instance=resource, permissions=None, created=True)
            resource.handle_moderated_uploads()
            resource_manager.set_thumbnail(resource.uuid, instance=resource, overwrite=False)
            return resource
        except Exception as e:
            logger.error(f"Error creating document {serializer.validated_data}", exc_info=e)
            if manager:
                manager.delete_retrieved_paths()
            raise e

    @extend_schema(
        methods=["get"],
        responses={200: ResourceBaseSerializer(many=True)},
        description="API endpoint allowing to retrieve linked resources",
    )
    @action(detail=True, methods=["get"])
    def linked_resources(self, request, pk=None, *args, **kwargs):
        return base_linked_resources(self.get_object().get_real_instance(), request.user, request.GET)
