# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2012 OpenPlans
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

from geonode.base.admin import MediaTranslationAdmin, ResourceBaseAdminForm
from geonode.layers.models import Layer, Attribute, Style
from geonode.layers.models import LayerFile, UploadSession

import autocomplete_light


class LayerAdminForm(ResourceBaseAdminForm):

    class Meta:
        model = Layer


class AttributeInline(admin.TabularInline):
    model = Attribute


class LayerAdmin(MediaTranslationAdmin):
    list_display = (
        'id',
        'typename',
        'service_type',
        'title',
        'Floodplains',
        'SUC',
        'date',
        'category')
    list_display_links = ('id',)
    list_editable = ('title', 'category')
    list_filter = ('owner', 'category',
                   'restriction_code_type__identifier', 'date', 'date_type')

    # def get_queryset(self, request):
    # return super(LayerAdmin,
    # self).get_queryset(request).prefetch_related('floodplain_tag','SUC_tag')
    def Floodplains(self, obj):
        return u", ".join(o.name for o in obj.floodplain_tag.all())

    def SUC(self, obj):
        return u", ".join(o.name for o in obj.SUC_tag.all())
    # def get_queryset(self, request):
    #     return super(LayerAdmin, self).get_queryset(request).prefetch_related('SUC_tag')
    # def SUC(self, obj):
    #     return u", ".join(o.name for o in obj.SUC_tag.all())
    inlines = [AttributeInline]

    search_fields = ('typename', 'title', 'abstract', 'purpose',)
    filter_horizontal = ('contacts',)
    date_hierarchy = 'date'
    readonly_fields = ('uuid', 'typename', 'workspace')

    form = LayerAdminForm


class AttributeAdmin(admin.ModelAdmin):
    model = Attribute
    list_display_links = ('id',)
    list_display = (
        'id',
        'layer',
        'attribute',
        'description',
        'attribute_label',
        'attribute_type',
        'display_order')
    list_filter = ('layer', 'attribute_type')
    search_fields = ('attribute', 'attribute_label',)


class StyleAdmin(admin.ModelAdmin):
    model = Style
    list_display_links = ('sld_title',)
    list_display = ('id', 'name', 'sld_title', 'workspace', 'sld_url')
    list_filter = ('workspace',)
    search_fields = ('name', 'workspace',)


class LayerFileInline(admin.TabularInline):
    model = LayerFile


class UploadSessionAdmin(admin.ModelAdmin):
    model = UploadSession
    list_display = ('date', 'user', 'processed')
    inlines = [LayerFileInline]


admin.site.register(Layer, LayerAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(UploadSession, UploadSessionAdmin)
