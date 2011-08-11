from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('geonode.proxy.views',
    (r'^proxy/', 'proxy'),
    (r'^gs_rest/styles', 'geoserver_style_proxy'),
)
