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
from geonode.metadata.engine import MetadataEngine
from geonode.metadata.models import UISchemaModel
from geonode.metadata.serializer import MetadataSerializer
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import generics
from django.core.cache import caches


class DynamicResourceViewSet(ViewSet):
    """
    Simple viewset that return the metadata value
    """

    serializer_class = MetadataSerializer

    def list(self, request):
        serializer = self.serializer_class(many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        engine = MetadataEngine()
        serializer = self.serializer_class(data=engine.get_data_by_pk(pk))
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)


class UiSchemaViewset(generics.RetrieveAPIView):
    """
    Return the UI schema
    """

    def get(self, request, **kwargs):
        uischema_cache = caches["uischema_cache"]
        schema = uischema_cache.get("uischema")
        if not schema:
            schema = UISchemaModel.objects.first().ui_schema_json
            uischema_cache.set("uischema", schema, 3600)
        return Response(schema)
