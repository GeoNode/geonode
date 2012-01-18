from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    (r'^$', 'maps'),
    url(r'^new$', 'newmap', name="map_new"),
    url(r'^new/data$', 'newmapJSON'),
    (r'^(?P<mapid>\d+)$', 'map_controller'),
    (r'^(?P<mapid>\d+)/view$', 'view'),
    (r'^(?P<mapid>\d+)/download/$', 'map_download'),
    (r'^check/$', 'check_download'),
    (r'^embed/$', 'embed'),
    (r'^(?P<mapid>\d+)/embed$', 'embed'),
    (r'^(?P<mapid>\d+)/data$', 'mapJSON'),
    url(r'^(?P<mapid>\d+)/ajax-permissions$', 'ajax_map_permissions', name='ajax_map_permissions'),
    url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name="change_poc"),
)

datapatterns = patterns('geonode.maps.views',
  url(r'^$', 'browse_data', name='data'),
  url(r'^acls/?$', 'layer_acls', name='layer_acls'),
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
