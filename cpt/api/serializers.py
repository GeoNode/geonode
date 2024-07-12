from rest_framework import serializers
from cpt.models import CategoryType, Category, Campaign


class CampaignsListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = [ 'campaing_title','campaign_url_name', 'campaing_short_description']


class CampaignSerializer(serializers.ModelSerializer):
    categories = serializers.SerializerMethodField()

    class Meta:
        model = Campaign
        fields = ['campaign_id', 'campaign_name', 'campaign_url_name', 'allow_drawings', 'rate_enabled', 'campaing_title', 'campaing_detailed_description', 'start_date', 'end_date', 'category_type', 'categories']

    def get_categories(self, obj):
        categories = Category.objects.filter(category_type=obj.category_type)
        return [category.name for category in categories]
