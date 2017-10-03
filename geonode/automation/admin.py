from django.contrib import admin
from geonode.automation.models import AutomationJob, CephDataObjectResourceBase

# Register your models here.


class AutomationJobAdmin(admin.ModelAdmin):
    model = AutomationJob
    list_display_links = ('id',)
    list_display = (
        'id',
        'datatype',
        'input_dir',
        'processor',
        'date_submitted',
        'status',
        'status_timestamp'
    )
    search_fields = ('datatype', 'status', 'input_dir', 'processor')
    list_filter = ('datatype', 'status', 'processor', 'target_os')


class CephDataObjectResourceBaseAdmin(admin.ModelAdmin):
    model = CephDataObjectResourceBase
    list_display_links = ('id',)
    list_display = (
        'id',
        'grid_ref',
        'block_uid',
        'name',
        'file_hash',
        'data_class',
        'last_modified',
        'content_type',
        'size_in_bytes'
    )
    search_fields = ('grid_ref', 'name', 'data_class', 'block_uid__block_name')
    list_filter = ('data_class', 'content_type')


admin.site.register(AutomationJob, AutomationJobAdmin)
admin.site.register(CephDataObjectResourceBase, CephDataObjectResourceBaseAdmin)
