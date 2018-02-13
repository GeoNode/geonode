import csv, StringIO, urllib
from geonode.geoserver.mixins import GeoServerMixin
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView
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


class GeoserverCreateLayerByFeature(GeoServerMixin, CreateAPIView):
    """
    This api will serve create layer
    """
    def create_csv(self, result):
        from shapely.geometry import shape

        for feature in result.get('features'):
            if 'geometry' in feature and 'properties' in feature:
                feature['properties'].update(dict(geom=shape(feature.get('geometry')).wkt))
         
        mem_file = StringIO.StringIO()
        csv_writer = csv.writer(mem_file, quoting=csv.QUOTE_ALL)

        features = [r.get('properties') for r in result.get('features')]
        keys = [k for k, v in features[0].items()]        
        values = [[v for k, v in f.items()] for f in features]
        csv_writer.writerows([keys] + values)

        return mem_file

    def create_layer(self, csv, host, scheme='http', cookies = None):
        import requests, json   

        if not cookies:
            cookies = dict()

        files = {'base_file': ('base_file.csv', csv.getvalue(), 'application/octet-stream', {'Expires': '0'})}

        data = {
            'permissions': json.dumps({}),
            'charset': 'UTF-8',
            'layer_title': 'auto_layer_upload_multi',
            'category': 'building',
            'organization': 1,
            'csv_layer_type': 'the_geom',
            'the_geom': 'geom',
            'layer_type': 'csv',
        }

        url = "{0}://{1}/layers/upload".format(scheme, host)
        client = requests.get("{0}://{1}".format(scheme, host))

        csrftoken = client.cookies['csrftoken']

        cookies.update(dict(csrftoken=csrftoken))

        headers = {'X-CSRFToken': csrftoken }
        return requests.post(url, cookies=cookies, headers=headers, data=data, files=files)

    def get(self, request, **kwargs):
        data = dict(request.query_params)
            
        query = self.get_configuration(data)

        query.update(dict(SERVICE='WFS'))

        result = self.get_response_from_geoserver('wfs', query)
        mem_file = self.create_csv(result)
        
        response = self.create_layer(mem_file, request.META.get('HTTP_HOST'), request.scheme, request.COOKIES)
        print response.content
        return Response(result, status=status.HTTP_200_OK)
