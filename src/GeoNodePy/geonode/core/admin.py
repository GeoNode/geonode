from django.contrib import admin

from geonode.core.models import ObjectRole, UserObjectRoleMapping, GenericObjectRoleMapping

admin.site.register(ObjectRole)
admin.site.register(UserObjectRoleMapping)
admin.site.register(GenericObjectRoleMapping)
