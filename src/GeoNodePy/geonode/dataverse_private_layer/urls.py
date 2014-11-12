from django.conf.urls import patterns, include, url


urlpatterns = patterns('geonode.dataverse_private_layer.views',

    url(r'^view-private-layer/(?P<wm_token>\w{56})/?$', 'view_private_layer', name="view_private_layer"),
)

urlpatterns += patterns('geonode.dataverse_private_layer.views_request_private_layer_url',

    url(r'^request-private-layer-url/$', 'view_request_private_layer_url', name="view_request_private_layer_url"),
)
