from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.dvn.views',
       url(r'^import/?$', 'dvn_import', name='dvn_import'),
       url(r'^export/?$', 'dvn_export', name="dvn_export")
)

urlpatterns += patterns('geonode.dvn.views_sld',
       url(r'^describe-features/(?P<layer_name>[^/]*)/$', 'view_layer_feature_defn', name='view_layer_feature_defn'),

       url(r'^classify-layer/$', 'view_create_new_layer_style', name='view_create_new_layer_style'),
       
)