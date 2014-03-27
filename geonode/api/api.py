from django.contrib.auth.models import User

from geonode.layers.models import Layer
from geonode.maps.models import Map
from geonode.documents.models import Document

from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization
from tastypie.constants import ALL, ALL_WITH_RELATIONS

from .authorization import GeoNodeAuthorization

class CommonMetaApi:
    authorization = DjangoAuthorization()
    allowed_methods = ['get','post','delete','put']

class UserResource(ModelResource):
    """User api"""

    class Meta(CommonMetaApi):
        queryset = User.objects.all()
        resource_name = 'users'
        allowed_methods = ['get']
        excludes = ['is_staff', 'password', 'is_superuser',
             'is_active', 'date_joined', 'last_login']

        filtering = {
            'username': ALL,
        }

class LayerResource(ModelResource):
    """Layer API"""

    class Meta(CommonMetaApi):
        authorization = GeoNodeAuthorization(
            view_perm = 'layers.view_layer',
            create_perm = 'layers.add_layer',
            update_perm = 'layer.change_layer',
            delete_perm = 'layer.delete_layer'
        )
        queryset = Layer.objects.all()
        resource_name = 'layers'


class MapResource(ModelResource):
    """Maps API"""

    class Meta(CommonMetaApi):
        authorization = GeoNodeAuthorization(
            view_perm = 'maps.view_map',
            create_perm = 'maps.add_map',
            update_perm = 'maps.change_map',
            delete_perm = 'maps.delete_map'
        )
        queryset = Map.objects.all()
        resource_name = 'maps'


class DocumentResource(ModelResource):
    """Maps API"""

    class Meta(CommonMetaApi):
        authorization = GeoNodeAuthorization(
            view_perm = 'documents.view_document',
            create_perm = 'documents.add_document',
            update_perm = 'documents.change_document',
            delete_perm = 'documents.delete_document'
        )
        queryset = Document.objects.all()
        resource_name = 'documents'
