from django.contrib import admin
from geonode.analytics.models import MapLoad, Visitor, LayerLoad, PinpointUserActivity


# Register your models here.
admin.site.register(MapLoad)

admin.site.register(Visitor)

admin.site.register(LayerLoad)

admin.site.register(PinpointUserActivity)
