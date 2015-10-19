__author__ = 'ismailsunni'
from django.conf.urls import patterns, url

from geosafe.views import MetadataListView, MetadataCreate

urlpatterns = patterns(
    '',
    url(
        r'^geosafe/metadata/$',
        MetadataListView.as_view(),
        name='metadata-list'
    ),
    url(
        r'^geosafe/metadata/upload$',
        MetadataCreate.as_view(),
        name='metadata-create'
    ),
    
    # url(r'^geosafe/listing/$', 'geosafe.views.listing'),  # same as index
    # url(r'^geosafe/view/(?P<layer_id>\d+)$', 'geosafe.views.view'),

)
