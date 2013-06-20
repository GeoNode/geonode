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
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from geonode.layers.models import Layer, Attribute, Style
from geonode.base.models import ContactRole

class ContactRoleInline(admin.TabularInline):
    model = ContactRole

class AttributeInline(admin.TabularInline):
    model = Attribute

class LayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'typename','service_type','title', 'date', 'category')
    list_display_links = ('id',)
    list_editable = ('title', 'category')
    list_filter  = ('date', 'date_type', 'constraints_use', 'category')
    search_fields = ('typename', 'title', 'abstract', 'purpose',)
    filter_horizontal = ('contacts',)
    date_hierarchy = 'date'
    readonly_fields = ('uuid', 'typename', 'workspace')
    inlines = [ContactRoleInline, AttributeInline]

    actions = ['change_poc']

    def change_poc(self, request, queryset):
        selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
        return HttpResponseRedirect(reverse('change_poc', kwargs={"ids": "_".join(selected)}))
    change_poc.short_description = "Change the point of contact for the selected layers"

class AttributeAdmin(admin.ModelAdmin):
    model = Attribute
    list_display_links = ('id',)
    list_display = ('id', 'layer', 'attribute', 'attribute_label', 'attribute_type', 'display_order')
    list_filter = ('layer', 'attribute_type')
    search_fields = ('attribute', 'attribute_label',)

class StyleAdmin(admin.ModelAdmin):
    model = Style
    list_display_links = ('sld_title',)
    list_display = ('id', 'name', 'sld_title', 'workspace', 'sld_url')
    list_filter = ('workspace',)
    search_fields = ('name', 'workspace',)

admin.site.register(Layer, LayerAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Style, StyleAdmin)
