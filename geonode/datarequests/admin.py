from django.contrib import admin

from geonode.datarequests.models import DataRequestProfile, RequestRejectionReason, DataRequest, ProfileRequest

admin.site.register(ProfileRequest)
admin.site.register(DataRequest)
admin.site.register(DataRequestProfile)
admin.site.register(RequestRejectionReason)
