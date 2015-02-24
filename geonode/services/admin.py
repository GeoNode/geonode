from django.contrib import admin

from geonode.services.models import Service
from geonode.base.admin import ResourceBaseAdminForm


class ServiceAdminForm(ResourceBaseAdminForm):

    class Meta:
        model = Service


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'method')
    list_display_links = ('id', 'name', )
    list_filter = ('type', 'method')
    form = ServiceAdminForm

admin.site.register(Service, ServiceAdmin)
