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
from django.urls import include, re_path, path

from geonode.management_commands_http.views import ManagementCommandView
from geonode.management_commands_http.routers import router


urlpatterns = [
    re_path(r"management/commands/$", ManagementCommandView.as_view()),
    re_path(r"management/commands/(?P<cmd_name>\w+)/$", ManagementCommandView.as_view()),
    re_path(r"management/commands/(?P<cmd_name>\w+)/", include(router.urls)),
    path("management/", include(router.urls)),
]
