from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document
from geonode.base.models import ResourceBase

from tastypie.constants import ALL, ALL_WITH_RELATIONS

from .models import FacetedModelResource
from .authorization import GeoNodeAuthorization


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