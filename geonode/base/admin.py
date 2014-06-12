from django.contrib import admin
from django.conf import settings

import autocomplete_light
from modeltranslation.admin import TranslationAdmin

from geonode.base.models import (TopicCategory, SpatialRepresentationType,
    Region, RestrictionCodeType, ContactRole, ResourceBase, Link, License, Thumbnail)

class MediaTranslationAdmin(TranslationAdmin):
    class Media: 
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }

class LicenseAdmin(MediaTranslationAdmin):
    model = License
    list_display = ('id', 'name')
    list_display_links = ('name',)

class ResourceBaseAdmin(admin.ModelAdmin):
    list_display = ('id','title', 'date', 'category')
    list_display_links = ('id',)

    form = autocomplete_light.modelform_factory(ResourceBase)

class TopicCategoryAdmin(MediaTranslationAdmin):
    model = TopicCategory
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')
    if settings.MODIFY_TOPICCATEGORY==False:
        exclude = ('identifier', 'description',)
    
    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False
        
    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        if settings.MODIFY_TOPICCATEGORY:
            return True
        else:
            return False
    
class RegionAdmin(MediaTranslationAdmin):
    model = Region
    list_display_links = ('name',)
    list_display = ('code', 'name', 'parent')
    search_fields = ('code', 'name',)
    group_fieldsets = True

class SpatialRepresentationTypeAdmin(MediaTranslationAdmin):
    model = SpatialRepresentationType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')
    
    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False
        
    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False
        
class RestrictionCodeTypeAdmin(MediaTranslationAdmin):
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
    form = autocomplete_light.modelform_factory(ContactRole)

class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)
    form = autocomplete_light.modelform_factory(Link)
    
class ThumbnailAdmin(admin.ModelAdmin):
    model = Thumbnail
    list_display = ('get_title', 'get_geonode_type', 'thumb_file', 'get_thumb_url',)
    search_fields = ('resourcebase__title',)
    form = autocomplete_light.modelform_factory(Thumbnail)
    
    def get_title(self, obj):
        rb = obj.resourcebase_set.all()[0] # should be always just one!
        return rb.title
    get_title.short_description = 'Title' 
    
    def get_thumb_url(self, obj):
        rb = obj.resourcebase_set.all()[0] # should be always just one!
        return u'<img src="%s" alt="%s" height="80px" />' % (rb.get_thumbnail_url(), 
            obj.id)
    get_thumb_url.allow_tags = True
    get_thumb_url.short_description = 'URL' 
    
    def get_geonode_type(self, obj):
        rb = obj.resourcebase_set.all()[0] # should be always just one!
        return rb.class_name
    get_geonode_type.short_description = 'Type'

admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(ResourceBase, ResourceBaseAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Thumbnail, ThumbnailAdmin)
admin.site.register(License, LicenseAdmin)
