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

from urllib.parse import urljoin

from django.urls import reverse
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from geonode.resource.manager import resource_manager
from geonode.security.utils import get_resources_with_perms

from .tasks import resouce_service_dispatcher
from .utils import (
    filtered,
    resolve_type_serializer)

from ..models import ExecutionRequest

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

     - input: <str: execution id>
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
                        'output_params': _request.output_params
                    },
                    status=status.HTTP_200_OK)
        return Response(status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        logger.exception(e)
        return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)


@api_view(['DELETE'])
def resource_service_delete(request, uuid: str):
    """Instructs the Async dispatcher to execute a 'DELETE' operation over a valid 'uuid'

     - input_params: {
         uuid: "<str: UUID>"
       }

     - output_params: {
         output: <int: number of resources deleted / 0 if none>
       }

     - output: {
            "status": "ready",
            "execution_id": "<str: execution ID>",
            "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
        }

    Sample request:

     1. curl -v -X DELETE -u admin:admin http://localhost:8000/api/v2/resource-service/delete/1234
        OUTPUT: {
            "status":"ready",
            "execution_id":"7ed0b141-cf85-434f-bbfb-c02447a5221b",
            "status_url":"http://localhost:8000/api/v2/resource-service/execution-status/7ed0b141-cf85-434f-bbfb-c02447a5221b"
        }

     2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/42c0dee6-0cb0-4af7-9bd9-f7dccf75a2d9
        OUTPUT: {
            "user":"admin",
            "status":"finished",
            "func_name":"delete",
            "created":"2021-07-19T14:09:59.930619Z",
            "finished":"2021-07-19T14:10:00.054915Z",
            "last_updated":"2021-07-19T14:09:59.930647Z",
            "input_params":{"uuid":"1234"},
            "output_params":{"output":0}
        }
    """
    if request.user.is_anonymous:
        return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        _exec_request = ExecutionRequest.objects.create(
            user=request.user,
            func_name='delete',
            input_params={
                "uuid": uuid
            }
        )
        resouce_service_dispatcher.apply_async((_exec_request.exec_id,))
        return Response(
            {
                'status': _exec_request.status,
                'execution_id': _exec_request.exec_id,
                'status_url':
                    urljoin(
                        settings.SITEURL,
                        reverse('rs-execution-status', kwargs={'execution_id': _exec_request.exec_id})
                    )
            },
            status=status.HTTP_200_OK)
    except Exception as e:
        logger.exception(e)
        return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)
