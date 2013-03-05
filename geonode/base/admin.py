from django.contrib import admin

from geonode.base.models import TopicCategory, ContactRole, ResourceBase

class ResourceBaseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'date', 'category')
    list_display_links = ('id',)

class TopicCategoryAdmin(admin.ModelAdmin):
    model = TopicCategory
    list_display_links = ('name',)
    list_display = ('id', 'name', 'slug', 'description')

class ContactRoleAdmin(admin.ModelAdmin):
    model = ContactRole
    list_display_links = ('id',)
    list_display = ('id','contact', 'resource', 'role')
    list_editable = ('contact', 'resource', 'role')

admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(ResourceBase, ResourceBaseAdmin)
