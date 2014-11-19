from django.contrib import admin
from geonode.dataverse_private_layer.models import RegisteredApplication, WorldMapToken


"""
class WorldMapTokenInline(admin.TabularInline):
    model = DataFile
    extra= 1
    readonly_fields = ('update_time', 'create_time', 'md5', )
    fields = ('dataverse_user', 'data_file', 'application')
"""

class RegisteredApplicationAdmin(admin.ModelAdmin):
    #inlines = (WorldMapTokenInline)
    save_on_top = True
    list_display = ('name', 'ip_address', 'hostname', 'time_limit_minutes', 'contact_email', 'description' )
    readonly_fields = ('update_time', 'create_time', 'md5', 'time_limit_seconds')
admin.site.register(RegisteredApplication, RegisteredApplicationAdmin)


class WorldMapTokenAdmin(admin.ModelAdmin):
    save_on_top = True
    list_display = ( 'map_layer', 'token', 'has_expired', 'last_refresh_time', 'update_time' )
    list_filter = ('has_expired', )    
    readonly_fields = ('update_time', 'create_time', 'token',  )
admin.site.register(WorldMapToken, WorldMapTokenAdmin)
