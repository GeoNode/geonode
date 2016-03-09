from django.conf.urls import patterns

from geonode.api.urls import api

from .api import CollectionResource

api.register(CollectionResource())

urlpatterns = patterns('geonode.contrib.collections.views',)
