# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    url(r'^$', 'maps_browse', name='maps_browse'),
    url(r'^new$', 'new_map', name="new_map"),
    url(r'^new/data$', 'new_map_json', name='maps_new_json'),
    #url(r'^(?P<mapid>\d+)$', 'map_controller', name='maps_controller'),
    url(r'^(?P<mapid>\d+)/view$', 'map_view', name='map_view'),
    url(r'^(?P<mapid>\d+)/download/$', 'map_download', name='maps_download'),
    url(r'^check/$', 'map_download_check', name='maps_download_check'),
    (r'^embed/$', 'map_embed'),
    (r'^(?P<mapid>\d+)/embed$', 'map_embed'),
    url(r'^(?P<mapid>\d+)/data$', 'map_json', name='maps_json'),
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^search/api/?$', 'maps_search', name='maps_search_api'),
    url(r'^(?P<mapid>\d+)/ajax-permissions$', 'map_ajax_permissions', name='maps_ajax_perm'),
    #url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name='maps_change_poc'),
)

datapatterns = patterns('geonode.layers.views',
  url(r'^$', 'layer_browse', name='layer_browse'),
  url(r'^acls/?$', 'layer_acls', name='data_acls'),
  url(r'^search/?$', 'layer_search_page', name='layer_search_page'),
  url(r'^search/api/?$', 'layer_search', name='layer_search_api'),
  url(r'^search/detail/?$', 'layer_search_result_detail', name='layer_search_result_detail'),
  #url(r'^api/batch_permissions/?$', 'batch_permissions', name='data_batch_perm'),
  #url(r'^api/batch_delete/?$', 'batch_delete', name='data_batch_del'),
  url(r'^upload$', 'layer_upload', name='layer_upload'),
  url(r'^download$', 'layer_batch_download', name='layer_batch_download'),
  url(r'^(?P<layername>[^/]*)$', 'layer_detail', name="data_detail"),
  url(r'^(?P<layername>[^/]*)/metadata$', 'layer_metadata', name="data_metadata"),
  url(r'^(?P<layername>[^/]*)/remove$', 'layer_remove', name="data_remove"),
  url(r'^(?P<layername>[^/]*)/replace$', 'layer_replace', name="data_replace"),
  url(r'^(?P<layername>[^/]*)/style$', 'layer_style', name="data_style"),
  url(r'^(?P<layername>[^/]*)/ajax-permissions$', 'layer_ajax_permissions', name='data_ajax_perm'),
)
