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
import typing
import inspect
import logging
import importlib

from django.apps import apps
from django.db.models.query import QuerySet

from rest_framework import status
from rest_framework.response import Response

from geonode.base.models import ResourceBase
from geonode.security.utils import get_resources_with_perms
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.serializers import ResourceBaseSerializer
from geonode.base.api.serializers import BaseDynamicModelSerializer

logger = logging.getLogger(__name__)


def get_api_serializer(app) -> BaseDynamicModelSerializer:
    if app:
        try:
            _module = importlib.import_module(f"{app.name}.api.serializers")
            for name, obj in inspect.getmembers(_module):
                if inspect.isclass(obj) and issubclass(obj, ResourceBaseSerializer):
                    return obj
        except Exception as e:
            logger.debug(e)
    return ResourceBaseSerializer


def resolve_type_serializer(resource_type: str = None) -> typing.Tuple[object, BaseDynamicModelSerializer]:
    _resource_type = ResourceBase
    _serializer = ResourceBaseSerializer
    if resource_type:
        _resource_type_found = False
        for label, app in apps.app_configs.items():
            if _resource_type_found:
                break
            if hasattr(app, "models"):
                for _model_name, _model in app.models.items():
                    if resource_type.lower() == _model_name.lower():
                        _resource_type_found = True
                        _serializer = get_api_serializer(app)
                        _resource_type = _model
                        break
        if not _resource_type_found:
            _resource_type = ResourceBase
    return _resource_type, _serializer


def filtered(request, resources: QuerySet, serializer: BaseDynamicModelSerializer) -> Response:
    try:
        paginator = GeoNodeApiPagination()
        paginator.page_size = request.GET.get("page_size", 10)
        user_resources = get_resources_with_perms(request.user)
        resources = resources.filter(id__in=user_resources)
        result_page = paginator.paginate_queryset(resources, request)
        resource_type_serializer = serializer(result_page, embed=True, many=True)
        return paginator.get_paginated_response({"resources": resource_type_serializer.data})
    except Exception as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, exception=e)
