from django.contrib import admin
from geonode.maps.models import LayerAttribute
from .models import DataTable, DataTableAttribute, TableJoin, JoinTarget, JoinTargetFormatType, GeocodeType, LatLngTableMappingRecord

class DataTableAdmin(admin.ModelAdmin):
    model = DataTable
    search_fields = ('title',)

    list_display = (
        'id',
        'title',
        'owner',
        'created',
        'table_name',
        'tablespace')
    list_display_links = ('title',)


class DataTableAttributeAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'attribute_label', 'datatable', 'attribute_type', 'searchable')
    list_filter  = ('datatable', 'searchable', 'attribute_type')

class LatLngTableMappingRecordAdmin(admin.ModelAdmin):
    search_fields = ('title',)
    list_display = ('datatable', 'lat_attribute', 'lng_attribute', 'layer', 'mapped_record_count', 'unmapped_record_count', 'created')
    list_filter  = ('datatable', 'layer', )



class TableJoinAdmin(admin.ModelAdmin):
    model = TableJoin


class JoinTargetAdmin(admin.ModelAdmin):
    model = JoinTarget
    list_display = ('name', 'layer', 'attribute', 'geocode_type', 'expected_format', 'year')
    readonly_fields = ('return_to_layer_admin', )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            if request.GET.get('layer', None) is not None:
                kwargs["queryset"] = LayerAttribute.objects.filter(
                                        layer=request.GET.get('layer'))
        return super(JoinTargetAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

class JoinTargetFormatTypeAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    readonly_fields = ('created', 'modified')


admin.site.register(DataTable, DataTableAdmin)
admin.site.register(DataTableAttribute, DataTableAttributeAdmin)
admin.site.register(TableJoin, TableJoinAdmin)
admin.site.register(JoinTarget, JoinTargetAdmin)
admin.site.register(JoinTargetFormatType, JoinTargetFormatTypeAdmin)
admin.site.register(GeocodeType)
admin.site.register(LatLngTableMappingRecord, LatLngTableMappingRecordAdmin)
