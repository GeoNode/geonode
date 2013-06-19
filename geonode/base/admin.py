from django.contrib import admin

from geonode.base.models import TopicCategory, ContactRole, ResourceBase, Link

class ResourceBaseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'date', 'category')
    list_display_links = ('id',)

class TopicCategoryAdmin(admin.ModelAdmin):
    model = TopicCategory
    list_display_links = ('name',)
    list_display = ('id', 'name', 'slug', 'description')
    exclude = ('layers_count', 'maps_count', 'documents_count')

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id','contact', 'resource', 'role')
    list_editable = ('contact', 'resource', 'role')

class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)

admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(ResourceBase, ResourceBaseAdmin)
admin.site.register(Link, LinkAdmin)
