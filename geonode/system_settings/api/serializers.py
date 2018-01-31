from rest_framework import serializers
from geonode.system_settings.models import SystemSettings
from geonode.layers.models import Layer
from django.utils.translation import ugettext as _
import json


class LayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Layer
        fields = ('uuid', 'title', 'typename',)
        # fields = '__all__'


class SystemSettingsSerializer(serializers.ModelSerializer):

    content_object = serializers.SerializerMethodField()

    def get_content_object(self, obj):
        if isinstance(obj.content_object, Layer):
            serializer = LayerSerializer(obj.content_object)
        else:
            raise Exception(_('Unexpected type of tagged object'))
        return serializer.data

    class Meta:
        model = SystemSettings
        fields = ('settings_code', 'value', 'content_object',)
        read_only_fields = ('content_object',)

