from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase

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
    ordering = ['date', 'title', 'popular_count']
    max_limit = None


class CommonModelApi(ModelResource):
    keywords = fields.ToManyField(TagResource, 'keywords', null=True)
    category = fields.ToOneField(TopicCategoryResource, 'category', null=True, full=True)
    owner = fields.ToOneField(UserResource, 'owner', full=True)
    absolute__url = fields.CharField()
    rating = fields.FloatField(attribute='rating', null = True)
    thumbnail_url = fields.CharField(null=True)

    def dehydrate_thumbnail_url(self, bundle):
        return bundle.obj.get_thumbnail_url()    

    def dehydrate_absolute__url(self, bundle):
        return bundle.obj.get_absolute_url()

    def build_filters(self, filters={}):
        orm_filters = super(CommonModelApi, self).build_filters(filters)
        if 'type__in' in filters and filters['type__in'] in FILTER_TYPES.keys():
            orm_filters.update({'type': filters.getlist('type__in')})
        if 'extent' in filters:
            orm_filters.update({'extent': filters['extent'].split(',')})
        return orm_filters

    def apply_filters(self, request, applicable_filters):
        types = applicable_filters.pop('type', None)
        extent = applicable_filters.pop('extent', None)
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

        if extent:
            filtered = self.filter_bbox(filtered, extent)

        return filtered

    def filter_bbox(self, queryset, bbox):
        '''modify the queryset q to limit to the provided bbox

        bbox - 4 tuple of floats representing 'southwest_lng,southwest_lat,northeast_lng,northeast_lat'
        returns the modified query
        '''
        bbox = map(str, bbox) # 2.6 compat - float to decimal conversion
        queryset = queryset.filter(bbox_x0__gte=bbox[0])
        queryset = queryset.filter(bbox_y0__gte=bbox[1])
        queryset = queryset.filter(bbox_x1__lte=bbox[2])
        return queryset.filter(bbox_y1__lte=bbox[3])


class ResourceBaseResource(CommonModelApi):
    """ResourceBase api"""


    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.polymorphic_queryset().distinct().order_by('-date')
        resource_name = 'base'


class FeaturedResourceBaseResource(CommonModelApi):
    """Only the featured resourcebases"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.filter(featured=True).order_by('-date')
        resource_name = 'featured'


class LayerResource(CommonModelApi):
    """Layer API"""


    class Meta(CommonMetaApi):
        queryset = Layer.objects.distinct().order_by('-date')
        resource_name = 'layers'
        excludes = ['csw_anytext', 'metadata_xml']

class MapResource(CommonModelApi):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.distinct().order_by('-date')
        resource_name = 'maps'


class DocumentResource(CommonModelApi):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Document.objects.distinct().order_by('-date')
        resource_name = 'documents'
