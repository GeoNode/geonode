from django.contrib import admin
from geosafe.models import Metadata


# Register your models here.
class MetadataAdmin(admin.ModelAdmin):
    list_display = (
        'layer',
        'user',
        'date_created'
    )


admin.site.register(Metadata, MetadataAdmin)
