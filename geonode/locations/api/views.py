from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.http import JsonResponse
from django.db import connections

# Create your views here.


class NearestPointAPIView(APIView):

    permission_classes = (AllowAny,)

    def post(self, request, format=None):
        """
        # Data format
        {
            "layer_name": "zip_test_01",
            "latitude": 23.905811,
            "longitude": 90.409975
        }

        # Query for distance only
        SELECT ST_Distance(the_geom, 'SRID=4326;POINT(90.409975 23.905811)'::geometry) as d
        FROM zip_test_01
        ORDER BY d limit 10;

        # Query for distance, latitude and longitude
        SELECT ST_Distance(the_geom, 'SRID=4326;POINT(90.409975 23.905811)'::geometry) as distance,
        ST_X(ST_ClosestPoint(the_geom, 'SRID=4326;POINT(90.409975 23.905811)'::geometry)) as longitude,
        ST_Y(ST_ClosestPoint(the_geom, 'SRID=4326;POINT(90.409975 23.905811)'::geometry)) as latitude
        FROM zip_test_01
        ORDER BY distance limit 10;

        """
        layer_name = str(request.data.get("layer_name"))
        latitude = str(request.data.get("latitude"))
        longitude = str(request.data.get("longitude"))

        with connections['datastore'].cursor() as cursor:
            cursor.execute(
                "SELECT ROW_TO_JSON(t) FROM (SELECT ST_Distance(the_geom, 'SRID=4326;POINT(" +
                longitude + " " + latitude +
                ")'::geometry) as distance,ST_X(ST_ClosestPoint(the_geom, 'SRID=4326;POINT(" +
                longitude + " " + latitude +
                ")'::geometry)) as longitude, ST_Y(ST_ClosestPoint(the_geom, 'SRID=4326;POINT(" +
                longitude + " " + latitude +
                ")'::geometry)) as latitude FROM " +
                layer_name + " ORDER BY distance limit 10) t;")

            all_data = cursor.fetchall()
        # import pdb;pdb.set_trace()
        return JsonResponse(all_data, safe=False)
