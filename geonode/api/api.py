from django.contrib.auth.models import User

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document

from tastypie.resources import ModelResource
from tastypie.authentication import SessionAuthentication
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS

class CommonMetaApi:
    authentication= SessionAuthentication()
    authorization = DjangoAuthorization()
    allowed_methods = ['get','post','delete','put']

class LayerResource(ModelResource):
    """Layer API"""

    class Meta(CommonMetaApi):
        queryset = Layer.objects.all()
        resource_name = 'layers'


class MapResource(ModelResource):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Map.objects.all()
        resource_name = 'maps'


class DocumentResource(ModelResource):
    """Maps API"""

    class Meta(CommonMetaApi):
        queryset = Document.objects.all()
        resource_name = 'documents'