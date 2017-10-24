from django.contrib import admin
from geonode.contrib.dataverse_permission_links.models import DataversePermissionLink
from geonode.contrib.dataverse_permission_links.forms import DataversePermissionLinkForm

class DataversePermissionLinkAdmin(admin.ModelAdmin):
    form = DataversePermissionLinkForm
    save_on_top = True
    search_fields = ('dataverse_username',  'worldmap_username')
    list_display = ('name',
                    'is_active',
                    'dataverse_username',
                    'worldmap_username',
                    'worldmap_user',
                    'modified',
                    'created')

    list_filter = ('is_active',)
    readonly_fields = ('modified', 'created',)

admin.site.register(DataversePermissionLink, DataversePermissionLinkAdmin)
