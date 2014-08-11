from geonode.classification.models import ClassificationMethod, ColorRamp

from django.contrib import admin


class ClassificationMethodAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ('display_name',  'value_name',)
    list_display = ('display_name', 'value_name', 'active', 'sort_order', 'is_string_usable', )
    list_filter = ('active', 'is_string_usable', )   
    readonly_fields = ('modified', 'created')
admin.site.register(ClassificationMethod, ClassificationMethodAdmin)


class ColorRampAdmin(admin.ModelAdmin):
    save_on_top = True
    search_fields = ('display_name',  'value_name',)
    list_display = ('display_name', 'value_name', 'active', 'sort_order', 'start_color', 'end_color')
    readonly_fields = ('modified', 'created')
    list_filter = ('active', )   
    
admin.site.register(ColorRamp, ColorRampAdmin)

