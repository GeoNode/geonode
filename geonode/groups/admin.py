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
from modeltranslation.admin import TranslationAdmin
from geonode.base.admin import set_user_and_group_layer_permission

from . import models


@admin.register(models.GroupCategory)
class GroupCategoryAdmin(TranslationAdmin):
    list_display = ('name', 'slug',)
    readonly_fields = ('slug',)


class GroupMemberInline(admin.TabularInline):
    model = models.GroupMember


class GroupProfileAdmin(admin.ModelAdmin):
    inlines = [
        GroupMemberInline
    ]
    exclude = ['group', ]
    actions = [set_user_and_group_layer_permission]


admin.site.register(models.GroupProfile, GroupProfileAdmin)
