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
from django.http import JsonResponse
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.response import Response

from django.utils.translation.trans_real import get_language_from_request

from geonode.base.models import ResourceBase
from geonode.metadata.manager import metadata_manager


class MetadataViewSet(ViewSet):
    """
    Simple viewset that return the metadata JSON schema
    """
    
    queryset = ResourceBase.objects.all()

    def list(self, request):
        pass

    # Get the JSON schema
    # A pk argument is set for futured multiple schemas
    @action(detail=False, 
            methods=['get'],
            url_path="schema(?:/(?P<pk>\d+))?"
            )
    def schema(self, request, pk=None):
        ''' 
        The user is able to export her/his keys with
        resource scope.
        '''

        lang = get_language_from_request(request)[:2]
        schema = metadata_manager.get_schema(lang)
    
        if schema:
            return Response(schema)

        else:
            response = {"Message": "Schema not found"}
            return Response(response)

    # Get the JSON schema
    @action(detail=False, 
            methods=['get', 'put'],
            url_path="instance/(?P<pk>\d+)"
            )
    def schema_instance(self, request, pk=None):
 
        try:
            resource = ResourceBase.objects.get(pk=pk)
            schema_instance = metadata_manager.build_schema_instance(resource)

            if request.method == 'GET':
                return JsonResponse(schema_instance, content_type="application/schema-instance+json", json_dumps_params={"indent":3})
            
            elif request.method == 'PUT':
                
                updated_content = metadata_manager.update_schema_instance(resource, request.data, schema_instance)

                return Response(updated_content)
            
        except ResourceBase.DoesNotExist:
            result = {"message": "The dataset was not found"}
            return Response(result)