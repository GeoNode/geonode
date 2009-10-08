from geonode.layers.models import Layer
from django.contrib import admin

class MapAdmin(admin.ModelAdmin):
    model = Layer 

admin.site.register(Layer, MapAdmin)

