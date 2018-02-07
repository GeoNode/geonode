import urllib
from geonode.geoserver.mixins import GeoServerMixin
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response

        
class GeoserverWFSListAPIView(ListAPIView, GeoServerMixin):
    """
    This api will serve wfs call of geoserver
    """
    
    def get(self, request, **kwargs):
        data = dict(request.query_params)
            
        query = self.get_configuration(data)
        query.update(dict(SERVICE='WFS'))

        result = self.get_response_from_geoserver('wfs', query)

        for feature in result.get('features'):
            if 'geometry' in feature:
                del feature['geometry']

        return Response(result, status=status.HTTP_200_OK)

