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
from django.views.decorators.csrf import csrf_exempt
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from django.http import JsonResponse

class MetadataViewSet(ViewSet):
    """
    Simple viewset that return the metadata JSON schema
    """

    # serializer_class = MetadataSerializer

    # Get the JSON schema
    @action(detail=False, methods=['get'])
    def schema(self, request):
        ''' 
        The user is able to export her/his keys with
        resource scope.
        '''
        
        schema = metadata_manager.get_schema()
    
        if schema:
            return JsonResponse(schema)

        else:
            response = {"Message": "Schema not found"}
            return JsonResponse(response)

