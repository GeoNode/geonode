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

from modeltranslation.admin import TabbedTranslationAdmin

from geonode.maps.models import Map, MapLayer
from geonode.base.admin import ResourceBaseAdminForm
from geonode.base.admin import metadata_batch_edit


class MapLayerInline(admin.TabularInline):
    model = MapLayer


class MapAdminForm(ResourceBaseAdminForm):

    class Meta(ResourceBaseAdminForm.Meta):
        model = Map
        fields = '__all__'


class MapAdmin(TabbedTranslationAdmin):
    inlines = [MapLayerInline, ]
    list_display_links = ('title',)
    list_display = ('id', 'title', 'owner', 'category', 'group', 'is_approved', 'is_published', 'featured',)
    list_editable = ('owner', 'category', 'group', 'is_approved', 'is_published', 'featured',)
    list_filter = ('owner', 'category', 'group', 'featured',
                   'is_approved', 'is_published',)
    search_fields = ('title', 'abstract', 'purpose',
                     'is_approved', 'is_published',)
    form = MapAdminForm
    actions = [metadata_batch_edit]

    def delete_queryset(self, request, queryset):
        """
        We need to invoke the 'ResourceBase.delete' method even when deleting
        through the admin batch action
        """
        for obj in queryset:
            from geonode.resource.manager import resource_manager
            resource_manager.delete(obj.uuid, instance=obj)


class MapLayerAdmin(admin.ModelAdmin):
    list_display = ('id', 'map', 'name')
    list_filter = ('map',)
    search_fields = ('map__title', 'name',)
    form = forms.modelform_factory(MapLayer, fields='__all__')


admin.site.register(Map, MapAdmin)
admin.site.register(MapLayer, MapLayerAdmin)
