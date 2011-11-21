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
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^search/api/?$', 'maps_search', name='maps_search_api'),
    url(r'^(?P<mapid>\d+)/ajax-permissions$', 'ajax_map_permissions', name='ajax_map_permissions'),
    url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name="change_poc"),
    url(r'^newsearch/?$', 'new_search_page', name='new_search'),
    url(r'^newsearch/api?$', 'new_search_api', name='new_search_api'),
)
