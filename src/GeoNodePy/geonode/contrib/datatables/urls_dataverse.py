from django.conf.urls import patterns, url

urlpatterns = patterns('geonode.contrib.datatables.views_dataverse',

   # Upload tabular file and join it to an existing layer
   #
   url(r'^api/upload-join/?$', 'view_upload_table_and_join_layer', name='view_upload_table_and_join_layer'),

   # Get details
   #url(r'^api/(?P<dt_id>\d+)/$', 'datatable_detail', name='datatable_detail'),

   # Delete
   #url(r'^api/(?P<dt_id>\d+)/remove$', 'datatable_remove', name='datatable_remove'),

)