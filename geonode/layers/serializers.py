from rest_framework.serializers import ModelSerializer

from .models import StyleExtension

class StyleExtensionSerializer(ModelSerializer):
    """
    Model serializer for Style Extension Model
    """
    class Meta:
        model = StyleExtension
        fields = ('id','style', 'json_field', 'sld_body')
        depth = 1
        