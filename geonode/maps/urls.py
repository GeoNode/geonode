# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    url(r'^$', 'maps_browse', name='maps_browse'),
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^search/api/?$', 'maps_search', name='maps_search_api'),
    url(r'^new$', 'new_map', name="new_map"),
    url(r'^new/data$', 'new_map_json', name='new_map_json'),
    url(r'^(?P<mapid>\d+)$', 'map_detail', name='map_detail'),
    url(r'^(?P<mapid>\d+)/view$', 'map_view', name='map_view'),
    url(r'^(?P<mapid>\d+)/data$', 'map_json', name='map_json'),
    url(r'^(?P<mapid>\d+)/download$', 'map_download', name='map_download'),
    url(r'^(?P<mapid>\d+)/remove$', 'map_remove', name='map_remove'),
    url(r'^(?P<mapid>\d+)/metadata$', 'map_metadata', name='map_metadata'),
    url(r'^(?P<mapid>\d+)/embed$', 'map_embed', name='map_embed'),
    url(r'^(?P<mapid>\d+)/ajax-permissions$', 'map_ajax_permissions', name='map_ajax_permissions'),
    url(r'^check/$', 'map_download_check', name='map_download_check'),
    url(r'^embed/$', 'map_embed', name='map_embed'),
    #url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name='maps_change_poc'),
)
