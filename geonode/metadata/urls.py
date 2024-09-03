#########################################################################
#
# Copyright (C) 2024 OSGeo
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

from django.urls import path

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from drf_spectacular.renderers import OpenApiJsonRenderer
from geonode.metadata.views import DynamicResourceViewSet, UiSchemaViewset
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r"", DynamicResourceViewSet, basename="tasks")

urlpatterns = [
    path(
        "schema/",
        SpectacularAPIView.as_view(patterns=[router.urls[0]], renderer_classes=[OpenApiJsonRenderer]),
        name="schema",
    ),
    path("schema/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("ui-schema/", UiSchemaViewset.as_view(), name="ui_schema"),
] + router.urls
