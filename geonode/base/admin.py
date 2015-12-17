from django.contrib import admin
from django.conf import settings

import autocomplete_light
from autocomplete_light.contrib.taggit_field import TaggitField, TaggitWidget

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from modeltranslation.admin import TranslationAdmin

from geonode.base.models import (TopicCategory, SpatialRepresentationType, Region, RestrictionCodeType,
                                 ContactRole, Link, License, HierarchicalKeyword)


class MediaTranslationAdmin(TranslationAdmin):
    class Media:
        js = (
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }


class LicenseAdmin(MediaTranslationAdmin):
    model = License
    list_display = ('id', 'name')
    list_display_links = ('name',)


class TopicCategoryAdmin(MediaTranslationAdmin):
    model = TopicCategory
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')
    if settings.MODIFY_TOPICCATEGORY is False:
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
    list_display = ('id', 'contact', 'resource', 'role')
    list_editable = ('contact', 'resource', 'role')
    form = autocomplete_light.modelform_factory(ContactRole)


class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)
    form = autocomplete_light.modelform_factory(Link)

class HierarchicalKeywordAdmin(TreeAdmin):
    form = movenodeform_factory(HierarchicalKeyword)

admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(HierarchicalKeyword, HierarchicalKeywordAdmin)

class ResourceBaseAdminForm(autocomplete_light.ModelForm):
    keywords = TaggitField(widget=TaggitWidget('HierarchicalKeywordAutocomplete'), required=False)
