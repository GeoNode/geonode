from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.dataverse_layer_metadata.views',
        
       #url(r'^check-for-existing/$', 'get_existing_layer_data', name='get_existing_layer_data'),     # Does layer exist

       url(r'^get-existing-layer-info/$', 'get_existing_layer_data', name='get_existing_layer_data'),     # Does layer exist

       url(r'^get-dataverse-user-layers/$', 'view_get_dataverse_user_layers', name='view_get_dataverse_user_layers'),     # Does layer exist
)


#urlpatterns += patterns('geonode.dataverse_layer_metadata.view_embed_layer',

#    url(r'^view-embedded/$', 'view_embedded_layer', name='view_embedded_layer'),

#)

"""
urlpatterns += patterns('geonode.dataverse_layer_metadata.view_wms_services',

    url(r'^view-layer-legend/$', 'view_layer_legend', name='view_layer_legend'),

)
"""