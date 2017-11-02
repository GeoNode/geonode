from django.contrib import admin
from geonode.analytics.models import MapLoad, Visitor, LayerLoad, PinpointUserActivity


# Register your models here.
admin.site.register(MapLoad.MapLoad)

admin.site.register(Visitor.Visitor)

admin.site.register(LayerLoad.LayerLoad)

admin.site.register(PinpointUserActivity.PinpointUserActivity)
