__author__ = 'ismailsunni'
from django.conf.urls import patterns, url

from geosafe.views import (
    AnalysisListView,
    AnalysisCreateView)

urlpatterns = patterns(
    '',
    url(
        r'^geosafe/analysis/create/$',
        AnalysisCreateView.as_view(),
        name='analysis-create'
    ),
    url(
        r'^geosafe/analysis/$',
        AnalysisListView.as_view(),
        name='analysis-list'
    ),
)
