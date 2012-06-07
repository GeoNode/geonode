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
