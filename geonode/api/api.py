from django.contrib.auth.models import User

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase, TopicCategory

from taggit.models import Tag

from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie import fields

from .authorization import GeoNodeAuthorization


class TagResource(ModelResource):
    """Tags api"""

    class Meta:
        queryset = Tag.objects.all()
        resource_name = 'keywords'
        allowed_methods = ['get',]
        filtering = {
            'slug': ALL,
        }


class TopicCategoryResource(ModelResource):
    """Category api"""

    class Meta:
        queryset = TopicCategory.objects.all()
        resource_name = 'categories'
        allowed_methods = ['get',]
        filtering = {
            'identifier': ALL,
        }


class UserResource(ModelResource):
    """User api"""

    class Meta:
        authorization = DjangoAuthorization()
        queryset = User.objects.all()
        resource_name = 'users'
        allowed_methods = ['get',]
        excludes = ['is_staff', 'password', 'is_superuser',
             'is_active', 'date_joined', 'last_login']

        filtering = {
            'username': ALL,
        }


class FacetedModelResource(ModelResource):

    keywords = fields.ToManyField(TagResource, 'keywords', full=True, null=True)
    category = fields.ToOneField(TopicCategoryResource, 'category', full=True, null=True)
    owner = fields.ToOneField(UserResource, 'owner', full=True)


    def get_facets(self, results):
        facets = {
            'map': 0,
            'document': 0,
            'layer': 0,
            'raster': 0,
            'vector': 0 
        }
        facets['document'] = results.instance_of(Document).count()
        facets['map'] = results.instance_of(Map).count()
        layers = results.instance_of(Layer)
        if layers.count() > 0:
            facets['raster'] = layers.filter(Layer___storeType='coverageStore').count()
            facets['vector'] = layers.filter(Layer___storeType='dataStore').count()
            facets['layer'] = facets['raster'] + facets['vector']
        return facets

    def get_counts(self, results):
        tags = {}
        categories = {}

        # Tags and categories counts
        for item in results:
            for tagged_item in item.tagged_items.all():
                tags[tagged_item.tag.slug] = tags.get(tagged_item.tag.slug,{})
                tags[tagged_item.tag.slug]['slug'] = tagged_item.tag.slug
                tags[tagged_item.tag.slug]['name'] = tagged_item.tag.name
                tags[tagged_item.tag.slug]['count'] = tags[tagged_item.tag.slug].get('count',0) + 1

            if item.category:
                categories[item.category.identifier] = categories.get(item.category.identifier, {})
                categories[item.category.identifier]['identifier'] = item.category.identifier
                categories[item.category.identifier]['gn_description'] = item.category.gn_description
                categories[item.category.identifier]['count'] = categories[item.category.identifier].get(
                    'count', 0) + 1

        return tags, categories

    def get_list(self, request, **kwargs):
        """
        Returns a serialized list of resources.

        Calls ``obj_get_list`` to provide the data, then handles that result
        set and serializes it.

        Should return a HttpResponse (200 OK).
        """

        base_bundle = self.build_bundle(request=request)
        objects = self.obj_get_list(bundle=base_bundle, **self.remove_api_resource_names(kwargs))
        sorted_objects = self.apply_sorting(objects, options=request.GET)

        paginator = self._meta.paginator_class(request.GET, sorted_objects, resource_uri=self.get_resource_uri(), limit=self._meta.limit, max_limit=self._meta.max_limit, collection_name=self._meta.collection_name)
        to_be_serialized = paginator.page()

        # Dehydrate the bundles in preparation for serialization.
        bundles = []

        for obj in to_be_serialized[self._meta.collection_name]:
            bundle = self.build_bundle(obj=obj, request=request)
            bundles.append(self.full_dehydrate(bundle, for_list=True))

        to_be_serialized['meta']['facets'] = self.get_facets(objects)
        to_be_serialized['meta']['tags'], to_be_serialized['meta']['categories'] = self.get_counts(objects)

        to_be_serialized[self._meta.collection_name] = bundles
        to_be_serialized = self.alter_list_data_to_serialize(request, to_be_serialized)
        
        return self.create_response(request, to_be_serialized)


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


class ResourceBaseResource(FacetedModelResource):
    """ResourceBase api"""

    class Meta(CommonMetaApi):
        queryset = ResourceBase.objects.all()
        resource_name = 'base'


class LayerResource(FacetedModelResource):
    """Layer API"""

    class Meta(CommonMetaApi):
        queryset = Layer.objects.all()
        resource_name = 'layers'


class MapResource(FacetedModelResource):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.all()
        resource_name = 'maps'


class DocumentResource(FacetedModelResource):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Document.objects.all()
        resource_name = 'documents'
