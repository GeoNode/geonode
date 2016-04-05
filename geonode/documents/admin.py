from django.contrib import admin
from geonode.documents.models import Document
from geonode.base.admin import MediaTranslationAdmin, ResourceBaseAdminForm


class DocumentAdminForm(ResourceBaseAdminForm):

    class Meta:
        model = Document
        exclude = (
            'resource',
        )


class DocumentAdmin(MediaTranslationAdmin):
    list_display = ('id', 'title', 'date', 'categories_str')
    list_display_links = ('id',)
    list_filter = ('date', 'date_type', 'restriction_code_type', 'categories')
    search_fields = ('title', 'abstract', 'purpose',)
    date_hierarchy = 'date'
    form = DocumentAdminForm

admin.site.register(Document, DocumentAdmin)
