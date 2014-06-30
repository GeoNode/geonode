import itertools
from django.db.models import Q
from django.http import HttpResponse
from django.conf import settings

from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from tastypie.utils import trailing_slash

from guardian.shortcuts import get_objects_for_user

from django.conf.urls import url
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404

from tastypie.utils.mime import determine_format, build_content_type
if settings.HAYSTACK_SEARCH:
    from haystack.query import SearchQuerySet

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
            orm_filters.update({'extent': filters['extent']})
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
        bbox = bbox.split(',') #TODO: Why is this different when done through haystack?
        bbox = map(str, bbox) # 2.6 compat - float to decimal conversion
        intersects = ~(Q(bbox_x0__gt=bbox[2]) | Q(bbox_x1__lt=bbox[0]) | Q(bbox_y0__gt=bbox[3]) | Q(bbox_y1__lt=bbox[1]))
        return queryset.filter(intersects)

    def get_search(self, request, **kwargs):
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)

        # Get the list of objects that matches the filter
        filters = self.build_filters(request.GET)
        filtered_objects = self.apply_filters(request, filters)
        filtered_ids = set(filtered_objects.values_list('id', flat=True))

        #Get the list of objects the user has access to
        perm_ids = set(get_objects_for_user(request.user, 'base.view_resourcebase').values_list('id', flat=True))

        # Combine lists. Include only if in both
        filter_set = filtered_ids.intersection(perm_ids)

        # Do the query using the filterset and the query term. Facet the results
        if len(filter_set) > 0:
            sqs = SearchQuerySet().models(Layer, Map, Document).load_all().auto_query(request.GET.get('q', '')).filter(oid__in=filter_set).facet('type').facet('subtype').facet('owner').facet('keywords').facet('category')
            # Build the Facet dict
            facets = {}
            for facet in sqs.facet_counts()['fields']:
                facets[facet] = {} 
                for item in sqs.facet_counts()['fields'][facet]:
                    facets[facet][item[0]] = item[1]

            # Paginate the results
            paginator = Paginator(sqs, request.GET.get('limit'))

            try:
                page = paginator.page(int(request.GET.get('offset')) / int(request.GET.get('limit'), 0) + 1)
            except InvalidPage:
                raise Http404("Sorry, no results on that page.")

            if page.has_previous():
                previous_page = page.previous_page_number()
            else:
                previous_page = 1
            if page.has_next():
                next_page = page.next_page_number()
            else:
                next_page = 1
            total_count = sqs.count()
            objects = page.object_list
        else:
            next_page = 0
            previous_page = 0
            total_count = 0
            facets = {}
            objects = []
        
        object_list = {
           "meta": {
                "limit": 100,
                "next": next_page, 
                "offset": int(getattr(request.GET, 'offset',0)),
                "previous": previous_page, 
                "total_count": total_count,
                "facets" : facets,
            },
            'objects': map(lambda x: x.get_stored_fields(), objects),
        }
        self.log_throttled_access(request)
        return self.create_response(request, object_list)

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
        
        if isinstance(data, dict) and 'objects' in data and not isinstance(data['objects'], list):
            data['objects'] = list(data['objects'].values(*VALUES))

        desired_format = self.determine_format(request)
        serialized = self.serialize(request, data, desired_format)
        return response_class(content=serialized, content_type=build_content_type(desired_format), **response_kwargs)


class ResourceBaseResource(CommonModelApi):
    """ResourceBase api"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.polymorphic_queryset().distinct().order_by('-date')
        resource_name = 'base'
        excludes = ['csw_anytext', 'metadata_xml']

    def prepend_urls(self):
        if settings.HAYSTACK_SEARCH:
            return [
                url(r"^(?P<resource_name>%s)/search%s$" % (self._meta.resource_name, trailing_slash()), self.wrap_view('get_search'), name="api_get_search"),
            ]
        else:
            return []

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
