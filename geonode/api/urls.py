from tastypie.api import Api

from .api import TagResource, TopicCategoryResource, ProfileResource, \
    GroupResource, RegionResource, OwnersResource
from .resourcebase_api import LayerResource, MapResource, DocumentResource, \
    ResourceBaseResource, FeaturedResourceBaseResource, MapStoryResource

api = Api(api_name='api')

api.register(LayerResource())
api.register(MapStoryResource())
api.register(MapResource())
api.register(DocumentResource())
api.register(ProfileResource())
api.register(ResourceBaseResource())
api.register(TagResource())
api.register(RegionResource())
api.register(TopicCategoryResource())
api.register(GroupResource())
api.register(FeaturedResourceBaseResource())
api.register(OwnersResource())

# TODO: This should not live here but in geonode/contrib/favorite/urls.py
# but its not currently working there.
from geonode.contrib.favorite.api import FavoriteResource
api.register(FavoriteResource())

