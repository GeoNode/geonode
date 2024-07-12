from django.contrib import admin
from .models import CategoryType, Category, Campaign

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

# Registering the Campaign model
@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ('campaign_id', 'campaign_name', 'campaign_url_name', 'allow_drawings', 'rate_enabled', 'campaing_title', 'campaing_short_description',\
                    'campaing_detailed_description','start_date', 'end_date', 'category_type')
    search_fields = ('campaign_name', 'campaign_url_name', 'category_type__name')
    list_filter = ('category_type', 'start_date', 'end_date')




# admin.site.register(Campaign)
# admin.site.register(Category)
# admin.site.register(CategoryType, CategoryTypeAdmin)
