# -*- coding: utf-8 -*-

from geonode.analytics.models import Analysis
from django.contrib import admin

class AnalysisAdmin(admin.ModelAdmin):
    list_display_links = ('title',)
    list_display = ('id','title', 'owner')
    list_filter = ('owner', 'category',)
    search_fields = ('title', 'abstract', 'purpose', 'owner__profile__name',)

admin.site.register(Analysis, AnalysisAdmin)
