from geonode.core.models import UserRowLevelPermission, GenericRowLevelPermission
from django.contrib import admin

admin.site.register(UserRowLevelPermission)
admin.site.register(GenericRowLevelPermission)