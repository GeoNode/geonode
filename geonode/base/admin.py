from django.contrib import admin

from geonode.base.models import (TopicCategory, SpatialRepresentationType,
    Region, RestrictionCodeType, ContactRole, ResourceBase, Link)

class ResourceBaseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'date', 'category')
    list_display_links = ('id',)

class TopicCategoryAdmin(admin.ModelAdmin):
    model = TopicCategory
    list_display_links = ('name',)
    list_display = ('id', 'name', 'slug', 'description')
    
class RegionAdmin(admin.ModelAdmin):
    model = Region
    list_display_links = ('name',)
    list_display = ('code', 'name')
    
class SpatialRepresentationTypeAdmin(admin.ModelAdmin):
    model = SpatialRepresentationType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')
    
    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False
        
    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False
        
class RestrictionCodeTypeAdmin(admin.ModelAdmin):
    model = RestrictionCodeType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')
    
    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False
        
    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False

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
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(ResourceBase, ResourceBaseAdmin)
admin.site.register(Link, LinkAdmin)
