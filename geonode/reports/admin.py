from django.contrib import admin

# Register your models here.
from geonode.reports.models import DownloadCount, SUCLuzViMin, DownloadTracker

class DownloadCountAdmin(admin.ModelAdmin):
    model = DownloadCount
    list_display_links = ('id',)
    list_display = (
        'id',
        'date',
        'category',
        'chart_group',
        'download_type',
        'count')

admin.site.register(DownloadCount, DownloadCountAdmin)

class SUCLuzViMinAdmin(admin.ModelAdmin):
    model = SUCLuzViMin
    list_display_links = ('id',)
    list_display = (
        'id',
        'province',
        'suc',
        'luzvimin')

admin.site.register(SUCLuzViMin, SUCLuzViMinAdmin)

class DownloadTrackerAdmin(admin.ModelAdmin):
    model = DownloadTracker
    list_display_links = ('id',)
    list_display = (
        'id',
        'timestamp',
        'actor',
        'title',
        'resource_type',
        'dl_type',
        'keywords')

admin.site.register(DownloadTracker, DownloadTrackerAdmin)
