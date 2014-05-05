from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase

from tastypie.constants import ALL, ALL_WITH_RELATIONS

from tastypie.resources import ModelResource
from tastypie import fields
from .authorization import GeoNodeAuthorization

from .api import TagResource, TopicCategoryResource, UserResource


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

class CommonModelApi(ModelResource):
    keywords = fields.ToManyField(TagResource, 'keywords', null=True)
    category = fields.ToOneField(TopicCategoryResource, 'category', null=True)
    owner = fields.ToOneField(UserResource, 'owner')


    def get_facets(self, results):
        facets = {}

        documents = results.instance_of(Document)
        if documents.count() > 0:
            facets['document'] = {
                'count': documents.count(),
                'slug': 'Documents'
            }

        maps = results.instance_of(Map)
        if maps.count() > 0:
            facets['map'] = {
                'count': maps.count(),
                'slug': 'Maps'
            }

        layers = results.instance_of(Layer)
        if layers.count() > 0:
            facets['raster'] = {
                'slug': 'Rasters',
                'count': layers.filter(Layer___storeType='coverageStore').count()
            }
            facets['vector'] = {
                'slug': 'Vectors',
                'count': layers.filter(Layer___storeType='dataStore').count()
            }

        return facets


    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.

        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """

        base_bundle = self.build_bundle(request=request)
        objects = self.obj_get_list(bundle=base_bundle, **self.remove_api_resource_names(kwargs)).distinct()
        sorted_objects = self.apply_sorting(objects, options=request.GET)
        
        paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_uri(), limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()

        # Dehydrate the bundles in preparation for serialization.
        bundles = []

        for obj in to_be_serialized[self._meta.collection_name]:
            bundle = self.build_bundle(obj=obj, request=request)
            bundles.append(self.full_dehydrate(bundle, for_list=True))

        to_be_serialized['meta']['facets'] = self.get_facets(objects)

        to_be_serialized[self._meta.collection_name] = bundles
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        
        return self.create_response(request, to_be_serialized)


class ResourceBaseResource(CommonModelApi):
    """ResourceBase api"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.all()
        resource_name = 'base'


class LayerResource(CommonModelApi):
    """Layer API"""

    class Meta(CommonMetaApi):
        queryset = Layer.objects.all()
        resource_name = 'layers'


class MapResource(CommonModelApi):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.all()
        resource_name = 'maps'


class DocumentResource(CommonModelApi):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Document.objects.all()
        resource_name = 'documents'