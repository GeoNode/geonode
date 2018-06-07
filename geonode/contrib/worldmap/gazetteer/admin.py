from django.contrib import admin

from .models import GazetteerEntry, GazetteerAttribute


class GazetteerEntryAdmin(admin.ModelAdmin):
    list_display = (
        'layer_name',
        'layer_attribute',
        'feature_type',
        'place_name',
        'project',
        'username',
    )


class GazetteerAttributeAdmin(admin.ModelAdmin):
    list_display = (
        'layer_name',
        'attribute',
        'in_gazetteer',
        'is_start_date',
        'is_end_date',
        'date_format',
    )


admin.site.register(GazetteerEntry, GazetteerEntryAdmin)
admin.site.register(GazetteerAttribute, GazetteerAttributeAdmin)
