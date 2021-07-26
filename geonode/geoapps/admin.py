#########################################################################
#
# Copyright (C) 2020 OSGeo
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

from modeltranslation.admin import TabbedTranslationAdmin

from geonode.geoapps.models import GeoApp
from geonode.base.admin import ResourceBaseAdminForm


class GeoAppAdminForm(ResourceBaseAdminForm):

    class Meta(ResourceBaseAdminForm.Meta):
        model = GeoApp
        fields = '__all__'


class GeoAppAdmin(TabbedTranslationAdmin):
    list_display_links = ('title',)
    list_display = ('id', 'title', 'type', 'owner', 'category', 'group', 'is_approved', 'is_published',)
    list_editable = ('owner', 'category', 'group', 'is_approved', 'is_published',)
    list_filter = ('title', 'owner', 'category', 'group', 'is_approved', 'is_published',)
    search_fields = ('title', 'abstract', 'purpose', 'is_approved', 'is_published',)
    form = GeoAppAdminForm

    def delete_queryset(self, request, queryset):
        """
        We need to invoke the 'ResourceBase.delete' method even when deleting
        through the admin batch action
        """
        for obj in queryset:
            from geonode.resource.manager import resource_manager
            resource_manager.delete(obj.uuid, instance=obj)


admin.site.register(GeoApp, GeoAppAdmin)
