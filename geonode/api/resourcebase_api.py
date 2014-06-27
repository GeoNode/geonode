from django.db.models import Q
from django.http import HttpResponse

from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.utils.mime import determine_format, build_content_type

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase

from .authorization import GeoNodeAuthorization

from .api import TagResource, TopicCategoryResource, UserResource, FILTER_TYPES

LAYER_SUBTYPES = {
    'vector': 'dataStore',
    'raster': 'coverageStore',
    'remote': 'remoteStore',
}
FILTER_TYPES.update(LAYER_SUBTYPES)

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
    rating = fields.FloatField(attribute='rating', null = True)

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
                if the_type in LAYER_SUBTYPES.keys():
                    if filtered:
                        filtered = filtered | semi_filtered.filter(Layer___storeType=LAYER_SUBTYPES[the_type])
                    else:
                        filtered = semi_filtered.filter(Layer___storeType=LAYER_SUBTYPES[the_type])
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
        '''modify the queryset q to limit to data that intersects with the provided bbox 

        bbox - 4 tuple of floats representing 'southwest_lng,southwest_lat,northeast_lng,northeast_lat'
        returns the modified query
        '''
        bbox = map(str, bbox) # 2.6 compat - float to decimal conversion
        intersects = ~(Q(bbox_x0__gt=bbox[2]) | Q(bbox_x1__lt=bbox[0]) | Q(bbox_y0__gt=bbox[3]) | Q(bbox_y1__lt=bbox[1]))
        return queryset.filter(intersects)

    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.

        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """
        # TODO: Uncached for now. Invalidation that works for everyone may be
        #       impossible.
        base_bundle = self.build_bundle(request=request)
        objects = self.obj_get_list(bundle=base_bundle, **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_uri(), limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()

        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        return self.create_response(request, to_be_serialized)

    def create_response(self, request, data, response_class=HttpResponse, **response_kwargs):
        """
        Extracts the common "which-format/serialize/return-response" cycle.

        Mostly a useful shortcut/hook.
        """
        VALUES = [
            # fields in the db
            'id',
            'uuid',
            'title',
            'abstract',
            'csw_wkt_geometry',
            'csw_type',
            'distribution_description',
            'distribution_url',
            'owner_id',
            'share_count',
            'srid',
            'category',
            'supplemental_information',
            'thumbnail_url',
            'absolute_url',
        ]
        
        if isinstance(data, dict) and 'objects' in data:
            data['objects'] = list(data['objects'].values(*VALUES))

        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return response_class(content=serialized, content_type=build_content_type(desired_format), **response_kwargs)


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
