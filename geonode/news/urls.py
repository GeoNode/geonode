from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from geonode.news.views import NewsList, NewsCreate, NewsUpdate, NewsDelete, NewsDetails


urlpatterns = patterns(
    'geonode.news.views',

    # url(r'^create$', 'news_create', name='news-create'),
    # url(r'^list$', 'news_lsit', name='news-list'),
    # url(r'^(?P<news_pk>[0-9]+)/details$', 'news_details', name='news-details'),

    url(r'^list$', NewsList.as_view(), name='news-list'),
    url(r'^create$', NewsCreate.as_view(), name='news-create'),
    url(r'^(?P<news_pk>[0-9]+)/update$', NewsUpdate.as_view(), name='news-update'),
    url(r'^(?P<news_pk>[0-9]+)/delete$', NewsDelete.as_view(), name='news-delete'),
    url(r'^(?P<news_pk>[0-9]+)/details$', NewsDetails.as_view(), name='news-details'),
    url(r'^news_templates/?$', TemplateView.as_view(template_name='news_templates.html'), name='news_templates'),

)