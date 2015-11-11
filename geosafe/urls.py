__author__ = 'ismailsunni'
from django.conf.urls import patterns, url

from geosafe.views.analysis import (
    AnalysisListView,
    AnalysisCreateView, impact_function_filter)

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
    url(
        r'^geosafe/analysis/impact-function-filter$',
        impact_function_filter,
        name='impact-function-filter'
    ),
)
