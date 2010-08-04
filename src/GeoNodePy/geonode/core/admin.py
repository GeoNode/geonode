from geonode.core.models import ObjectRole, UserObjectRoleMapping, GenericObjectRoleMapping
from django.contrib import admin

admin.site.register(ObjectRole)
admin.site.register(UserObjectRoleMapping)
admin.site.register(GenericObjectRoleMapping)