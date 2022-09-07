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
import logging

from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import WithDynamicViewSetMixin
from geonode.base.api.filters import DynamicSearchFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.resource.api.exceptions import ExecutionRequestException
from geonode.resource.api.serializer import ExecutionRequestSerializer
from geonode.resource.manager import resource_manager
from geonode.security.utils import get_resources_with_perms
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.decorators import api_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..models import ExecutionRequest
from .utils import filtered, resolve_type_serializer

logger = logging.getLogger(__name__)


@api_view(['GET'])
def resource_service_search(request, resource_type: str = None):
    """
    Return a list of resources matching the filtering criteria.

    Sample requests:

     - Get all ResourceBases the user has access to:
        http://localhost:8000/api/v2/resource-service/search

     - Get all ResourceBases filtered by type criteria the user has access to:
        http://localhost:8000/api/v2/resource-service/search/layer

     - Get ResourceBases filtered by model criteria the user has access to:
        http://localhost:8000/api/v2/resource-service/search/?filter={"title__icontains":"foo"}

    """
    try:
        search_filter = json.loads(request.GET.get('filter', '{}'))
    except Exception as e:
        return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    _resource_type, _serializer = resolve_type_serializer(resource_type)
    logger.error(f"Serializing '{_resource_type}' resources through {_serializer}.")
    return filtered(request, resource_manager.search(search_filter, resource_type=_resource_type), _serializer)


@api_view(['GET'])
def resource_service_exists(request, uuid: str):
    """
    Returns a JSON boolean success field valorized with the 'exists' operation outcome.

    -  GET http://localhost:8000/api/v2/resource-service/exists/13decd74-df04-11eb-a0c1-00155dc3de71
       ```
        200,
        {
            'success': true
        }
       ```
    """
    _exists = False
    if resource_manager.exists(uuid):
        _exists = get_resources_with_perms(request.user).filter(uuid=uuid).exists()
    return Response({'success': _exists}, status=status.HTTP_200_OK)


@api_view(['GET'])
def resource_service_execution_status(request, execution_id: str):
    """Main dispatcher endpoint to follow an API request status progress

     - GET input: <str: execution id>
     - output: <ExecutionRequest>
    """
    try:
        _exec_request = ExecutionRequest.objects.filter(exec_id=execution_id)
        if not _exec_request.exists():
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            _request = _exec_request.get()
            if _request.user == request.user or request.user.is_superuser:
                return Response(
                    {
                        'user': _request.user.username,
                        'status': _request.status,
                        'func_name': _request.func_name,
                        'created': _request.created,
                        'finished': _request.finished,
                        'last_updated': _request.last_updated,
                        'input_params': _request.input_params,
                        'output_params': _request.output_params,
                        'step': _request.step,
                        'log': _request.log
                    },
                    status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception(e)
        return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)


class ExecutionRequestViewset(WithDynamicViewSetMixin, ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    filter_backends = [
        DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter
    ]
    serializer_class = ExecutionRequestSerializer
    pagination_class = GeoNodeApiPagination
    http_method_names = ['get', 'delete']

    def get_queryset(self, queryset=None):
        return ExecutionRequest.objects.filter(user=self.request.user).order_by('pk')

    def delete(self, *args, **kwargs):
        try:
            _pk = kwargs.get("pk")
            if not _pk:
                raise ExecutionRequestException("UUID was not provided")

            _entry = self.get_queryset().filter(exec_id=_pk)
            if not _entry.exists():
                raise NotFound(detail=f"uuid provided does not exists: {_pk}")

            _entry.delete()

            return Response(status=200)
        except ValidationError as e:
            raise ExecutionRequestException(detail=e.messages[0] if e.messages else e)
        except Exception as e:
            raise e
