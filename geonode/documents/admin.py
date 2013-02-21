from django.contrib import admin
from geonode.documents.models import Document
from geonode.base.models import ContactRole

class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'date', 'category')
    list_display_links = ('id',)
    list_filter  = ('date', 'date_type', 'constraints_use', 'category')
    search_fields = ('title', 'abstract', 'purpose',)
    date_hierarchy = 'date'

admin.site.register(Document, DocumentAdmin)