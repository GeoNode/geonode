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
from django.urls import re_path

from . import views

js_info_dict = {
    "packages": ("geonode.base",),
}

urlpatterns = [
    # 'geonode.resourcebases.views',
    re_path(r"^(?P<resourcebaseid>\d+)/metadata$", views.resourcebase_metadata, name="resourcebase_metadata"),
    re_path(
        r"^(?P<resourcebaseid>[^/]*)/metadata_detail$",
        views.resourcebase_metadata_detail,
        name="resourcebase_metadata_detail",
    ),
    re_path(
        r"^(?P<resourcebaseid>\d+)/metadata_advanced$",
        views.resourcebase_metadata_advanced,
        name="resourcebase_metadata_advanced",
    ),
    re_path(
        r"^(?P<resourcebaseid>[^/]+)/embed$",
        views.resourcebase_embed,
        {"template": "base/base_embed.html"},
        name="resourcebase_embed",
    ),
]
