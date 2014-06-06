from django.contrib import admin
from geonode.documents.models import Document

import autocomplete_light

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'date', 'category')
    list_display_links = ('id',)
    list_filter  = ('date', 'date_type', 'restriction_code_type', 'category')
    search_fields = ('title', 'abstract', 'purpose',)
    date_hierarchy = 'date'
    form = autocomplete_light.modelform_factory(Document)

admin.site.register(Document, DocumentAdmin)
