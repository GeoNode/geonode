from geonode.maps.models import Map
from geonode.maps.models import Layer
from django.contrib import admin

class LayerInline(admin.TabularInline):
    model = Layer

class MapAdmin(admin.ModelAdmin):
    inlines = [LayerInline,]


admin.site.register(Map, MapAdmin)
admin.site.register(Layer)
