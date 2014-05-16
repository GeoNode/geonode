from django.contrib import admin

from geonode.contrib.services.models import Service

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'method')
    list_display_links = ('id', 'name', )
    list_filter = ('type', 'method')

admin.site.register(Service, ServiceAdmin)
