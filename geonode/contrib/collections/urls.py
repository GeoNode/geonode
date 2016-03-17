from django.conf.urls import patterns, url

from geonode.api.urls import api

from .api import CollectionResource
from .views import CollectionDetail

api.register(CollectionResource())

urlpatterns = patterns('geonode.contrib.collections.views',
    url(r'^(?P<slug>[-\w]+)/$', CollectionDetail.as_view(), name='collection-detail'),
)
