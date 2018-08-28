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
from geonode.documents.models import Document
from geonode.base.admin import MediaTranslationAdmin, ResourceBaseAdminForm
from geonode.base.admin import metadata_batch_edit


class DocumentAdminForm(ResourceBaseAdminForm):

    class Meta:
        model = Document
        fields = '__all__'
        exclude = (
            'resource',
        )


class DocumentAdmin(MediaTranslationAdmin):
    list_display = ('id',
                    'title',
                    'date',
                    'category',
                    'group',
                    'is_approved',
                    'is_published',
                    'metadata_completeness')
    list_display_links = ('id',)
    list_editable = ('title', 'category', 'group', 'is_approved', 'is_published')
    list_filter = ('date', 'date_type', 'restriction_code_type', 'category',
                   'group', 'is_approved', 'is_published',)
    search_fields = ('title', 'abstract', 'purpose',
                     'is_approved', 'is_published',)
    date_hierarchy = 'date'
    form = DocumentAdminForm
    actions = [metadata_batch_edit]


admin.site.register(Document, DocumentAdmin)
