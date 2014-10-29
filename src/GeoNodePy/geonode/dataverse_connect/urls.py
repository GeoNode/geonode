from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.dataverse_connect.views',
       url(r'^import/?$', 'view_add_worldmap_shapefile', name='view_add_worldmap_shapefile'),     # First time layer creation
#       url(r'^export/?$', 'dvn_export', name="dvn_export")
)


urlpatterns += patterns('geonode.dataverse_connect.views_sld',
       url(r'^describe-features/(?P<layer_name>[^/]*)/$', 'view_layer_feature_defn', name='view_layer_feature_defn'),

       url(r'^classify-layer/$', 'view_create_new_layer_style', name='view_create_new_layer_style'),
       
)