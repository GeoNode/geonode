from django.contrib import admin

from geonode.datarequests.models import DataRequestProfile, RequestRejectionReason, DataRequest, ProfileRequest, BaseRequest, LipadOrgType, SUC_Contact

#class BaseRequestAdmin(admin.ModelAdmin):
#   model = BaseRequest
#    search_fields = ('id','status','created')

class SUC_ContactAdmin(admin.ModelAdmin):
    model = SUC_Contact
    search_fields=('id', 'name','position','email_address')

class ProfileRequestAdmin(admin.ModelAdmin):
    model = ProfileRequest
    search_fields=('id', 'first_name','last_name','organization','status','administrator__username','email')

class DataRequestAdmin(admin.ModelAdmin):
    model = DataRequest
    search_fields=('id', 'status','request_letter__title','profile_request__first_name', 'profile_request__last_name')

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
        'organization_type',
        'jurisdiction_shapefile',
        'request_letter')
    list_filter = ('request_status', 'organization_type')
    search_fields = ('username', 'first_name', 'middle_name', 'last_name', 'organization','organization_type' )


#admin.site.register(BaseRequest,BaseRequestAdmin)
admin.site.register(SUC_Contact, SUC_ContactAdmin)
admin.site.register(ProfileRequest,ProfileRequestAdmin)
admin.site.register(DataRequest,DataRequestAdmin)
admin.site.register(DataRequestProfile, DataRequestProfileAdmin)
admin.site.register(RequestRejectionReason)
admin.site.register(LipadOrgType)
