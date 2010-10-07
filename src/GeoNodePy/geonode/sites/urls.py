from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.sites',),
}
urlpatterns = patterns('geonode.sites.views',
    #(r'^site/(\w+)/(?P<mapid>\d+)$', 'map_controller'),
    #(r'^site/(\w+)/(?P<mapid>\d+)/view$', 'view'),
    #(r'^site/(\w+)/(?P<mapid>\d+)/download/$', 'map_download'),
    #(r'^site/(\w+)/check/$', 'check_download'),
    #(r'^site/(\w+)/embed/$', 'embed'),
    #(r'^site/(\w+)/(?P<mapid>\d+)/embed$', 'embed'),
    #(r'^site/(\w+)/(?P<mapid>\d+)/data$', 'mapJSON'),
    #url(r'^site/(\w+)/search/?$', 'maps_search_page', name='maps_search'),
    #url(r'^site/(\w+)/search/api/?$', 'maps_search', name='maps_search_api'),
    #url(r'^site/(\w+)/(?P<mapid>\d+)/ajax-permissions$', 'ajax_map_permissions', name='ajax_map_permissions'),
    #
)