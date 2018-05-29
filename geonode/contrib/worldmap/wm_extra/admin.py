from django.contrib import admin

from .models import ExtLayer, ExtMap, ExtLayerAttribute, LayerStats, MapStats, Endpoint, Action


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


class ExtLayerAttributeAdmin(admin.ModelAdmin):
    list_display = (
        'layer_name',
        'searchable',
    )


class EndpointAdmin(admin.ModelAdmin):
    list_display = ('id', 'description', 'owner', 'url')
    list_display_links = ('id',)
    search_fields = ['description', 'url']


class ActionAdmin(admin.ModelAdmin):
    """
    Admin for Action.
    """
    list_display = ('id', 'timestamp', 'action_type', 'description', )
    list_filter = ('action_type', )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)


admin.site.register(ExtLayer, ExtLayerAdmin)
admin.site.register(ExtMap, ExtMapAdmin)
admin.site.register(LayerStats, LayerStatsAdmin)
admin.site.register(MapStats, MapStatsAdmin)
admin.site.register(ExtLayerAttribute, ExtLayerAttributeAdmin)
admin.site.register(Endpoint, EndpointAdmin)
admin.site.register(Action, ActionAdmin)
