from rest_framework import serializers
from cpt.models import  Category, Campaign,Form, Rating
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
import json 
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos.error import GEOSException
from django.contrib.gis.gdal.error import GDALException  # Correct import for GDALException

import logging
logger = logging.getLogger(__name__)

class CampaignsListSerializer(serializers.ModelSerializer):
    total_comment_count = serializers.SerializerMethodField()
    geoserver_layers = serializers.SerializerMethodField()
    class Meta:
        model = Campaign
        fields = [ 'campaing_title','campaign_url_name', 'campaing_short_description','geoserver_layers','start_date','end_date','total_comment_count']
    
    def get_geoserver_layers(self, obj):
        """
        Convert related GeoserverLayers instances to "workspace:layername" format.
        """
        layers = obj.geoserver_layers.all()  # Get all related layers
        
        # Convert to "workspace:layername" format
        formatted_layers = [f"{layer}" for layer in layers]
        return formatted_layers
    def get_total_comment_count(self, obj):
        # Formlar ve rating'ler üzerinden toplam yorum sayısını hesaplayın
        unique_form_ids = Form.objects.filter(campaign=obj).values_list('id', flat=True)
        rating_count_without_form = Rating.objects.filter(campaign=obj, form__isnull=True).count()
        total_comment_count = len(unique_form_ids) + rating_count_without_form
        return total_comment_count
    
class CampaignSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()
    geoserver_layers = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = [
            'campaign_id', 'campaign_name', 'campaign_url_name', 'rate_enabled',
            'campaing_title', 'campaing_detailed_description', 'start_date',
            'end_date', 'category_type', 'categories', 'geoserver_layers',
            'form_enabled', 'allow_drawings',
        ]

    def get_categories(self, obj):
        categories = Category.objects.filter(category_type=obj.category_type)
        return [category.name for category in categories]
    def get_geoserver_layers(self, obj):
        """
        Convert related GeoserverLayers instances to "workspace:layername" format.
        """
        layers = obj.geoserver_layers.all()  # Get all related layers
        
        # Convert to "workspace:layername" format
        formatted_layers = [f"{layer}" for layer in layers]
        return formatted_layers



class RatingSerializer(serializers.ModelSerializer):
    campaign_id = serializers.IntegerField(write_only=True)
    class Meta:
        model = Rating
        fields = ['campaign_id', 'rating'] 
    def validate_campaign_id(self, value):
        """
        Control campaign_id and validate if it exists.
        """
        if not Campaign.objects.filter(campaign_id=value).exists():
            raise serializers.ValidationError("Campaign not found.")
        return value
    def create(self, validated_data):
        campaign_id = validated_data.pop('campaign_id')
        
        campaign = Campaign.objects.get(campaign_id=campaign_id)  
        rating = Rating.objects.create(campaign=campaign, **validated_data)
        return rating

class GeoJSONField(serializers.Field):
    def to_internal_value(self, data):
        """
        Convert incoming GeoJSON data to a GEOSGeometry object.
        Handles both Feature and FeatureCollection.
        """
        try:
            geojson_type = data.get('type')
            
            if geojson_type == 'Feature':
                # Extract the geometry part from the Feature and convert it to GEOSGeometry
                geometry = data.get('geometry')
                if geometry:
                    return GEOSGeometry(json.dumps(geometry))
                else:
                    raise serializers.ValidationError("Invalid Feature data: Geometry is missing.")
            
            elif geojson_type == 'FeatureCollection':
                # Extract geometries from the FeatureCollection
                geometries = [GEOSGeometry(json.dumps(feature['geometry'])) for feature in data['features']]
                return geometries  # Return a list of GEOSGeometry objects
            
            else:
                raise serializers.ValidationError("Invalid GeoJSON data: Must be a Feature or FeatureCollection.")
        
        except (GEOSException, GDALException, ValueError) as e:
            logger.error(f"Invalid GeoJSON data: {e}")
            raise serializers.ValidationError(f"Invalid GeoJSON data: {e}")

    def to_representation(self, value):
        """
        Convert GEOSGeometry object(s) back to GeoJSON for output.
        """
        if isinstance(value, list):
            # Handle the case where value is a list of geometries (FeatureCollection)
            features = [{"type": "Feature", "geometry": json.loads(geom.geojson), "properties": {}} for geom in value]
            return {"type": "FeatureCollection", "features": features}
        else:
            # Handle individual geometry (Feature)
            return {"type": "Feature", "geometry": json.loads(value.geojson), "properties": {}}
        
class FormSerializer(serializers.ModelSerializer):
    feedback_location = GeoJSONField()  # Handle GeoJSON input/output for location
    feedback_geometry = GeoJSONField(required=False)  # Handle GeoJSON for geometry
    campaign_id = serializers.IntegerField(write_only=True)  # Accept campaign_id from the request
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.all(), required=False)  # Make the campaign field optional

    class Meta:
        model = Form
        fields = '__all__'
    
    def validate_campaign_id(self, value):
        """
        Validate that the campaign_id exists.
        """
        if not Campaign.objects.filter(campaign_id=value).exists():
            raise serializers.ValidationError("Campaign not found.")
        return value

    def create(self, validated_data):
        # Extract the campaign_id from the validated data
        campaign_id = validated_data.pop('campaign_id')
        
        # Retrieve the Campaign instance
        campaign = Campaign.objects.get(campaign_id=campaign_id)
        
        # Set the campaign in the validated_data
        validated_data['campaign'] = campaign
        
        # Create the Form instance with the campaign and other validated data
        form = Form.objects.create(**validated_data)
        return form
