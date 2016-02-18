from django.contrib import admin
from guardian.models import UserObjectPermission, GroupObjectPermission

class UserObjectPermissionAdmin(admin.ModelAdmin):
    model = UserObjectPermission
    list_display_links = ('id',)
    list_display = (
        'id',
        'user',)
    list_filter = ('permission',)
    search_fields = ('user__username','content_type__name','object_pk','permission__name')
    
class GroupObjectPermissionAdmin(admin.ModelAdmin):
    model = GroupObjectPermission
    list_display_links = ('id',)
    list_display = (
        'id',
        'group',)
    list_filter = ('permission',)
    search_fields = ('group__name','content_type__name','object_pk','permission__name')
    
admin.site.register(UserObjectPermission, UserObjectPermissionAdmin)
admin.site.register(GroupObjectPermission, GroupObjectPermissionAdmin)
