from django.contrib import admin
from django import forms
from geonode.maps.models import Layer, LayerAttribute
from .models import DataTable, DataTableAttribute, TableJoin, JoinTarget, JoinTargetFormatType, GeocodeType, LatLngTableMappingRecord
import string

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
    list_filter  = ('datatable',)# 'layer', )



class TableJoinAdmin(admin.ModelAdmin):
    model = TableJoin


class JoinTargetAdminForm(forms.ModelForm):
    """
    Limit the JoinTarget Layer and LayerAttribute choices.
    (If not limited, the page can take many minutes--or never load
        e.g. listing 20k+ layers and all of the attributes in those layers
    )
    """
    def __init__(self, *args, **kwargs):
        super(JoinTargetAdminForm, self).__init__(*args, **kwargs)

        selected_layer_id = kwargs.get('initial', {}).get('layer', None)

        # Is this an existing/saved Join Target?
        #
        if self.instance and self.instance.id:
            # Yes, limit choices to the chosen layer and its attributes
            #
            self.fields['layer'].queryset = Layer.objects.filter(\
                                    pk=self.instance.layer.id)
            self.fields['attribute'].queryset = LayerAttribute.objects.filter(\
                                    layer=self.instance.layer.id)

        elif selected_layer_id and selected_layer_id.isdigit():
            self.fields['layer'].queryset = Layer.objects.filter(\
                                            pk=selected_layer_id)
            self.fields['attribute'].queryset = LayerAttribute.objects.filter(\
                                            layer=selected_layer_id)


        elif 'initial' in kwargs:
            # We can't "afford" to list everything.
            # Don't list any layers or their attributes
            #   - An admin template instructs the user on how
            #       to add a new JoinTarget via the Layer admin
            #
            self.fields['layer'].queryset = Layer.objects.none()
            self.fields['attribute'].queryset = LayerAttribute.objects.none()



class JoinTargetAdmin(admin.ModelAdmin):
    model = JoinTarget
    form = JoinTargetAdminForm
    list_display = ('name', 'layer', 'attribute', 'geocode_type', 'expected_format', 'year')
    readonly_fields = ('return_to_layer_admin', )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            layer_id = request.GET.get('layer', 'nope')
            if layer_id.isdigit():
                kwargs["queryset"] = LayerAttribute.objects.filter(
                                        layer=request.GET.get('layer'))
        return super(JoinTargetAdmin, self).formfield_for_foreignkey(\
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
