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
from django.contrib.admin import helpers
from django.conf import settings
from django.core.management import call_command
from django.template.response import TemplateResponse

import autocomplete_light
import StringIO
from autocomplete_light.contrib.taggit_field import TaggitField, TaggitWidget

from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from modeltranslation.admin import TranslationAdmin

from geonode.base.models import (TopicCategory, SpatialRepresentationType, Region, RestrictionCodeType,
                                 ContactRole, Link, Backup, License, HierarchicalKeyword)


class MediaTranslationAdmin(TranslationAdmin):
    class Media:
        js = (
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }


class BackupAdminForm(autocomplete_light.ModelForm):

    class Meta:
        model = Backup
        fields = '__all__'


def run(self, request, queryset):
    """
    Running a Backup
    """
    if request.POST.get('_selected_action'):
        id = request.POST.get('_selected_action')
        siteObj = self.model.objects.get(pk=id)
        if request.POST.get("post"):
            for siteObj in queryset:
                self.message_user(request, "Executed Backup: " + siteObj.name)
                out = StringIO.StringIO()
                call_command('backup', force_exec=True, backup_dir=siteObj.base_folder, stdout=out)
                value = out.getvalue()
                if value:
                    siteObj.location = value
                    siteObj.save()
                else:
                    self.message_user(request, siteObj.name + " backup failed!")
        else:
            context = {
                "objects_name": "Backups",
                'title': "Confirm run of Backups:",
                'action_exec': "run",
                'cancellable_backups': [siteObj],
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            }
            return TemplateResponse(request, 'admin/backups/confirm_cancel.html', context,
                                    current_app=self.admin_site.name)


def restore(self, request, queryset):
    """
    Running a Restore
    """
    if request.POST.get('_selected_action'):
        id = request.POST.get('_selected_action')
        siteObj = self.model.objects.get(pk=id)
        if request.POST.get("post"):
            for siteObj in queryset:
                self.message_user(request, "Executed Restore: " + siteObj.name)
                out = StringIO.StringIO()
                if siteObj.location:
                    call_command('restore', force_exec=True, backup_file=str(siteObj.location).strip(), stdout=out)
                else:
                    self.message_user(request, siteObj.name + " backup not ready!")
        else:
            context = {
                "objects_name": "Restores",
                'title': "Confirm run of Restores:",
                'action_exec': "restore",
                'cancellable_backups': [siteObj],
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            }
            return TemplateResponse(request, 'admin/backups/confirm_cancel.html', context,
                                    current_app=self.admin_site.name)


run.short_description = "Run the Backup"
restore.short_description = "Run the Restore"


class BackupAdmin(MediaTranslationAdmin):
    list_display = ('id', 'name', 'date', 'location')
    list_display_links = ('name',)
    date_hierarchy = 'date'
    readonly_fields = ('location',)
    form = BackupAdminForm
    actions = [run, restore]


class LicenseAdmin(MediaTranslationAdmin):
    model = License
    list_display = ('id', 'name')
    list_display_links = ('name',)


class TopicCategoryAdmin(MediaTranslationAdmin):
    model = TopicCategory
    list_display_links = ('identifier',)
    list_display = ('identifier', 'description', 'gn_description', 'fa_class', 'is_choice')
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
    form = autocomplete_light.modelform_factory(ContactRole, fields='__all__')


class LinkAdmin(admin.ModelAdmin):
    model = Link
    list_display_links = ('id',)
    list_display = ('id', 'resource', 'extension', 'link_type', 'name', 'mime')
    list_filter = ('resource', 'extension', 'link_type', 'mime')
    search_fields = ('name', 'resource__title',)
    form = autocomplete_light.modelform_factory(Link, fields='__all__')


class HierarchicalKeywordAdmin(TreeAdmin):
    form = movenodeform_factory(HierarchicalKeyword)


admin.site.register(TopicCategory, TopicCategoryAdmin)
admin.site.register(Region, RegionAdmin)
admin.site.register(SpatialRepresentationType, SpatialRepresentationTypeAdmin)
admin.site.register(RestrictionCodeType, RestrictionCodeTypeAdmin)
admin.site.register(ContactRole, ContactRoleAdmin)
admin.site.register(Link, LinkAdmin)
admin.site.register(Backup, BackupAdmin)
admin.site.register(License, LicenseAdmin)
admin.site.register(HierarchicalKeyword, HierarchicalKeywordAdmin)


class ResourceBaseAdminForm(autocomplete_light.ModelForm):
    # We need to specify autocomplete='TagAutocomplete' or admin views like
    # /admin/maps/map/2/ raise exceptions during form rendering.
    # But if we specify it up front, TaggitField.__init__ throws an exception
    # which prevents app startup. Therefore, we defer setting the widget until
    # after that's done.
    keywords = TaggitField(required=False)
    keywords.widget = TaggitWidget(autocomplete='HierarchicalKeywordAutocomplete')
