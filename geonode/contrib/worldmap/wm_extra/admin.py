from django.contrib import admin

from .models import ExtLayer, ExtMap, LayerStats, MapStats, Endpoint


class ExtLayerAdmin(admin.ModelAdmin):
    list_display = (
        'layer',
        'last_modified',
        'gazetteer_project',
        'in_gazetteer',
        'searchable',
        'last_modified',
    )

class ExtMapAdmin(admin.ModelAdmin):
    list_display = (
        'map',
        'content_map',
    )

class LayerStatsAdmin(admin.ModelAdmin):
    list_display = (
        'layer',
        'visits',
        'uniques',
        'last_modified',
    )

class MapStatsAdmin(admin.ModelAdmin):
    list_display = (
        'map',
        'visits',
        'uniques',
        'last_modified',
    )

class EndpointAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'owner', 'url')
    list_display_links = ('id',)
    search_fields = ['description', 'url']


admin.site.register(ExtLayer, ExtLayerAdmin)
admin.site.register(ExtMap, ExtMapAdmin)
admin.site.register(LayerStats, LayerStatsAdmin)
admin.site.register(MapStats, MapStatsAdmin)
admin.site.register(Endpoint, EndpointAdmin)
