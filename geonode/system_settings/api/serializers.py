from rest_framework.serializers import ModelSerializer
from geonode.system_settings.models import SystemSettings
from geonode.layers.models import Layer
from django.utils.translation import ugettext as _


class LayerSerializer(ModelSerializer):
    class Meta:
        model = Layer
        fields = '__all__'


class SystemSettingsSerializer(ModelSerializer):

    def to_representation(self, value):
        """
        Serialize tagged objects to a simple textual representation.
        """
        #import pdb;pdb.set_trace()
        if isinstance(value.content_object, Layer):
            serializer = LayerSerializer(value.content_object)
        else:
            raise Exception(_('Unexpected type of tagged object'))
        return serializer.data

    class Meta:
        model = SystemSettings
        exclude = ('created_date', 'last_modified')


