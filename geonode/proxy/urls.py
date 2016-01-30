from django.conf.urls.defaults import patterns

urlpatterns = patterns('geonode.proxy.views',
    (r'^proxy/', 'proxy'),
    (r'^gs/rest/styles', 'geoserver_rest_proxy', dict(
        proxy_path='/gs/rest/styles', downstream_path='rest/styles')),
    (r'^gs/rest/layers', 'geoserver_rest_proxy', dict(
        proxy_path='/gs/rest/layers', downstream_path='rest/layers')),
    (r'^gs/rest/sldservice', 'geoserver_rest_proxy', dict(
        proxy_path='/gs/rest/sldservice', downstream_path='rest/sldservice')),
    (r'^picasa/','picasa'),
    (r'^youtube/','youtube'),
    (r'^flickr/','flickr'),
    (r'^hglpoint/','hglpoints'),
    (r'^hglServiceStarter/(?P<layer>[^/]*)/?','hglServiceStarter'),
    (r'^tweettrends','tweetTrendProxy'),
    (r'^tweetserver/(?P<geopsip>[A-Za-z0-9\._\-\:]+)/','tweetServerProxy'),
    (r'^tweetDownload','tweetDownload'),
)
