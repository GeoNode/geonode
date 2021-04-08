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

from geonode.upload.models import Upload, UploadFile

from django.contrib import admin


def import_link(obj):
    return f"<a href='{obj.get_import_url()}'>Geoserver Importer Link</a>"


import_link.short_description = 'Link'
import_link.allow_tags = True


class UploadAdmin(admin.ModelAdmin):
    list_display = ('id', 'import_id', 'name', 'layer', 'user', 'date', 'state', import_link)
    list_display_links = ('id',)
    date_hierarchy = 'date'
    list_filter = ('name', 'layer', 'user', 'date', 'state')
    search_fields = ('name', 'layer', 'user', 'date', 'state')

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            obj.delete()


class UploadFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'upload', 'slug', 'base')
    list_display_links = ('id',)
    list_filter = ('slug', )
    search_fields = ('slug', )


admin.site.register(Upload, UploadAdmin)
admin.site.register(UploadFile, UploadFileAdmin)
