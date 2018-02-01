import json
import requests
import urllib
from django.conf import settings
from geonode.layers.models import Layer
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response


class GeoserverWMSListAPIView(ListAPIView):
    def _get_configuration(self, data):
        query = {}
        for k,v in data.items():
            query.update({k: v[0]})

        return query

    def _get_response_from_geoserver(self, url):
        response = requests.get(url)    
        return json.loads(response.content)

    def getAttributesPermission(self, layer_name):
        attributes = [l.attribute for l in Layer.objects.get(typename=layer_name).attribute_set.all()]
        return attributes
    
    def get(self, request, **kwargs):
        data = dict(request.query_params)
        layers = data.get('layers', [None])[0]

        if not layers:
            layers = data.get('LAYERS')[0]
            
        query = self._get_configuration(data)

        url = settings.LOCAL_GEOSERVER.get('source').get('url')

        result = self._get_response_from_geoserver('{}?{}'.format(url, urllib.urlencode(query)))
        
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
        
            
