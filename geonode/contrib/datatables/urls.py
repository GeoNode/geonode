from django.conf.urls import patterns, url
from django.views.generic import TemplateView

js_info_dict = {
    'packages': ('geonode.contrib.datatables',),
}

urlpatterns = patterns('geonode.contrib.datatables.views',
   #-------------------
   # Datatables
   #-------------------
   # Upload
   url(r'^api/upload/?$', 'datatable_upload_api', name='datatable_upload_api'),

   # Get details
   url(r'^api/(?P<dt_id>\d+)/?$', 'datatable_detail', name='datatable_detail'),

   # Delete
   url(r'^api/(?P<dt_id>\d+)/remove/?$', 'datatable_remove', name='datatable_remove'),

   #-------------------
   # Datatable Joins
   #-------------------
   # Datatable Join to an existing layer
   url(r'^api/join/?$', 'tablejoin_api', name='tablejoin_api'),

   # Datatable Upload and Join to an existing layer
   url(r'^api/upload_and_join/?$', 'datatable_upload_and_join_api', name='datatable_upload_and_join_api'),

   #-------------------
   # Upload with lat/lon coordinates
   #-------------------
   url(r'^api/upload_lat_lon/?$', 'datatable_upload_lat_lon_api', name='datatable_upload_lat_lon_api'),

   # Delete
   url(r'^api/upload_lat_lon/(?P<dt_id>\d+)/remove/?$', 'datatable_lat_lon_remove', name='datatable_lat_lon_remove'),

   #-------------------------------
   # existing TableJoin  objects
   #-------------------------------

   # Retrieve TableJoin details
   url(r'^api/join/(?P<tj_id>\d+)/?$', 'tablejoin_detail', name='tablejoin_detail'),

   # Delete TableJoin
   url(r'^api/join/remove/(?P<tj_id>\d+)/?$', 'tablejoin_remove', name='tablejoin_remove'),

   #-------------------
   # JoinTarget
   #-------------------
   # Retrieve JoinTarget information
   url(r'^api/jointargets/?$', 'jointargets', name='jointargets'),

   )
