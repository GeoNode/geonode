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

from uuid import uuid1
from urllib.parse import urljoin

from django.urls import reverse
from django.conf import settings
from django.http.request import QueryDict

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from geonode.base.models import Configuration
from geonode.resource.manager import ResourceManager, resource_manager
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


@api_view(['POST'])
def resource_service_create(request, resource_type: str = None):
    """Instructs the Async dispatcher to execute a 'CREATE' operation
     **WARNING**: This will create an empty dataset; if you need to upload a resource to GeoNode, consider using the endpoint "ingest" instead

     - input_params: {
         uuid: "<str: UUID>",
         defaults: "{\"owner\":\"<str: username>\",<list: str>}",  # WARNING: 'owner' is mandatory
         resource_type: "<enum: ['dataset', 'document', 'map', '<GeoApp: name>']>"
       }

     - output_params: {
         output: <int: number of resources deleted / 0 if none>
       }

     - output: {
            "status": "ready",
            "execution_id": "<str: execution ID>",
            "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
        }

    Sample Request:

    1. curl -v -X POST -u admin:admin -H "Content-Type: application/json" -d 'defaults={"owner":"admin","title":"pippo"}'
          http://localhost:8000/api/v2/resource-service/create/dataset
        OUTPUT: {
            "status": "ready",
            "execution_id": "90ca670d-df60-44b6-b358-d792c6aecc58",
            "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58"
        }

     2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58
        OUTPUT: {
            "user": "admin",
            "status": "finished",
            "func_name": "create",
            "created": "2021-07-22T15:32:09.096075Z",
            "finished": "2021-07-22T15:32:26.936683Z",
            "last_updated": "2021-07-22T15:32:09.096129Z",
            "input_params": {
                "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb",
                "defaults": "{\"owner\":\"admin\",\"title\":\"pippo\"}",
                "resource_type": "dataset"
            },
            "output_params": {
                "output": {
                    "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb"
                }
            }
        }
    """
    config = Configuration.load()
    if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated \
    or not request.user.has_perm('base.add_resourcebase'):
        return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        request_params = QueryDict(request.body, mutable=True)
        _exec_request = ExecutionRequest.objects.create(
            user=request.user,
            func_name='create',
            input_params={
                "uuid": request_params.get('uuid', str(uuid1())),
                "resource_type": resource_type,
                "defaults": request_params.get('defaults', f"{{\"owner\":\"{request.user.username}\"}}")
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


@api_view(['POST'])
def resource_service_ingest(request, resource_type: str = None):
    """Instructs the Async dispatcher to execute a 'INGEST' operation
     **WARNING**: This will create an empty dataset; if you need to upload a resource to GeoNode, consider using the endpoint "ingest" instead

     - input_params: {
         uuid: "<str: UUID>",
         defaults: "{\"owner\":\"<str: username>\",<list: str>}",  # WARNING: 'owner' is mandatory
         resource_type: "<enum: ['dataset', 'document', 'map', '<GeoApp: name>']>"
       }

     - output_params: {
         output: <int: number of resources deleted / 0 if none>
       }

     - output: {
            "status": "ready",
            "execution_id": "<str: execution ID>",
            "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
        }

    Sample Request:

    1. curl -v -X POST -u admin:admin -H "Content-Type: application/json" -d 'defaults={"owner":"admin","title":"pippo"}'
          http://localhost:8000/api/v2/resource-service/create/dataset
        OUTPUT: {
            "status": "ready",
            "execution_id": "90ca670d-df60-44b6-b358-d792c6aecc58",
            "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58"
        }

     2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/90ca670d-df60-44b6-b358-d792c6aecc58
        OUTPUT: {
            "user": "admin",
            "status": "finished",
            "func_name": "create",
            "created": "2021-07-22T15:32:09.096075Z",
            "finished": "2021-07-22T15:32:26.936683Z",
            "last_updated": "2021-07-22T15:32:09.096129Z",
            "input_params": {
                "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb",
                "defaults": "{\"owner\":\"admin\",\"title\":\"pippo\"}",
                "resource_type": "dataset"
            },
            "output_params": {
                "output": {
                    "uuid": "fa404f64-eb01-11eb-8f91-00155d41f2fb"
                }
            }
        }
    """
    config = Configuration.load()
    if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated \
    or not request.user.has_perm('base.add_resourcebase'):
        return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        request_params = QueryDict(request.body, mutable=True)
        _exec_request = ExecutionRequest.objects.create(
            user=request.user,
            func_name='ingest',
            input_params={
                "uuid": request_params.get('uuid', str(uuid1())),
                "files": request_params.get('files', '[]'),
                "resource_type": resource_type,
                "defaults": request_params.get('defaults', f"{{\"owner\":\"{request.user.username}\"}}")
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

     1. curl -v -X DELETE -u admin:admin http://localhost:8000/api/v2/resource-service/delete/<uuid>
        OUTPUT: {
            "status":"ready",
            "execution_id":"7ed0b141-cf85-434f-bbfb-c02447a5221b",
            "status_url":"http://localhost:8000/api/v2/resource-service/execution-status/7ed0b141-cf85-434f-bbfb-c02447a5221b"
        }

     2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/7ed0b141-cf85-434f-bbfb-c02447a5221b
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
    config = Configuration.load()
    resource = ResourceManager._get_instance(uuid)
    if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated or \
            resource is None or not request.user.has_perm('delete_resourcebase', resource.get_self_resource()):
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


@api_view(['PUT'])
def resource_service_update(request, uuid: str):
    """Instructs the Async dispatcher to execute a 'UPDATE' operation over a valid 'uuid'

     - input_params: {
         uuid: "<str: UUID>"
         xml_file: str = None
         metadata_uploaded: bool = False
         vals: dict = {}
         regions: list = []
         keywords: list = []
         custom: dict = {}
         notify: bool = True
       }

     - output_params: {
         output: {
             uuid: "<str: UUID>"
         }
       }

     - output: {
            "status": "ready",
            "execution_id": "<str: execution ID>",
            "status_url": "http://localhost:8000/api/v2/resource-service/execution-status/<str: execution ID>"
        }

    Sample Request:

    1. curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'vals={"title":"pippo"}' http://localhost:8000/api/v2/resource-service/update/<uuid>
        OUTPUT: {
            "status":"ready",
            "execution_id":"08846e84-eae4-11eb-84be-00155d41f2fb",
            "status_url":"http://localhost:8000/api/v2/resource-service/execution-status/08846e84-eae4-11eb-84be-00155d41f2fb"
        }

    2. curl -v -X GET -u admin:admin http://localhost:8000/api/v2/resource-service/execution-status/08846e84-eae4-11eb-84be-00155d41f2fb
        OUTPUT: {
            "user": "admin",
            "status": "finished",
            "func_name": "update",
            "created": "2021-07-22T14:42:56.284740Z",
            "finished": "2021-07-22T14:43:01.813971Z",
            "last_updated": "2021-07-22T14:42:56.284797Z",
            "input_params": {
                "uuid": "ee11541c-eaee-11eb-942c-00155d41f2fb",
                "vals": "{\"title\":\"pippo\"}",
                "custom": {},
                "notify": true,
                "regions": [],
                "keywords": [],
                "xml_file": null,
                "metadata_uploaded": false
            },
            "output_params": {
                "output": {
                    "uuid": "ee11541c-eaee-11eb-942c-00155d41f2fb"
                }
            }
        }

    Sample Request with more parameters:

    1. curl -v -X PUT -u admin:admin -H "Content-Type: application/json" -d 'vals={"title":"pippo"}' -d 'metadata_uploaded=true' -d 'keywords=["k1", "k2", "k3"]'
          http://localhost:8000/api/v2/resource-service/update/<uuid>
    """
    config = Configuration.load()
    resource = ResourceManager._get_instance(uuid)
    if config.read_only or config.maintenance or request.user.is_anonymous or not request.user.is_authenticated or \
            resource is None or not request.user.has_perm('change_resourcebase', resource.get_self_resource()):
        return Response(status=status.HTTP_403_FORBIDDEN)
    try:
        request_params = QueryDict(request.body, mutable=True)
        _exec_request = ExecutionRequest.objects.create(
            user=request.user,
            func_name='update',
            input_params={
                "uuid": uuid,
                "xml_file": request_params.get('xml_file', None),
                "metadata_uploaded": request_params.get('metadata_uploaded', False),
                "vals": request_params.get('vals', '{}'),
                "regions": request_params.get('regions', '[]'),
                "keywords": request_params.get('keywords', '[]'),
                "custom": request_params.get('custom', '{}'),
                "notify": request_params.get('notify', True)
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
