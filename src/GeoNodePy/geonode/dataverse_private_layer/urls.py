from django.conf.urls import patterns, include, url

# Keeping this code around for possible future use.
"""
urlpatterns = patterns('geonode.dataverse_private_layer.views',

    url(r'^view-private-layer/(?P<wm_token>\w{56})/?$', 'view_private_layer', name="view_private_layer"),
)

urlpatterns += patterns('geonode.dataverse_private_layer.views_request_private_layer_url',

    url(r'^request-private-layer-url/$', 'view_request_private_layer_url', name="view_request_private_layer_url"),

    url(r'^proxy-test/$', 'view_quick_test', name='view_quick_test'),

    url(r'^proxy-test2/$', 'view_proxy_test2', name='view_proxy_test2'),
)
"""