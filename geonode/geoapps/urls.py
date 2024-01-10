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
from django.urls import include, re_path

from . import views

js_info_dict = {
    "packages": ("geonode.geoapps",),
}

urlpatterns = [
    # 'geonode.geoapps.views',
    re_path(r"^new$", views.new_geoapp, name="new_geoapp"),
    re_path(r"^(?P<geoappid>\d+)/metadata$", views.geoapp_metadata, name="geoapp_metadata"),
    re_path(r"^(?P<geoappid>[^/]*)/metadata_detail$", views.geoapp_metadata_detail, name="geoapp_metadata_detail"),
    re_path(r"^(?P<geoappid>\d+)/metadata_advanced$", views.geoapp_metadata_advanced, name="geoapp_metadata_advanced"),
    re_path(
        r"^(?P<geoappid>[^/]+)/embed$", views.geoapp_edit, {"template": "apps/app_embed.html"}, name="geoapp_embed"
    ),
    re_path(r"^", include("geonode.geoapps.api.urls")),
]
