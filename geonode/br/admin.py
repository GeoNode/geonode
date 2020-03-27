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
from geonode.br.models import RestoredBackup


class RestoredBackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'restoration_date', 'archive_md5', 'creation_date')

    def __init__(self, *args, **kwargs):
        super(RestoredBackupAdmin, self).__init__(*args, **kwargs)
        self.readonly_fields = [field.name for field in self.model._meta.get_fields()]

    def get_actions(self, request):
        actions = super(RestoredBackupAdmin, self).get_actions(request)
        del_action = "delete_selected"
        if del_action in actions:
            del actions[del_action]
        return actions

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        pass

    def delete_model(self, request, obj):
        pass

    def save_related(self, request, form, formsets, change):
        pass


admin.site.register(RestoredBackup, RestoredBackupAdmin)
