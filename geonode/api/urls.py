from tastypie.api import Api
from django.conf.urls import patterns, url

from .api import TagResource, TopicCategoryResource, ProfileResource, \
    GroupResource, RegionResource, DataRequestProfileResource
from .resourcebase_api import LayerResource, MapResource, DocumentResource, \
    ResourceBaseResource, FeaturedResourceBaseResource

api = Api(api_name='api')

urlpatterns = patterns(
    'geonode.api.views',
    url(r'^combined-(?P<apiname>[^/]*)$', 'api_combined', name="api_combined"),
    url(r'^combined-(?P<apiname>[^/]*)/?', 'api_combined', name="api_combined"),
    url(r'^combinedResourceBaseAutocomplete', 'api_autocomplete', name="api_autocomplete"),
)

api.register(LayerResource())
api.register(MapResource())
api.register(DocumentResource())
api.register(ProfileResource())
api.register(ResourceBaseResource())
api.register(TagResource())
api.register(RegionResource())
api.register(TopicCategoryResource())
api.register(GroupResource())
api.register(FeaturedResourceBaseResource())
api.register(DataRequestProfileResource())
