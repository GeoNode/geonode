from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    (r'^$', 'maps'),
    url(r'^new$', 'newmap', name="map_new"),
    (r'^(?P<mapid>\d+)/edit/$', 'map_controller'),
    (r'^(?P<mapid>\d+)/edit/describe/$', 'describemap'),    
    (r'^(?P<mapid>\d+)/download/$', 'map_download'),
    (r'^check/$', 'check_download'),
    (r'^checkurl/$', 'ajax_url_lookup'),
    (r'^embed/$', 'embed'),
    (r'^(?P<mapid>\d+)/embed$', 'embed'),
    (r'^(?P<mapid>\d+)/data$', 'mapJSON'),
    (r'^searchfields/?$', 'searchFieldsJSON'),    
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^search/api/?$', 'maps_search', name='maps_search_api'),
    url(r'^(?P<mapid>\d+)/ajax-permissions$', 'ajax_map_permissions', name='ajax_map_permissions'),
    url(r'^(?P<mapid>\d+)/ajax-permissions-email$', 'ajax_map_permissions_by_email', name='ajax_map_permissions_by_email'),    
    url(r'^change-poc/(?P<ids>\w+)$', 'change_poc', name="change_poc"),
    (r'^updatelayers/$', 'updatelayers'),
    (r'^cleardeadlayers/$', 'cleardeadlayers'),
    (r'^(?P<mapid>\w+.*)/$', 'view'),
    (r'^(?P<mapid>\w+.*)/edit$', 'map_controller'),

)
