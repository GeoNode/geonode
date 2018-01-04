from rest_framework import serializers
from .models import MapLayer


class MapLayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapLayer
        fields = '__all__'