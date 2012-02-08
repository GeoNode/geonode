from geonode.core.models import ObjectRole, UserObjectRoleMapping, GroupObjectRoleMapping, GenericObjectRoleMapping
from django.contrib import admin

admin.site.register(ObjectRole)
admin.site.register(UserObjectRoleMapping)
admin.site.register(GroupObjectRoleMapping)
admin.site.register(GenericObjectRoleMapping)