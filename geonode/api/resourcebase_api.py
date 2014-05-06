from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase

from tastypie.constants import ALL, ALL_WITH_RELATIONS

from tastypie.resources import ModelResource
from tastypie import fields
from .authorization import GeoNodeAuthorization

from .api import TagResource, TopicCategoryResource, UserResource, FILTER_TYPES

FILTER_TYPES.update({
    'vector': 'dataStore',
    'raster': 'coverageStore'
})

class CommonMetaApi:
    authorization = GeoNodeAuthorization()
    allowed_methods = ['get',]
    filtering = {
            'title': ALL,
            'keywords': ALL_WITH_RELATIONS,
            'category': ALL_WITH_RELATIONS,
            'owner': ALL_WITH_RELATIONS,
            'date': ALL,
        }
    ordering = ['date',]


class CommonModelApi(ModelResource):
    keywords = fields.ToManyField(TagResource, 'keywords', null=True)
    category = fields.ToOneField(TopicCategoryResource, 'category', null=True)
    owner = fields.ToOneField(UserResource, 'owner')

    def build_filters(self, filters={}):
        orm_filters = super(CommonModelApi, self).build_filters(filters)
        if 'type__in' in filters and filters['type__in'] in FILTER_TYPES.keys():
            orm_filters.update({'type': filters.getlist('type__in')})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        types = applicable_filters.pop('type', None)
        semi_filtered = super(CommonModelApi, self).apply_filters(request, applicable_filters)
        filtered = None
        if types:
            for the_type in types:
                if the_type == 'vector' or the_type == 'raster':
                    if filtered:
                        filtered = filtered | semi_filtered.filter(Layer___storeType=FILTER_TYPES[the_type])
                    else:
                        filtered = semi_filtered.filter(Layer___storeType=FILTER_TYPES[the_type])
                else:
                    if filtered:
                        filtered = filtered | semi_filtered.instance_of(FILTER_TYPES[the_type])
                    else:
                        filtered = semi_filtered.instance_of(FILTER_TYPES[the_type])
        else:
            filtered = semi_filtered
        return filtered


class ResourceBaseResource(CommonModelApi):
    """ResourceBase api"""

    count = fields.IntegerField()


    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.all().order_by('-date')
        resource_name = 'base'


class LayerResource(CommonModelApi):
    """Layer API"""


    class Meta(CommonMetaApi):
        queryset = Layer.objects.all().order_by('-date')
        resource_name = 'layers'


class MapResource(CommonModelApi):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.all().order_by('-date')
        resource_name = 'maps'


class DocumentResource(CommonModelApi):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Document.objects.all().order_by('-date')
        resource_name = 'documents'