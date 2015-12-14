from geonode.core.models import ObjectRole, UserObjectRoleMapping, GenericObjectRoleMapping
from django.contrib import admin

admin.site.register(ObjectRole)
admin.site.register(UserObjectRoleMapping)

class GenericObjectRoleMappingAdmin(admin.ModelAdmin):
    save_on_top = True
    list_filter = ('subject', 'object_id')
    list_display = ('subject', 'object', 'object_ct', 'object_id',  'role')
admin.site.register(GenericObjectRoleMapping, GenericObjectRoleMappingAdmin)
#admin.site.register(GenericObjectRoleMapping)