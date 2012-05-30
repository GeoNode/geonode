from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('geonode.proxy.views',
    (r'^proxy/', 'proxy'),
    (r'^gs/rest/styles', 'geoserver_rest_proxy', dict(
        proxy_path='/gs/rest/styles', downstream_path='rest/styles')),
    (r'^gs/rest/layers', 'geoserver_rest_proxy', dict(
        proxy_path='/gs/rest/layers', downstream_path='rest/layers')),
    (r'^picasa/','picasa'),
    (r'^youtube/','youtube'),
    (r'^hglpoint/','hglpoints'),
    (r'^hglServiceStarter/(?P<layer>[^/]*)/?','hglServiceStarter'),
    (r'^tweettrends','tweetTrendProxy'),
)
