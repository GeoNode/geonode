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

from geonode.maps.models import Map, MapLayer
from modeltranslation.admin import TranslationAdmin
from django.contrib import admin

class MapLayerInline(admin.TabularInline):
    model = MapLayer

class MapAdmin(TranslationAdmin):
    inlines = [MapLayerInline,]
    list_display_links = ('title',)
    list_display = ('id','title', 'owner')
    list_filter = ('owner', 'category',)
    search_fields = ('title', 'abstract', 'purpose', 'owner__profile__name',)

    class Media:
        js = (
            'http://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js',
            'http://ajax.googleapis.com/ajax/libs/jqueryui/1.10.2/jquery-ui.min.js',
            'modeltranslation/js/tabbed_translation_fields.js',
        )
        css = {
            'screen': ('modeltranslation/css/tabbed_translation_fields.css',),
        }
    
class MapLayerAdmin(admin.ModelAdmin):
    list_display = ('id','map', 'name')
    list_filter = ('map',)
    search_fields = ('map__title', 'name',)

admin.site.register(Map, MapAdmin)
admin.site.register(MapLayer, MapLayerAdmin)
