# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.contrib import admin
from django.conf import settings

from autocomplete_light.forms import ModelForm
from autocomplete_light.forms import modelform_factory
from autocomplete_light.contrib.taggit_field import TaggitField, TaggitWidget

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from modeltranslation.admin import TranslationAdmin

from geonode.base.models import (
    TopicCategory,
    SpatialRepresentationType,
    Region,
    RestrictionCodeType,
    ContactRole,
    Link,
    License,
    HierarchicalKeyword,
    MenuPlaceholder,
    Menu,
    MenuItem,
    CuratedThumbnail,
    Configuration,
)
from django.http import HttpResponseRedirect


def metadata_batch_edit(modeladmin, request, queryset):
    ids = ','.join([str(element.pk) for element in queryset])
    resource = queryset[0].class_name.lower()
    return HttpResponseRedirect(
        '/{}s/metadata/batch/{}/'.format(resource, ids))


metadata_batch_edit.short_description = 'Metadata batch edit'


def set_batch_permissions(modeladmin, request, queryset):
    ids = ','.join([str(element.pk) for element in queryset])
    resource = queryset[0].class_name.lower()
    return HttpResponseRedirect(
        '/{}s/permissions/batch/{}/'.format(resource, ids))


set_batch_permissions.short_description = 'Set permissions'


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
    list_display = (
        'identifier',
        'description',
        'gn_description',
        'fa_class',
        'is_choice')
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
    form = modelform_factory(ContactRole, fields='__all__')


class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)
    form = modelform_factory(Link, fields='__all__')


class HierarchicalKeywordAdmin(TreeAdmin):
    search_fields = ('name', )
    form = movenodeform_factory(HierarchicalKeyword)


class MenuPlaceholderAdmin(admin.ModelAdmin):
    model = MenuPlaceholder
    list_display = ('name', )


class MenuAdmin(admin.ModelAdmin):
    model = Menu
    list_display = ('title', 'placeholder', 'order')


class MenuItemAdmin(admin.ModelAdmin):
    model = MenuItem
    list_display = ('title', 'menu', 'order', 'blank_target', 'url')


class CuratedThumbnailAdmin(admin.ModelAdmin):
    model = CuratedThumbnail
    list_display = ('id', 'resource', 'img', 'img_thumbnail')


class ConfigurationAdmin(admin.ModelAdmin):
    model = Configuration

    def has_delete_permission(self, request, obj=None):
        # Disable delete action of Singleton model, since "delete selected objects" uses QuerysSet.delete()
        # instead of Model.delete()
        return False

    def get_form(self, request, obj=None, **kwargs):
        form = super(ConfigurationAdmin, self).get_form(request, obj, **kwargs)

        # allow only superusers to modify Configuration
        if not request.user.is_superuser:
            for field in form.base_fields:
                form.base_fields.get(field).disabled = True

        return form


admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(HierarchicalKeyword, HierarchicalKeywordAdmin)
admin.site.register(MenuPlaceholder, MenuPlaceholderAdmin)
admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuItem, MenuItemAdmin)
admin.site.register(CuratedThumbnail, CuratedThumbnailAdmin)
admin.site.register(Configuration, ConfigurationAdmin)


class ResourceBaseAdminForm(ModelForm):
    # We need to specify autocomplete='TagAutocomplete' or admin views like
    # /admin/maps/map/2/ raise exceptions during form rendering.
    # But if we specify it up front, TaggitField.__init__ throws an exception
    # which prevents app startup. Therefore, we defer setting the widget until
    # after that's done.
    keywords = TaggitField(required=False)
    keywords.widget = TaggitWidget(
        autocomplete='HierarchicalKeywordAutocomplete')
