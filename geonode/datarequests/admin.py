from django.contrib import admin

from geonode.datarequests.models import DataRequestProfile, RequestRejectionReason, DataRequest, ProfileRequest

class ProfileRequestAdmin(admin.ModelAdmin):
    model = ProfileRequest
    search_fields=('id', 'last_name','organization','status','administrator',)

class DataRequestAdmin(admin.ModelAdmin):
    model = DataRequest
    search_fields=('id', 'status','request_letter__title')

admin.site.register(ProfileRequest,ProfileRequestAdmin)
admin.site.register(DataRequest,DataRequestAdmin)
admin.site.register(DataRequestProfile)
admin.site.register(RequestRejectionReason)
