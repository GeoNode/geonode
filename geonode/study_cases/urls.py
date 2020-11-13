"""URLs for the ``Study Cases`` module."""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.StudyCasesListView.as_view(),
        name='study_cases_list'),

    url(r'^create/$',
        views.StudyCasesCreateView.as_view(),
        name='study_cases_submit'),
    
]
