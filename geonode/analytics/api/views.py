
from geonode.analytics.models.MapLoad import MapLoad
from geonode.analytics.models.Visitor import Visitor
from geonode.analytics.models.LayerLoad import LayerLoad
from geonode.analytics.models.PinpointUserActivity import PinpointUserActivity

from geonode.layers.models import Layer
from geonode.maps.models import Map

from geonode.analytics.api.serializers import (
    MapLoadSerializer,
    LayerLoadSerializer,
    VisitorSerializer,
    PinpointUserActivitySerializer
)

from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_gis.filters import InBBoxFilter

# Create your views here.


class MapLoadListAPIView(ListAPIView):
    queryset = MapLoad.objects.all()
    serializer_class = MapLoadSerializer
    # bbox_filter_field = 'map'
    # filter_backends = (InBBoxFilter,)

    # set permission for admin


class LayerLoadListAPIView(ListAPIView):
    queryset = LayerLoad.objects.all()
    serializer_class = LayerLoadSerializer
    # import pdb;pdb.set_trace()
    # bbox_filter_field = 'layer'
    # filter_backends = (InBBoxFilter,)

    # set permission for admin


class VisitorListAPIView(ListAPIView):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer

    # set permission for admin


class PinpointUserActivityListAPIView(ListAPIView):
    queryset = PinpointUserActivity.objects.select_related().all()
    serializer_class = PinpointUserActivitySerializer
    bbox_filter_field = 'point'
    filter_backends = (InBBoxFilter,)

    # set permission for admin


class PinpointUserActivityCreateAPIView(APIView):

    def post(self, request, format=None):
        data = request.data

        pinpoint_user_activity = PinpointUserActivity()
        pinpoint_user_activity.user = None if request.user.id is None else request.user
        pinpoint_user_activity.map = None if str(data['map']) == '' else Map.objects.get(id=int(data['map']))
        pinpoint_user_activity.layer = Layer.objects.get(id=int(data['layer']))
        pinpoint_user_activity.ip = str(request.environ['REMOTE_ADDR'])
        pinpoint_user_activity.agent = str(request.environ['HTTP_USER_AGENT'])
        pinpoint_user_activity.activity_type = str(data['activity_type'])
        pinpoint_user_activity.latitude = None if str(data['latitude']) == '' else float(data['latitude'])
        pinpoint_user_activity.longitude = None if str(data['longitude']) == '' else float(data['longitude'])
        pinpoint_user_activity.point = None

        try:
            pinpoint_user_activity.save()
        except (AssertionError, AttributeError) as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class VisitorCreateAPIView(APIView):

    def post(self, request, format=None):

        data = request.data

        visitor = Visitor()
        visitor.user = None if request.user.id is None else request.user
        visitor.page_name = str(request.environ['PATH_INFO'])
        visitor.latitude = None if str(data['latitude']) == '' else float(data['latitude'])
        visitor.longitude = None if str(data['longitude']) == '' else float(data['longitude'])
        visitor.ip = str(request.environ['REMOTE_ADDR'])
        visitor.agent = str(request.environ['HTTP_USER_AGENT'])

        try:
            visitor.save()
        except (AssertionError, AttributeError) as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class LayerLoadCreateAPIView(APIView):

    def post(self, request, format=None):

        data = request.data

        # import pdb;pdb.set_trace()

        layer_load = LayerLoad()
        layer_load.user = None if request.user.id is None else request.user
        layer_load.layer = Layer.objects.get(id=int(data['layer']))
        layer_load.latitude = None if str(data['latitude']) == '' else float(data['latitude'])
        layer_load.longitude = None if str(data['longitude']) == '' else float(data['longitude'])
        layer_load.ip = str(request.environ['REMOTE_ADDR'])
        layer_load.agent = str(request.environ['HTTP_USER_AGENT'])

        # import pdb;pdb.set_trace()

        try:
            layer_load.save()
        except (AssertionError, AttributeError) as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)


class MapLoadCreateAPIView(APIView):

    def post(self, request, format=None):

        data = request.data

        # import pdb;pdb.set_trace()

        map_load = MapLoad()
        map_load.user = None if request.user.id is None else request.user
        map_load.map = Map.objects.get(id=int(data['map']))
        map_load.latitude = None if str(data['latitude']) == '' else float(data['latitude'])
        map_load.longitude = None if str(data['longitude']) == '' else float(data['longitude'])
        map_load.ip = str(request.environ['REMOTE_ADDR'])
        map_load.agent = str(request.environ['HTTP_USER_AGENT'])

        try:
            map_load.save()
        except (AssertionError, AttributeError) as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_200_OK)
