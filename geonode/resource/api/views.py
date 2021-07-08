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
import inspect
import importlib

from django.apps import apps

from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view

from geonode.base.models import ResourceBase
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.serializers import ResourceBaseSerializer

from geonode.resource.manager import resource_manager

from geonode.security.utils import get_resources_with_perms

import logging

logger = logging.getLogger(__name__)


def _get_api_serializer(app):
    if app:
        try:
            _module = importlib.import_module(f'{app.name}.api.serializers')
            for name, obj in inspect.getmembers(_module):
                if inspect.isclass(obj) and issubclass(obj, ResourceBaseSerializer):
                    return obj
        except Exception as e:
            logger.debug(e)
    return ResourceBaseSerializer


def _filtered(request, resources, serializer):
    try:
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get('page_size', 10)
        user_resources = get_resources_with_perms(request.user)
        resources = resources.filter(id__in=user_resources)
        result_page = paginator.paginate_queryset(resources, request)
        resource_type_serializer = serializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"resources": resource_type_serializer.data})
    except Exception as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=e)


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
    _serializer = ResourceBaseSerializer
    try:
        search_filter = json.loads(request.GET.get('filter', '{}'))
    except Exception as e:
        return Response(status=status.HTTP_400_BAD_REQUEST, exception=e)

    if not resource_type:
        resource_type = ResourceBase
    else:
        _resource_type_found = False
        for label, app in apps.app_configs.items():
            if _resource_type_found:
                break
            if hasattr(app, 'models'):
                for _model_name, _model in app.models.items():
                    if resource_type.lower() == _model_name.lower():
                        _resource_type_found = True
                        _serializer = _get_api_serializer(app)
                        resource_type = _model
                        break
        if not _resource_type_found:
            resource_type = ResourceBase
    logger.debug(f"Searching for {resource_type} type resources.")
    return _filtered(request, resource_manager.search(search_filter, resource_type=resource_type), _serializer)


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
    return Response({'success': resource_manager.exists(uuid)}, status=status.HTTP_200_OK)
