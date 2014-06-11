from django.contrib import admin
from geonode.documents.models import Document
from modeltranslation.admin import TranslationAdmin

class DocumentAdmin(TranslationAdmin):
    list_display = ('id', 'title', 'date', 'category')
    list_display_links = ('id',)
    list_filter  = ('date', 'date_type', 'restriction_code_type', 'category')
    search_fields = ('title', 'abstract', 'purpose',)
    date_hierarchy = 'date'

admin.site.register(Document, DocumentAdmin)
