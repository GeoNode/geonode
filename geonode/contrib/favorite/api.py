import json

from django.core.urlresolvers import reverse

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

    class Meta:
        queryset = Favorite.objects.all()
        resource_name = 'favorites'
        allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'content_type': 'exact',  
        }
