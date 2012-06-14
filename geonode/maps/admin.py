# -*- coding: utf-8 -*-
from geonode.maps.models import Map, MapLayer
from django.contrib import admin

class MapLayerInline(admin.TabularInline):
    model = MapLayer

class MapAdmin(admin.ModelAdmin):
    inlines = [MapLayerInline,]

admin.site.register(Map, MapAdmin)
admin.site.register(MapLayer)
