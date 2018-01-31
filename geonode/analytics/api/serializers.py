
from geonode.analytics.models.MapLoad import MapLoad
from geonode.analytics.models.Visitor import Visitor
from geonode.analytics.models.LayerLoad import LayerLoad
from geonode.analytics.models.PinpointUserActivity import PinpointUserActivity

from rest_framework.serializers import ModelSerializer
from rest_framework_gis.serializers import GeoFeatureModelSerializer


class MapLoadSerializer(ModelSerializer):

    class Meta:
        model = MapLoad()
        # geo_field = "map"
        fields = ('user', 'map', 'latitude', 'longitude', 'agent', 'ip')


class LayerLoadSerializer(ModelSerializer):

    class Meta:
        model = LayerLoad()
        # geo_field = "layer"
        fields = ('user', 'layer', 'latitude', 'longitude', 'agent', 'ip')


class VisitorSerializer(ModelSerializer):

    class Meta:
        model = Visitor()
        fields = ('user', 'page_name', 'latitude', 'longitude', 'agent', 'ip')


class PinpointUserActivitySerializer(GeoFeatureModelSerializer):

    class Meta:
        model = PinpointUserActivity()
        geo_field = "point"
        fields = ('user', 'layer', 'map', 'activity_type', 'latitude', 'longitude', 'agent', 'ip')
