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
"""
The only place where v3 routes are registered: import the viewset and register it here by hand.
Keep the prefixes alphabetical, so the root stays readable
"""
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

from geonode.api.v3.viewsets import V3RootView
from geonode.sources.api.v3.views import DataItemViewSet, SourceConnectionViewSet, SourceProviderViewSet

app_name = "api_v3"


class V3Router(DefaultRouter):
    APIRootView = V3RootView


router = V3Router(trailing_slash=True)
router.register(r"data-items", DataItemViewSet, "data-items")
router.register(r"source-connections", SourceConnectionViewSet, "source-connections")
router.register(r"source-providers", SourceProviderViewSet, "source-providers")

urlpatterns = [
    # url_name is namespaced because this module sets app_name
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="api_v3:schema"), name="swagger-ui"),
    path("schema/redoc/", SpectacularRedocView.as_view(url_name="api_v3:schema"), name="redoc"),
    path("", include(router.urls)),
]
