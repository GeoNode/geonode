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
from geonode.urls import urlpatterns
from geonode.upload.api.views import ResourceImporter, ImporterViewSet
from django.urls import re_path

urlpatterns.insert(
    0,
    re_path(
        r"uploads/upload",
        ImporterViewSet.as_view({"post": "create"}),
        name="importer_upload",
    ),
)

urlpatterns.insert(
    1,
    re_path(
        r"resources/(?P<pk>\w+)/copy",
        ResourceImporter.as_view({"put": "copy"}),
        name="importer_resource_copy",
    ),
)
