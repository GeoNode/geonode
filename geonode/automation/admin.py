from django.contrib import admin
from geonode.automation.models import *

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
        'size_in_bytes',
        'file_hash',
        'name',
        'last_modified',
        'content_type',
        'data_class',
        'grid_ref',
        'block_uid'
    )

admin.site.register(AutomationJob, AutomationJobAdmin)
admin.site.register(CephDataObjectResourceBase, CephDataObjectResourceBaseAdmin)
