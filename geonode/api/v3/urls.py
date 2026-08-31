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
"""The one and only place where v3 routes are registered.

v3 registers everything here, explicitly, in one pass, and
is included exactly once from :mod:`geonode.urls`.

Rules for this file:

* import the viewset and register it here -- never from an app's ``urls.py``
  and never from an ``AppConfig.ready()``;
* keep the prefixes alphabetical so the router root stays readable.

"""
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter

app_name = "api_v3"

# Explicit even though it's DRF's own default, so the requirement is visible
# here rather than only inherited.
router = DefaultRouter(trailing_slash=True)

urlpatterns = [
    # url_name is namespaced because this module sets app_name
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="api_v3:schema"), name="swagger-ui"),
    path("schema/redoc/", SpectacularRedocView.as_view(url_name="api_v3:schema"), name="redoc"),
    path("", include(router.urls)),
]
