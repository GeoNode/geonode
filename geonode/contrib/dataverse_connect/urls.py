from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.contrib.dataverse_connect.views',

       #url(r'^check-for-existing-layer/?$', 'view_check_for_existing_layer', name='view_check_for_existing_layer'),     # Has a layer already been created with this file?

       url(r'^import-shapefile/?$', 'view_add_worldmap_shapefile', name='view_add_worldmap_shapefile'),

       url(r'^import-geotiff/?$', 'view_add_worldmap_geotiff', name='view_add_worldmap_geotiff'),

)


urlpatterns += patterns('geonode.contrib.dataverse_styles.views_sld',

#       url(r'^describe-features/(?P<layer_name>[^/]*)/$', 'view_layer_feature_defn', name='view_layer_feature_defn'),

       url(r'^classify-layer/$', 'view_create_new_layer_style', name='view_create_new_layer_style'),

       url(r'^get-classify-attributes/$', 'view_layer_classification_attributes', name='view_layer_classification_attributes'),


)


urlpatterns += patterns('geonode.contrib.dataverse_connect.views_delete',

       url(r'^delete-map-layer/$', 'view_delete_dataverse_map_layer',\
            name='view_delete_dataverse_map_layer'),

)

urlpatterns += patterns('geonode.contrib.dataverse_layer_metadata.views',

       url(r'^layer-info/$', 'get_existing_layer_data', name='get_existing_layer_data'),     # Does layer exist

      # url(r'^get-dataverse-user-layers/$', 'view_get_dataverse_user_layers', name='view_get_dataverse_user_layers'),     # Does layer exist
)
