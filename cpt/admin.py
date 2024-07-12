from django.contrib import admin
from cpt.models import CategoryType, Category, Campaign
from django import forms
from geonode.geoserver.helpers import gs_catalog
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

class CampaignAdminForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['geoserver_workspace'].widget = forms.Select(choices=self.get_geoserver_workspaces())

    def get_geoserver_workspaces(self):
        try:
            workspaces = gs_catalog.get_workspaces()
            return [(ws.name, ws.name) for ws in workspaces]
        except Exception as e:
            return []

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    form = CampaignAdminForm
    list_display = (
        'campaign_id', 'campaign_name', 'campaign_url_name', 'campaing_title', 
        'campaing_short_description', 'campaing_detailed_description', 
        'start_date', 'end_date', 'category_type', 'geoserver_workspace', 
        'allow_drawings', 'rate_enabled'
    )
    search_fields = ('campaign_name', 'campaign_url_name', 'category_type__name')
    list_filter = ('category_type', 'start_date', 'end_date')
