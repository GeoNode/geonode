from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    url(r'^$', 'maps', name='maps_home'),
    url(r'^new$', 'newmap', name="maps_new"),
    url(r'^new/data$', 'newmapJSON', name='maps_newJSON'),
    url(r'^(?P<mapid>\d+)$', 'map_controller', name='maps_controller'),
    url(r'^(?P<mapid>\d+)/view$', 'view', name='maps_view'),
    url(r'^(?P<mapid>\d+)/download/$', 'map_download', name='maps_download'),
    url(r'^check/$', 'check_download', name='maps_download_check'),
    (r'^embed/$', 'embed'),
    (r'^(?P<mapid>\d+)/embed$', 'embed'),
    (r'^(?P<mapid>\d+)/data$', 'mapJSON'),
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^search/api/?$', 'maps_search', name='maps_search_api'),
    url(r'^(?P<mapid>\d+)/ajax-permissions$', 'ajax_map_permissions', name='ajax_map_permissions'),
    url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name="change_poc"),
)

datapatterns = patterns('geonode.maps.views',
  url(r'^$', 'browse_data', name='data_home'),
  url(r'^acls/?$', 'layer_acls', name='layer_acls'),
  url(r'^search/?$', 'search_page', name='search'),
  url(r'^search/api/?$', 'metadata_search', name='search_api'),
  url(r'^search/detail/?$', 'search_result_detail', name='search_result_detail'),
  url(r'^api/batch_permissions/?$', 'batch_permissions'),
  url(r'^api/batch_delete/?$', 'batch_delete'),
  url(r'^upload$', 'upload_layer', name='data_upload'),
  (r'^download$', 'batch_layer_download'),
  url(r'^(?P<layername>[^/]*)$', 'layer_detail', name="layer_detail"),
  url(r'^(?P<layername>[^/]*)/metadata$', 'layer_metadata', name="layer_metadata"),
  url(r'^(?P<layername>[^/]*)/remove$', 'layer_remove', name="layer_remove"),
  url(r'^(?P<layername>[^/]*)/replace$', 'layer_replace', name="layer_replace"),
  url(r'^(?P<layername>[^/]*)/style$', 'layer_style', name="layer_style"),
  (r'^(?P<layername>[^/]*)/ajax-permissions$', 'ajax_layer_permissions'),
)
