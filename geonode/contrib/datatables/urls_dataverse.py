from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.contrib.datatables.views_dataverse',

   # Upload tabular file and join it to an existing layer
   #
   url(r'^upload-join/?$', 'view_upload_table_and_join_layer',\
    name='view_upload_table_and_join_layer'),

   url(r'^upload-lat-lng/?$', 'view_upload_lat_lng_table',\
    name='view_upload_lat_lng_table'),

)
