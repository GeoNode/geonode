from django.conf.urls import patterns, include, url

from tastypie.api import Api

from .api import LayerResource, MapResource, DocumentResource, UserResource

api = Api(api_name='api')

api.register(LayerResource())
api.register(MapResource())
api.register(DocumentResource())
api.register(UserResource())
