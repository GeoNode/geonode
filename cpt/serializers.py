from rest_framework import serializers
from cpt.models import  Category, Campaign,Form, Rating
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
import json 


class CampaignsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [ 'campaing_title','campaign_url_name', 'campaing_short_description','geoserver_workspace','start_date','end_date']


class CampaignSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = ['campaign_id', 'campaign_name', 'campaign_url_name',  'rate_enabled', 'campaing_title', 'campaing_detailed_description', 'start_date', 'end_date', 'category_type', 'categories', 'geoserver_workspace',
                  'form_enabled','allow_drawings']

    def get_categories(self, obj):
        categories = Category.objects.filter(category_type=obj.category_type)
        return [category.name for category in categories]


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'


class GeoJSONField(serializers.Field):
    def to_internal_value(self, data):
        """
        Convert incoming GeoJSON data to a GEOSGeometry object.
        """
        try:
            return GEOSGeometry(json.dumps(data))
        except (GEOSException, ValueError) as e:
            raise serializers.ValidationError(f"Invalid GeoJSON data: {e}")

    def to_representation(self, value):
        """
        Convert GEOSGeometry object back to GeoJSON for output.
        """
        return json.loads(value.geojson)  # Convert back to GeoJSON

class FormSerializer(serializers.ModelSerializer):
    feedback_location = GeoJSONField()  # Custom field to handle GeoJSON
    feedback_geometry = serializers.JSONField(required=False)  # Store GeoJSON as raw string

    class Meta:
        model = Form
        fields = '__all__'
    
    def validate_feedback_geometry(self, value):
        """
        Validate feedback_geometry, assuming it's passed as a GeoJSON dict.
        """
        try:
            if isinstance(value, dict):
                json.dumps(value)  # Ensure it's a valid JSON
                return json.dumps(value)  # Convert to string for storage
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Invalid GeoJSON provided for feedback_geometry: {str(e)}")
