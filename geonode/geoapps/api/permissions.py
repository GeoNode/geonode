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
from django.conf import settings
from rest_framework.filters import BaseFilterBackend

from geonode.geoapps.models import GeoApp


class GeoAppPermissionsFilter(BaseFilterBackend):
    """
    A filter backend that limits results to those where the requesting user
    has read object level permissions.
    """
    shortcut_kwargs = {
        'accept_global_perms': True,
    }

    def filter_queryset(self, request, queryset, view):
        # We want to defer this import until runtime, rather than import-time.
        # See https://github.com/encode/django-rest-framework/issues/4608
        # (Also see #1624 for why we need to make this import explicitly)
        from guardian.shortcuts import get_objects_for_user
        from geonode.security.utils import get_visible_resources

        user = request.user
        resources = get_objects_for_user(
            user,
            'base.view_resourcebase',
            **self.shortcut_kwargs
        )

        _allowed_ids = get_visible_resources(
            resources,
            user,
            admin_approval_required=settings.ADMIN_MODERATE_UPLOADS,
            unpublished_not_visible=settings.RESOURCE_PUBLISHING,
            private_groups_not_visibile=settings.GROUP_PRIVATE_RESOURCES
        ).values_list('id', flat=True)

        obj_with_perms = [_app.id for _app in GeoApp.objects.filter(id__in=_allowed_ids)]

        return queryset.filter(id__in=obj_with_perms)
