# -*- coding: utf-8 -*-
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

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls import url

from . import api as resources
from . import resourcebase_api as resourcebase_resources

api = Api(api_name='api')

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
api.register(resourcebase_resources.ResourceBaseResource())

router = routers.DynamicRouter()

schema_view = get_schema_view(
    openapi.Info(
        title="GeoNode REST API",
        default_version='v2',
        description="Application for serving and sharing geospatial data",
        terms_of_service="https://github.com/GeoNode/geonode/wiki/Community-Bylaws",
        contact=openapi.Contact(email="dev@geonode.org"),
        license=openapi.License(name="GPL License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
