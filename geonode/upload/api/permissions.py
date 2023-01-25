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
from geonode.upload.models import Upload
from rest_framework.filters import BaseFilterBackend


class UploadPermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """

    shortcut_kwargs = {
        "accept_global_perms": True,
    }

    def filter_queryset(self, request, queryset, view):
        user = request.user

        if not user or user.is_anonymous or not user.is_authenticated:
            return Upload.objects.none()
        elif user.is_superuser:
            return queryset
        return queryset.filter(user=user)
