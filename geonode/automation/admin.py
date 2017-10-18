from django.contrib import admin
from geonode.automation.models import AutomationJob

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



admin.site.register(AutomationJob, AutomationJobAdmin)
