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

from django.contrib.sites.models import Site
from django.conf import settings
from django.db.models import Count
from django.contrib.auth import get_user_model

from tastypie.constants import ALL
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from guardian.shortcuts import get_objects_for_user

from geonode.api.resourcebase_api import CommonModelApi, LayerResource, MapResource, DocumentResource, \
                                         ResourceBaseResource
from geonode.base.models import ResourceBase
from geonode.api.urls import api
from geonode.api.api import TagResource, TopicCategoryResource, RegionResource, CountJSONSerializer, \
                            ProfileResource

from .utils import resources_for_site, users_for_site


class CommonSiteModelApi(CommonModelApi):
    """Override the apply_filters method to respect the site"""

    def apply_filters(self, request, applicable_filters):
        filtered = super(CommonSiteModelApi, self).apply_filters(request, applicable_filters)

        filtered = filtered.filter(id__in=resources_for_site())

        return filtered


class SiteResourceBaseResource(CommonSiteModelApi):
    """Site aware ResourceBase api"""

    class Meta(ResourceBaseResource.Meta):
        pass


class SiteLayerResource(CommonSiteModelApi):
    """Site aware Layer API"""

    class Meta(LayerResource.Meta):
        pass


class SiteMapResource(CommonSiteModelApi):

    """Site aware Maps API"""

    class Meta(MapResource.Meta):
        pass


class SiteDocumentResource(CommonSiteModelApi):
    """Site aware Documents API"""

    class Meta(DocumentResource.Meta):
        pass


class SiteResource(ModelResource):
    """Sites API"""

    class Meta:
        queryset = Site.objects.all()
        filtering = {
            'name': ALL
        }
        resource_name = 'sites'
        allowed_methods = ['get', 'delete', 'post']
        authorization = DjangoAuthorization()


class SiteCountJSONSerializer(CountJSONSerializer):
    """Custom serializer to post process the api and add counts for site"""

    def get_resources_counts(self, options):
        if settings.SKIP_PERMS_FILTER:
            resources = ResourceBase.objects.all()
        else:
            resources = get_objects_for_user(
                options['user'],
                'base.view_resourcebase'
            )
        if settings.RESOURCE_PUBLISHING:
            resources = resources.filter(is_published=True)

        if options['title_filter']:
            resources = resources.filter(title__icontains=options['title_filter'])

        if options['type_filter']:
            resources = resources.instance_of(options['type_filter'])

        resources = resources.filter(id__in=resources_for_site())
        counts = list(resources.values(options['count_type']).annotate(count=Count(options['count_type'])))

        return dict([(c[options['count_type']], c['count']) for c in counts])


class SiteTagResource(TagResource):
    """Site aware Tag API"""

    class Meta(TagResource.Meta):
        serializer = SiteCountJSONSerializer()


class SiteTopicCategoryResource(TopicCategoryResource):
    """Site aware Category API"""

    class Meta(TopicCategoryResource.Meta):
        serializer = SiteCountJSONSerializer()


class SiteRegionResource(RegionResource):
    """Site aware Region API"""

    class Meta(RegionResource.Meta):
        serializer = SiteCountJSONSerializer()


class SiteProfileResource(ProfileResource):
    """Site aware Profile API"""

    class Meta(ProfileResource.Meta):
        queryset = get_user_model().objects.exclude(username='AnonymousUser').filter(id__in=users_for_site())


api.register(SiteLayerResource())
api.register(SiteMapResource())
api.register(SiteDocumentResource())
api.register(SiteResourceBaseResource())
api.register(SiteResource())
api.register(SiteTagResource())
api.register(SiteTopicCategoryResource())
api.register(SiteRegionResource())
api.register(SiteProfileResource())
