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
from tastypie.api import Api
from dynamic_rest import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

from django.urls import path

from . import api as resources
from . import resourcebase_api as resourcebase_resources

api = Api(api_name="api")

api.register(resources.GroupCategoryResource())
api.register(resources.GroupResource())
api.register(resources.GroupProfileResource())
api.register(resources.OwnersResource())
api.register(resources.ProfileResource())
api.register(resources.RegionResource())
api.register(resources.StyleResource())
api.register(resources.TagResource())
api.register(resources.ThesaurusKeywordResource())
api.register(resources.TopicCategoryResource())
api.register(resourcebase_resources.DocumentResource())
api.register(resourcebase_resources.FeaturedResourceBaseResource())
api.register(resourcebase_resources.LayerResource())
api.register(resourcebase_resources.MapResource())
api.register(resourcebase_resources.GeoAppResource())
api.register(resourcebase_resources.ResourceBaseResource())

router = routers.DynamicRouter()

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
