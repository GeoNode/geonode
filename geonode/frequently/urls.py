"""URLs for the ``django-frequently`` application."""
from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.EntryCategoryListView.as_view(),
        name='frequently_list'),

    url(r'^your-question/$',
        views.EntryCreateView.as_view(),
        name='frequently_submit_question'),

    url(r'^(?P<slug>[a-z-0-9]+)/$',
        views.EntryDetailView.as_view(),
        name='frequently_entry_detail'),
]
