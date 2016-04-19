__author__ = 'ismailsunni'
from django.conf.urls import patterns, url

from geosafe.views.analysis import (
    AnalysisListView,
    AnalysisCreateView,
    AnalysisDetailView,
    impact_function_filter,
    layer_tiles, layer_metadata, layer_archive, layer_list, rerun_analysis,
    analysis_json, toggle_analysis_saved, download_report, layer_panel)

urlpatterns = patterns(
    '',
    url(
        r'^geosafe/analysis/create(?:/(?P<pk>\d*))?$',
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
    url(
        r'^geosafe/analysis/(?P<pk>\d+)$',
        AnalysisDetailView.as_view(),
        name='analysis-detail'
    ),
    url(
        r'^geosafe/analysis/layer-tiles$',
        layer_tiles,
        name='layer-tiles'
    ),
    url(
        r'^geosafe/analysis/layer-metadata/(?P<layer_id>\d+)',
        layer_metadata,
        name='layer-metadata'
    ),
    url(
        r'^geosafe/analysis/layer-archive/(?P<layer_id>\d+)',
        layer_archive,
        name='layer-archive'
    ),
    url(
        r'^geosafe/analysis/layer-list/'
        r'(?P<layer_purpose>(hazard|exposure|aggregation|impact))'
        r'(?:/(?P<layer_category>\w*))?'
        r'(?:/(?P<bbox>[,.\d-]*))?',
        layer_list,
        name='layer-list'
    ),
    url(
        r'^geosafe/analysis/layer-panel'
        r'(?:/(?P<bbox>[\[\],.\d-]*))?',
        layer_panel,
        name='layer-panel'
    ),
    url(
        r'^geosafe/analysis/rerun/'
        r'(?P<analysis_id>\d+)',
        rerun_analysis,
        name='rerun-analysis'
    ),
    url(
        r'^geosafe/analysis/check/'
        r'(?P<analysis_id>\d+)',
        analysis_json,
        name='check-analysis'
    ),
    url(
        r'^geosafe/analysis/toggle-saved/'
        r'(?P<analysis_id>\d+)',
        toggle_analysis_saved,
        name='toggle-analysis-saved'
    ),
    url(
        r'^geosafe/analysis/report/'
        r'(?P<analysis_id>\d+)/'
        r'(?P<data_type>(map|table))',
        download_report,
        name='download-report'
    ),
)
