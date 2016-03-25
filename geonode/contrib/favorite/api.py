import json

from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType

from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie import fields
from tastypie.constants import ALL
from tastypie.contrib.contenttypes.fields import GenericForeignKeyField

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.people.models import Profile
from geonode.api.resourcebase_api import LayerResource, MapResource, DocumentResource
from geonode.api.api import ProfileResource
from geonode.base.models import ResourceBase

from .models import Favorite 


class FavoriteResource(ModelResource):
    """Favorites API"""

    content_type = fields.CharField('content_type')
    content_object = GenericForeignKeyField({
        Layer: LayerResource,
        Map: MapResource,
        Document: DocumentResource,
        Profile: ProfileResource
    }, 'content_object', full=True)

    def dehydrate_content_type(self, bundle):
      return str(bundle.obj.content_type)

    def serialize(self, request, data, format, options={}):
        return super(FavoriteResource, self).serialize(request, data, format, options)

    def authorized_read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user.id)

    def build_filters(self, filters={}):
        orm_filters = super(FavoriteResource, self).build_filters(filters)
        if 'keyword' in filters:
            orm_filters.update({'keywords': filters.getlist('keyword')})
        if 'title' in filters:
            orm_filters.update({'title': filters['title']})
        if 'type' in filters:
            orm_filters.update({'type': filters.getlist('type')})

        return orm_filters

    def exclude_profiles(self, semi_filtered):
        profile_ctype = ContentType.objects.get_for_model(Profile)
        return semi_filtered.exclude(content_type=profile_ctype)

    def exclude_resources(self, semi_filtered):
        for rtype in (Map, Layer, Document):
            ctype = ContentType.objects.get_for_model(rtype)
            semi_filtered = semi_filtered.exclude(content_type=ctype)
        return semi_filtered

    def apply_filters(self, request, applicable_filters):
        types = applicable_filters.pop('type', None)
        keywords = applicable_filters.pop('keywords', None)
        title = applicable_filters.pop('title', None)

        semi_filtered = super(
            FavoriteResource,
            self).apply_filters(
            request,
            applicable_filters)

        if types:
            if not 'profile' in types:
                semi_filtered = self.exclude_profiles(semi_filtered)
            if not 'map' in types:
                ctype = ContentType.objects.get_for_model(Map)
                semi_filtered = semi_filtered.exclude(content_type=ctype)
            if not 'layer' in types:
                ctype = ContentType.objects.get_for_model(Layer)
                semi_filtered = semi_filtered.exclude(content_type=ctype)
            if not 'document' in types:
                ctype = ContentType.objects.get_for_model(Document)
                semi_filtered = semi_filtered.exclude(content_type=ctype)

        if title:
            semi_filtered = self.exclude_profiles(semi_filtered)
            filtered_resources = ResourceBase.objects.filter(title__in=title)
            semi_filtered = semi_filtered.filter(object_id__in=filtered_resources)

        if keywords:
            semi_filtered = self.exclude_profiles(semi_filtered)
            filtered_resources = ResourceBase.objects.filter(keywords__slug__in=keywords)
            semi_filtered = semi_filtered.filter(object_id__in=filtered_resources)

        return semi_filtered

    class Meta:
        queryset = Favorite.objects.all()
        resource_name = 'favorites'
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'content_type': 'exact',  
        }
