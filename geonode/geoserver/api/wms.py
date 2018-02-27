from geonode.geoserver.mixins import GeoServerMixin
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response


class GeoserverWMSGetFeatureInfoListAPIView(ListAPIView, GeoServerMixin):
    """
    This api will serve wms call of geoserver
    """
    
    def get(self, request, **kwargs):
        data = dict(request.query_params)
        layers = data.get('layers', [None])[0]

        if not layers:
            layers = data.get('LAYERS')[0]
            
        query = self.get_configuration(data)
        query.update(dict(SERVICE='WMS', REQUEST='GetFeatureInfo'))

        result = self.get_response_from_geoserver('wms', query)
        
        permitted_attributes = {}
        for layer_name in layers.split(','):
            attributes = self.getAttributesPermission(layer_name=layer_name)
            permitted_attributes.update({layer_name.split(':')[1]:attributes})

        for feature in result.get('features'):
            layer_name = feature['id'].split('.')[0]
            if 'geometry' in feature:
                del feature['geometry']
                
            for k,v in feature.get('properties').items():
                if k not in permitted_attributes[layer_name] and k in feature.get('properties'):
                    del feature['properties'][k]

        return Response(result, status=status.HTTP_200_OK)
