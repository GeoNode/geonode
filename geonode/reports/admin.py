from django.contrib import admin

# Register your models here.
from geonode.reports.models import DownloadCount, SUCLuzViMin

admin.site.register(DownloadCount)
admin.site.register(SUCLuzViMin)
