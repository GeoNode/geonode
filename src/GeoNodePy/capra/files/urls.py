from django.conf.urls.defaults import patterns

urlpatterns = patterns('capra.files.views',
    (r'^$', 'index'),
    (r'^index.json$', 'index_json'),
    (r'^upload$', 'upload'),
    (r'^(?P<id>\d+)$', 'dispatch'),
    (r'^(?P<id>\d+)/edit$', 'edit'),
)
