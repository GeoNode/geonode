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
from django.urls import path
from . import views

urlpatterns = [
    re_path(r"^csw$", views.csw_global_dispatch, name="csw_global_dispatch"),
    re_path(r"^opensearch$", views.opensearch_dispatch, name="opensearch_dispatch"),
    re_path(
        r"^csw_to_extra_format/(?P<layeruuid>[^/]*)/(?P<resname>[^/]*).txt$",
        views.csw_render_extra_format_txt,
        name="csw_render_extra_format_txt",
    ),
    re_path(
        r"^csw_to_extra_format/(?P<layeruuid>[^/]*)/(?P<resname>[^/]*).html$",
        views.csw_render_extra_format_html,
        name="csw_render_extra_format_html",
    ),
    path(r"uuid/<uuid>", views.resolve_uuid, name="resolve_uuid"),
]
