# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.layers',),
}

urlpatterns = patterns('geonode.layers.views',
  url(r'^$', 'layer_browse', name='layer_browse'),
  url(r'^acls/?$', 'layer_acls', name='layer_acls'),
  url(r'^search/?$', 'layer_search_page', name='layer_search_page'),
  url(r'^search/api/?$', 'layer_search', name='layer_search_api'),
  url(r'^search/detail/?$', 'layer_search_result_detail', name='layer_search_result_detail'),
  url(r'^upload$', 'layer_upload', name='layer_upload'),
  url(r'^download$', 'layer_batch_download', name='layer_batch_download'),
  url(r'^(?P<layername>[^/]*)$', 'layer_detail', name="layer_detail"),
  url(r'^(?P<layername>[^/]*)/metadata$', 'layer_metadata', name="layer_metadata"),
  url(r'^(?P<layername>[^/]*)/remove$', 'layer_remove', name="layer_remove"),
  url(r'^(?P<layername>[^/]*)/replace$', 'layer_replace', name="layer_replace"),
  url(r'^(?P<layername>[^/]*)/style$', 'layer_style', name="layer_style"),
  url(r'^(?P<layername>[^/]*)/ajax-permissions$', 'layer_ajax_permissions', name='layer_ajax_perm'),
  #url(r'^api/batch_permissions/?$', 'batch_permissions', name='batch_permssions'),
  #url(r'^api/batch_delete/?$', 'batch_delete', name='batch_delete'),
)
