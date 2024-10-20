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

from geonode.metadata.manager import metadata_manager
from geonode.metadata.api.serializers import MetadataSerializer
from rest_framework.viewsets import ViewSet
from geonode.base.models import ResourceBase
from rest_framework.decorators import action
from django.http import JsonResponse
from rest_framework.response import Response

class MetadataViewSet(ViewSet):
    """
    Simple viewset that return the metadata JSON schema
    """
    
    queryset = ResourceBase.objects.all()
    serializer_class = MetadataSerializer

    def list(self, request):
        serializer = self.serializer_class(many=True)
        return Response(serializer.data)

    # Get the JSON schema
    @action(detail=False, methods=['get'])
    def schema(self, request):
        ''' 
        The user is able to export her/his keys with
        resource scope.
        '''
        
        schema = metadata_manager.get_schema()
    
        if schema:
            return Response(schema)

        else:
            response = {"Message": "Schema not found"}
            return Response(response)

    def retrieve(self, request, pk=None):

        data = self.queryset.filter(pk=pk)
        #serializer = self._get_and_validate_serializer(data=data)
        # resource = metadata_manager.get_resource_base(data, self.serializer_class)
        schema_instance = metadata_manager.build_schema_instance(data)
        #serialized_resource = self.serializer_class(data=schema_instance)
        #serialized_resource.is_valid(raise_exception=True)
        return Response(schema_instance)