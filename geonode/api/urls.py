from django.conf.urls import patterns, include, url

from tastypie.api import Api

from .api import  UserResource, TagResource, TopicCategoryResource
from .resourcebase_api import LayerResource, MapResource, DocumentResource, ResourceBaseResource

api = Api(api_name='api')

api.register(LayerResource())
api.register(MapResource())
api.register(DocumentResource())
api.register(UserResource())
api.register(ResourceBaseResource())
api.register(TagResource())
api.register(TopicCategoryResource())
