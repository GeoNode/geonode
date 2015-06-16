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

import autocomplete_light

from geonode.maps.models import Map, MapLayer, MapSnapshot
from geonode.base.admin import MediaTranslationAdmin, ResourceBaseAdminForm
from django.contrib import admin


class MapLayerInline(admin.TabularInline):
    model = MapLayer


class MapAdminForm(ResourceBaseAdminForm):

    class Meta:
        model = Map


class MapAdmin(MediaTranslationAdmin):
    inlines = [MapLayerInline, ]
    list_display_links = ('title',)
    list_display = ('id', 'title', 'owner',)
    list_filter = ('owner', 'category',)
    search_fields = ('title', 'abstract', 'purpose',)
    form = MapAdminForm


class MapLayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'map', 'name')
    list_filter = ('map',)
    search_fields = ('map__title', 'name',)
    form = autocomplete_light.modelform_factory(MapLayer)

admin.site.register(Map, MapAdmin)
admin.site.register(MapLayer, MapLayerAdmin)
admin.site.register(MapSnapshot)
