#########################################################################
#
# Copyright (C) 2021 OSGeo
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

import rest_framework.permissions


class IsAdminOrListOnly(rest_framework.permissions.BasePermission):

    def has_permission(self, request, view):
        if request.user.is_superuser:
            result = True
        elif view.action == "list":
            result = True
        else:
            result = False
        return result


class IsSuperUser(rest_framework.permissions.BasePermission):

    def has_permission(self, request, view):
        return request.user.is_superuser
