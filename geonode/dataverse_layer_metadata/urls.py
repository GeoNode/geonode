from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.dataverse_layer_metadata.views',
               
       url(r'^get-existing-layer-info/$', 'get_existing_layer_data', name='get_existing_layer_data'),     # Does layer exist

      # url(r'^get-dataverse-user-layers/$', 'view_get_dataverse_user_layers', name='view_get_dataverse_user_layers'),     # Does layer exist
)

