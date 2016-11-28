from django.contrib import admin

from geonode.datarequests.models import DataRequestProfile, RequestRejectionReason

class DataRequestProfileAdmin(admin.ModelAdmin):
    model = DataRequestProfile
    list_display_links = ('id','username')

    list_display = (
        'id',
        'request_status',
        'username',
        'first_name',
        'middle_name',
        'last_name',
        'organization',
        'organization_type',)
    list_filter = ('request_status', 'organization_type')
    search_fields = ('username', 'first_name', 'middle_name', 'last_name', 'organization','organization_type', )


admin.site.register(DataRequestProfile, DataRequestProfileAdmin)
admin.site.register(RequestRejectionReason)
