from django.contrib import admin
from geonode.layers.models import Attribute
from .models import DataTable, TableJoin, JoinTarget, JoinTargetFormatType, GeocodeType

class DataTableAdmin(admin.ModelAdmin):
    model = DataTable
    list_display = (
        'id',
        'title',
        'table_name',
        'tablespace')
    list_display_links = ('title',)


class TableJoinAdmin(admin.ModelAdmin):
    model = TableJoin 

class JoinTargetAdmin(admin.ModelAdmin):
    model = JoinTarget

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attribute':
            kwargs["queryset"] = Attribute.objects.filter(
                resource=request.GET.get('layer'))
        return super(JoinTargetAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)

admin.site.register(DataTable, DataTableAdmin)
admin.site.register(TableJoin, TableJoinAdmin)
admin.site.register(JoinTarget, JoinTargetAdmin)
admin.site.register(JoinTargetFormatType)
admin.site.register(GeocodeType)
