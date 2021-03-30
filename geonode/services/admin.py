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

from geonode.base.admin import ResourceBaseAdminForm

from . import models


class HarvestJobAdminInline(admin.StackedInline):
    model = models.HarvestJob
    extra = 0


class HarvestJobAdminForm(ResourceBaseAdminForm):

    class Meta(ResourceBaseAdminForm.Meta):
        model = models.HarvestJob
        fields = '__all__'


class ServiceAdminForm(ResourceBaseAdminForm):

    class Meta(ResourceBaseAdminForm.Meta):
        model = models.Service
        fields = '__all__'


class HarvestJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'resource_id', 'status', 'details')
    list_display_links = ('id', 'service')
    list_filter = ('id', 'service', 'status')
    form = HarvestJobAdminForm


class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'base_url', 'type', 'method')
    list_display_links = ('id', 'name')
    list_filter = ('id', 'name', 'type', 'method')
    form = ServiceAdminForm
    inlines = (
        HarvestJobAdminInline,
    )


admin.site.register(models.Service, ServiceAdmin)
admin.site.register(models.HarvestJob, HarvestJobAdmin)
