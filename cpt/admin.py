from django.contrib import admin
from cpt.models import CategoryType, Category, Campaign,GeoserverLayers
from django import forms
from geonode.geoserver.helpers import gs_catalog
from django.core.exceptions import ValidationError
"""
parametrelerin ne oldugu ile ilgili kuuck infoyu admin panelde gostermek icin ne yapmali

"""

# Registering the CategoryType model
@admin.register(CategoryType)
class CategoryTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

# Registering the Category model
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_id', 'name', 'category_type')
    search_fields = ('name', 'category_type__name')
    list_filter = ('category_type',)

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = (
        'campaign_id', 'campaign_name', 'campaign_url_name', 'campaing_title', 
        'campaing_short_description', 'campaing_detailed_description', 
        'start_date', 'end_date', 'rate_enabled', 'category_type', 
        'form_enabled', 'allow_drawings'
    )
    search_fields = ('campaign_name', 'campaign_url_name', 'category_type__name')
    list_filter = ('category_type', 'start_date', 'end_date')
    
    filter_horizontal = ('geoserver_layers',)  # Enable the dual-pane selection UI for layers

    def get_form(self, request, obj=None, **kwargs):
        # Update the GeoserverLayers whenever the form is loaded
        GeoserverLayers.update_layers()
        return super().get_form(request, obj, **kwargs)