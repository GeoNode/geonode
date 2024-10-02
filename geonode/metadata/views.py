#########################################################################
#
# Copyright (C) 2024 OSGeo
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
from geonode.metadata.engine import engine
from geonode.metadata.serializer import MetadataSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from oauth2_provider.contrib.rest_framework import OAuth2Authentication

from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated


class MetadataViewSet(ViewSet):
    """
    Simple viewset that return the metadata value
    """

    authentication_classes = [SessionAuthentication, BasicAuthentication, OAuth2Authentication]
    permission_classes = [
        IsAuthenticated,
    ]
    http_method_names = ["get", "post", "patch"]
    serializer_class = MetadataSerializer

    def list(self, request):
        serializer = self.serializer_class(many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        serializer = self._get_and_validate_serializer(data=engine.get_data_by_pk(pk))
        return Response(serializer.data)

    def post(self, request):
        # do something with `post_data`
        serializer = self._get_and_validate_serializer(data=request.data)
        pk = engine.save_metadata(payload=serializer.data)
        return Response(data=engine.get_data_by_pk(pk))

    def patch(self, request, pk=None):
        if pk is None:
            raise PermissionDenied()
        # do something with `post_data`
        serializer = self._get_and_validate_serializer(data=request.data)
        pk = engine.set_metadata(payload=serializer.data, pk=pk)
        return Response(data=engine.get_data_by_pk(pk))

    def _get_and_validate_serializer(self, data):
        serializer = self.serializer_class(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer
