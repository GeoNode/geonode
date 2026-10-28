#########################################################################
#
# Copyright (C) 2026 OSGeo
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
from geonode.api.urls import router
from geonode.sources.api import views

router.register(r"source-providers", views.SourceProviderViewSet, "source-providers")
router.register(r"source-connections", views.SourceConnectionViewSet, "source-connections")
router.register(r"data-items", views.DataItemViewSet, "data-items")

urlpatterns = []
