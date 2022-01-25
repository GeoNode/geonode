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

from geonode.upload.models import Upload, UploadSizeLimit

from django import forms
from django.conf import settings
from django.contrib import admin
from django.utils.translation import ugettext as _


def import_link(obj):
    return f"<a href='{obj.get_import_url()}'>Geoserver Importer Link</a>"


import_link.short_description = 'Link'
import_link.allow_tags = True


class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'import_id', 'name', 'resource', 'user', 'date', 'state', import_link)
    list_display_links = ('id',)
    date_hierarchy = 'date'
    list_filter = ('name', 'resource', 'user', 'date', 'state')
    search_fields = ('name', 'resource', 'user', 'date', 'state')

    def delete_queryset(self, request, queryset):
        """
        We need to invoke the 'Upload.delete' method even when deleting
        through the admin batch action
        """
        for obj in queryset:
            obj.delete()


class UploadSizeLimitAdminForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super(UploadSizeLimitAdminForm, self).clean()

        default_slug = self.instance.slug if self.instance else None
        default_max_size = self.instance.max_size if self.instance else settings.DEFAULT_MAX_UPLOAD_SIZE
        slug = cleaned_data.get('slug', default_slug)
        max_size = cleaned_data.get('max_size', default_max_size)

        after_upload_slugs_list = ['total_upload_size_sum', 'document_upload_size']

        if slug == 'file_upload_handler':
            after_upload_sizes = UploadSizeLimit.objects.filter(
                slug__in=after_upload_slugs_list
            ).values_list('max_size', flat=True)
            if after_upload_sizes and max_size <= max(after_upload_sizes) * 2:
                raise forms.ValidationError(_(
                    "To avoid errors, max size should be at least 2 times "
                    "greater than the value of others size limits."
                ))

        if slug in after_upload_slugs_list:
            handler_max_size = UploadSizeLimit.objects.filter(
                slug='file_upload_handler'
            ).values_list('max_size', flat=True)
            if handler_max_size and max_size * 2 >= max(handler_max_size):
                raise forms.ValidationError(_(
                    "To avoid errors, max size should be at least 2 times "
                    "smaller than the value of 'file_upload_handler'."
                ))

        return cleaned_data

    class Meta:
        model = UploadSizeLimit
        fields = '__all__'


class UploadSizeLimitAdmin(admin.ModelAdmin):
    list_display = ('slug', 'description', 'max_size', 'max_size_label')
    form = UploadSizeLimitAdminForm

    def has_delete_permission(self, request, obj=None):
        protected_objects = [
            'total_upload_size_sum',
            'document_upload_size',
            'file_upload_handler',
        ]
        if obj and obj.slug in protected_objects:
            return False
        return super(UploadSizeLimitAdmin, self).has_delete_permission(request, obj)


admin.site.register(Upload, UploadAdmin)
admin.site.register(UploadSizeLimit, UploadSizeLimitAdmin)
