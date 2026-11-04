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
from rest_framework.routers import SimpleRouter

from geonode.sources.api import views

# own plain DRF router, not the shared dynamic one: SimpleRouter has no root view to shadow the api/v2/ one
router = SimpleRouter()
router.register(r"source-providers", views.SourceProviderViewSet, "source-providers")
router.register(r"source-connections", views.SourceConnectionViewSet, "source-connections")
router.register(r"data-items", views.DataItemViewSet, "data-items")

urlpatterns = router.urls
