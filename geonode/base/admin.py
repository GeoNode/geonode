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

from django import forms
from django.contrib import admin
from django.conf import settings
from django.shortcuts import render

from dal import autocomplete
from taggit.forms import TagField

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from modeltranslation.admin import TabbedTranslationAdmin

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

from geonode.base.forms import (
    BatchEditForm,
    BatchPermissionsForm,
    UserAndGroupPermissionsForm
)
from geonode.base.widgets import TaggitSelect2Custom


def metadata_batch_edit(modeladmin, request, queryset):
    ids = ','.join(str(element.pk) for element in queryset)
    resource = queryset[0].class_name.lower()
    form = BatchEditForm({
        'ids': ids
    })
    name_space_mapper = {
        'layer': 'layer_batch_metadata',
        'map': 'map_batch_metadata',
        'document': 'document_batch_metadata'
    }

    try:
        name_space = name_space_mapper[resource]
    except KeyError:
        name_space = None

    return render(
        request,
        "base/batch_edit.html",
        context={
            'form': form,
            'ids': ids,
            'model': resource,
            'name_space': name_space
        }
    )


metadata_batch_edit.short_description = 'Metadata batch edit'


def set_batch_permissions(modeladmin, request, queryset):
    ids = ','.join([str(element.pk) for element in queryset])
    resource = queryset[0].class_name.lower()
    form = BatchPermissionsForm(
        {
            'permission_type': ('r', ),
            'mode': 'set',
            'ids': ids
        })

    return render(
        request,
        "base/batch_permissions.html",
        context={
            'form': form,
            'model': resource,
        }
    )


set_batch_permissions.short_description = 'Set permissions'


def set_user_and_group_layer_permission(modeladmin, request, queryset):
    ids = ','.join(str(element.pk) for element in queryset)
    resource = queryset[0].__class__.__name__.lower()

    model_mapper = {
        "profile": "people",
        "groupprofile": "groups"
    }

    form = UserAndGroupPermissionsForm({
        'permission_type': ('r', ),
        'mode': 'set',
        'ids': ids,
    })

    return render(
        request,
        "base/user_and_group_permissions.html",
        context={
            "form": form,
            "model": model_mapper[resource]
        }
    )


set_user_and_group_layer_permission.short_description = 'Set layer permissions'


class LicenseAdmin(TabbedTranslationAdmin):
    model = License
    list_display = ('id', 'name')
    list_display_links = ('name',)


class TopicCategoryAdmin(TabbedTranslationAdmin):
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


class RegionAdmin(TabbedTranslationAdmin):
    model = Region
    list_display_links = ('name',)
    list_display = ('code', 'name', 'parent')
    search_fields = ('code', 'name',)
    group_fieldsets = True


class SpatialRepresentationTypeAdmin(TabbedTranslationAdmin):
    model = SpatialRepresentationType
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'is_choice')

    def has_add_permission(self, request):
        # the records are from the standard TC 211 list, so no way to add
        return False

    def has_delete_permission(self, request, obj=None):
        # the records are from the standard TC 211 list, so no way to remove
        return False


class RestrictionCodeTypeAdmin(TabbedTranslationAdmin):
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
    form = forms.modelform_factory(ContactRole, fields='__all__')


class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)
    form = forms.modelform_factory(Link, fields='__all__')


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
        form = super().get_form(request, obj, **kwargs)

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


class ResourceBaseAdminForm(autocomplete.FutureModelForm):

    keywords = TagField(widget=TaggitSelect2Custom('autocomplete_hierachical_keyword'))

    class Meta:
        pass
