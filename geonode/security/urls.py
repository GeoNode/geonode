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

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^permissions/(?P<resource_id>\d+)$", views.resource_permissions, name="resource_permissions"),
    re_path(r"^geolimits/(?P<resource_id>\d+)$", views.resource_geolimits, name="resource_geolimits"),
    re_path(r"^bulk-permissions/?$", views.set_bulk_permissions, name="bulk_permissions"),
    re_path(r"^request-permissions/?$", views.request_permissions, name="request_permissions"),
    re_path(
        r"^invalidate-permissions-cache/?$", views.invalidate_permissions_cache, name="invalidate_permissions_cache"
    ),
    re_path(
        r"^invalidate_tileddataset_cache/?$", views.invalidate_tileddataset_cache, name="invalidate_tileddataset_cache"
    ),
    re_path(r"^attributes_sats_refresh/?$", views.attributes_sats_refresh, name="attributes_sats_refresh"),
]
