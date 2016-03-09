import json

from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie import fields

from .models import Favorite 

class FavoriteResource(ModelResource):
    """Favorites API"""
    type = fields.CharField()
    detail_url = fields.CharField()
    thumbnail_url = fields.CharField()

    def dehydrate_type(self, bundle):
      return bundle.obj.content_type

    def dehydrate_detail_url(self, bundle):
        if str(bundle.obj.content_type) == "layer":
            return reverse('layer_detail', args=[Layer.objects.get(id=bundle.obj.id)])

    def dehydrate_thumbnail_url(self, bundle):
        if str(bundle.obj.content_type) == "layer":
            return Layer.objects.get(id=bundle.obj.id).thumbnail_url

    def serialize(self, request, data, format, options={}):
        options['something'] = 'anything'
        return super(FavoriteResource, self).serialize(request, data, format, options)

    def authorized_read_list(self, object_list, bundle):
        return object_list.filter(user=bundle.request.user.id)

    class Meta:
        queryset = Favorite.objects.all()
        resource_name = 'favorites'
        allowed_methods = ['get']
        authorization = Authorization()
