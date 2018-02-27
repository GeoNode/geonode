import json
import requests
import urllib
from django.conf import settings
from geonode.layers.models import Layer


class GeoServerMixin(object):
    """
    Mixing for GeoServer
    """
    def get_configuration(self, data):
        query = {}
        for k,v in data.items():
            query.update({k: v[0] if type(v) == list else v})
        return query

    def get_response_from_geoserver(self, api_type, query):
        url = settings.GEOSERVER_LOCATION + api_type
        response = requests.get('{}?{}'.format(url, urllib.urlencode(query)))    
        return json.loads(response.content)

    def getAttributesPermission(self, layer_name):
        attributes = [l.attribute for l in Layer.objects.get(typename=layer_name).attribute_set.all()]
        return attributes

