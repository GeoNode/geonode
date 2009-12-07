from geonode.maps.models import Map, Layer, MapLayer
from django.contrib import admin

class MapLayerInline(admin.TabularInline):
    model = MapLayer

class MapAdmin(admin.ModelAdmin):
    inlines = [MapLayerInline,]


admin.site.register(Map, MapAdmin)
admin.site.register(MapLayer)
admin.site.register(Layer)
