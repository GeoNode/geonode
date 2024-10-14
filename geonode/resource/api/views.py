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
import logging

from dynamic_rest.filters import DynamicFilterBackend, DynamicSortingFilter
from dynamic_rest.viewsets import WithDynamicViewSetMixin
from geonode.base.api.filters import DynamicSearchFilter
from geonode.base.api.pagination import GeoNodeApiPagination
from geonode.base.api.permissions import IsOwnerOrReadOnly
from geonode.resource.api.exceptions import ExecutionRequestException
from geonode.resource.api.serializer import ExecutionRequestSerializer
from oauth2_provider.contrib.rest_framework import OAuth2Authentication
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.core.exceptions import ValidationError
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.decorators import api_view
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from ..models import ExecutionRequest

logger = logging.getLogger(__name__)


@api_view(["GET"])
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
                        "user": _request.user.username,
                        "status": _request.status,
                        "func_name": _request.func_name,
                        "created": _request.created,
                        "finished": _request.finished,
                        "last_updated": _request.last_updated,
                        "input_params": _request.input_params,
                        "output_params": _request.output_params,
                        "step": _request.step,
                        "log": _request.log,
                    },
                    status=status.HTTP_200_OK,
                )
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
    filter_backends = [DynamicFilterBackend, DynamicSortingFilter, DynamicSearchFilter]
    serializer_class = ExecutionRequestSerializer
    pagination_class = GeoNodeApiPagination
    http_method_names = ["get", "delete"]

    class Meta:
        ordering = ["created"]

    def get_queryset(self, queryset=None):
        return ExecutionRequest.objects.filter(user=self.request.user).order_by("pk")

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
