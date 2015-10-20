__author__ = 'ismailsunni'
from django.conf.urls import patterns, url

from geosafe.views import (
    MetadataListView,
    MetadataCreate,
    MetadataDetailView,
    MetadataUpdateView,
    MetadataDeleteView)

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
    url(
        r'^geosafe/metadata/view/(?P<pk>\d+)$',
        MetadataDetailView.as_view(),
        name='metadata-detail'
    ),
    url(
        r'^geosafe/metadata/update/(?P<pk>\d+)$',
        MetadataUpdateView.as_view(),
        name='metadata-update'
    ),
    url(
        r'^geosafe/metadata/delete/(?P<pk>\d+)$',
        MetadataDeleteView.as_view(),
        name='metadata-delete'
    ),

)
