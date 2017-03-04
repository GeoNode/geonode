from django.contrib import admin
from geonode.eula.models import AnonDownloader
# Register your models here.

class AnonDownloaderAdmin(admin.ModelAdmin):
    model = AnonDownloader
    list_display_links = ('id',)
    list_display = (
        'id',
        'anon_first_name',
        'anon_last_name',
        'anon_email',
        'anon_organization',
        'anon_orgtype',
        'anon_orgother',
        'anon_purpose',
        'date',
        'anon_layer',
        'anon_document')
    search_fields = ('anon_first_name', 'anon_last_name', 'anon_email', 'anon_organization', 'anon_purpose',)

admin.site.register(AnonDownloader, AnonDownloaderAdmin)
