from django.contrib import admin

from geonode.datarequests.models import DataRequestProfile, RequestRejectionReason


admin.site.register(DataRequestProfile)
admin.site.register(RequestRejectionReason)
