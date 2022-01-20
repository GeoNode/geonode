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
import json
from urllib.parse import parse_qsl, urlparse
from dynamic_rest.viewsets import DynamicModelViewSet
from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter

from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.parsers import FileUploadParser
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from django.shortcuts import reverse
from django.utils.translation import ugettext as _

from geonode.base.api.filters import DynamicSearchFilter
from geonode.base.api.permissions import IsOwnerOrReadOnly, IsSelfOrAdminOrReadOnly
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.upload.utils import get_max_amount_of_steps

from .serializers import UploadSerializer, UploadSizeLimitSerializer
from .permissions import UploadPermissionsFilter

from ..models import Upload, UploadSizeLimit
from ..views import view as upload_view

import logging

logger = logging.getLogger(__name__)


class UploadViewSet(DynamicModelViewSet):
    """
    API endpoint that allows uploads to be viewed or edited.
    """
    parser_class = [FileUploadParser, ]

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter,
        UploadPermissionsFilter
    ]
    queryset = Upload.objects.all()
    serializer_class = UploadSerializer
    pagination_class = GeoNodeApiPagination

    def _emulate_client_upload_step(self, request, _step):
        """Emulates the calls of a client to the upload flow.
        It alters the content of the request object, so the same request should
        be reused in the next call of this method.

        Args:
            request (Request): A request object with the query params given by the lasted step call.
                               No params for the first call.
            _step (string): The current step, used as an argument in the upload_view call.
                            None for the first call.

        Returns:
            Response: response, upload_view response or a final response.
            string: next_step, the next step to be performed.
            boolean: is_final, True when the last step is executed or in case of errors.
        """
        response = upload_view(request, _step)
        if response.status_code == status.HTTP_200_OK:
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            data = json.loads(content)

            required_input = data.get('required_input', None)
            response_status = data.get('status', '')
            response_success = data.get('success', False)
            redirect_to = data.get('redirect_to', '')
            if required_input or not response_success or not redirect_to or response_status == 'finished':
                return response, None, True

            # Prepare next step
            parsed_redirect_to = urlparse(redirect_to)
            if reverse("data_upload") not in parsed_redirect_to.path:
                # Error, next step cannot be performed by `upload_view`
                return response, None, True
            next_step = parsed_redirect_to.path.split(reverse("data_upload"))[1]
            query_params = parse_qsl(parsed_redirect_to.query)
            request.method = 'GET'
            request.GET.clear()
            for key, value in query_params:
                request.GET[key] = value
            return response, next_step, False
        elif response.status_code == status.HTTP_302_FOUND:
            # Get next step, should be final
            parsed_redirect_to = urlparse(response.url)
            if reverse("data_upload") not in parsed_redirect_to.path:
                # Error, next step cannot be performed by `upload_view`
                return response, None, True
            next_step = parsed_redirect_to.path.split(reverse("data_upload"))[1]
            return response, next_step, False
        else:
            return response, None, True

    @extend_schema(methods=['put'],
                   responses={201: None},
                   description="""
        Starts an upload session based on the Dataset Upload Form.

        the form params look like:
        ```
            'csrfmiddlewaretoken': self.csrf_token,
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'time': 'false',
            'charset': 'UTF-8',
            'base_file': base_file,
            'dbf_file': dbf_file,
            'shx_file': shx_file,
            'prj_file': prj_file,
            'tif_file': tif_file
        ```
        """)
    @action(detail=False, methods=['post'])
    def upload(self, request, format=None):
        if not getattr(request, 'FILES', None):
            raise ParseError(_("Empty content"))

        user = request.user
        if not user or not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        next_step = None
        max_steps = get_max_amount_of_steps()
        for n in range(max_steps):
            response, next_step, is_final = self._emulate_client_upload_step(
                request,
                next_step
            )
            if is_final:
                return response
        # After performing 7 steps if we don't get any final response
        return response

    @extend_schema(methods=['put'],
                   responses={201: None},
                   description="""
        Starts an upload session based on the Dataset Upload Form.

        the form params look like:
        ```
            'csrfmiddlewaretoken': self.csrf_token,
            'permissions': '{ "users": {"AnonymousUser": ["view_resourcebase"]} , "groups":{}}',
            'time': 'false',
            'charset': 'UTF-8',
            'base_file': base_file,
            'dbf_file': dbf_file,
            'shx_file': shx_file,
            'prj_file': prj_file,
            'tif_file': tif_file
        ```
        """)
    @action(detail=False, methods=['post'])
    def upload_legacy(self, request, format=None):
        if not getattr(request, 'FILES', None):
            raise ParseError(_("Empty content"))

        user = request.user
        if not user or not user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        response = upload_view(request, None)
        if response.status_code == 200:
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            data = json.loads(content)

            import_id = int(data["redirect_to"].split("?id=")[1].split("&")[0])
            request.method = 'GET'
            request.GET['id'] = import_id

            upload_view(request, 'check')
            response = upload_view(request, 'final')
            content = response.content
            if isinstance(content, bytes):
                content = content.decode('UTF-8')
            data = json.loads(content)
            return Response(data=data, status=status.HTTP_201_CREATED)
        return Response(status=response.status_code)


class UploadSizeLimitViewSet(DynamicModelViewSet):
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsSelfOrAdminOrReadOnly]
    queryset = UploadSizeLimit.objects.all()
    serializer_class = UploadSizeLimitSerializer
    pagination_class = GeoNodeApiPagination

    def destroy(self, request, *args, **kwargs):
        protected_objects = [
            'total_upload_size_sum',
            'document_upload_size',
            'file_upload_handler',
        ]
        instance = self.get_object()
        if instance.slug in protected_objects:
            detail = _(f"The limit `{instance.slug}` should not be deleted.")
            raise ValidationError(detail)
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)
