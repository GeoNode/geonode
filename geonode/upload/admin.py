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

from geonode.upload.models import (
    Upload,
    UploadParallelismLimit,
    UploadSizeLimit,
)
from django.contrib import admin


def import_link(obj):
    return f"<a href='{obj.get_import_url()}'>Geoserver Importer Link</a>"


import_link.short_description = 'Link'
import_link.allow_tags = True


class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'import_id', 'name', 'resource', 'user', 'date', 'state', import_link)
    list_display_links = ('id',)
    date_hierarchy = 'date'
    list_filter = ('name', 'resource', 'user', 'date', 'state')
    search_fields = ('name', 'resource__title', 'user__username', 'date', 'state')

    def delete_queryset(self, request, queryset):
        """
        We need to invoke the 'Upload.delete' method even when deleting
        through the admin batch action
        """
        for obj in queryset:
            obj.delete()


class UploadSizeLimitAdmin(admin.ModelAdmin):
    list_display = ('slug', 'description', 'max_size', 'max_size_label')

    def has_delete_permission(self, request, obj=None):
        protected_objects = [
            'dataset_upload_size',
            'document_upload_size'
        ]
        if obj and obj.slug in protected_objects:
            return False
        return super(UploadSizeLimitAdmin, self).has_delete_permission(request, obj)


class UploadParallelismLimitAdmin(admin.ModelAdmin):
    list_display = ('slug', 'description', 'max_number',)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.slug == "default_max_parallel_uploads":
            return False
        return super(UploadParallelismLimitAdmin, self).has_delete_permission(request, obj)

    def has_add_permission(self, request):
        return False


admin.site.register(Upload, UploadAdmin)
admin.site.register(UploadSizeLimit, UploadSizeLimitAdmin)
admin.site.register(UploadParallelismLimit, UploadParallelismLimitAdmin)
