from django.conf.urls.defaults import *

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    (r'^$', 'maps'),
    url(r'^new/?$', 'newmap', name="map_new"),
    url(r'^new/data$', 'newmapJSON'),
    (r'^(?P<mapid>\d+)/share/?$', 'map_share'),
    (r'^(?P<mapid>\d+)/edit/?$', 'map_controller'),
    (r'^(?P<mapid>\d+)/edit/describe/?$', 'describemap'),
    (r'^(?P<mapid>\d+)/download/?$', 'map_download'),
    (r'^check/?$', 'check_download'),
    (r'^checkurl/?$', 'ajax_url_lookup'),
    (r'^history/(?P<mapid>\d+)/?$', 'ajax_snapshot_history'),
    (r'^embed/?$', 'embed'),
    (r'^(?P<mapid>[A-Za-z0-9_\-]+)/embed/?$', 'embed'),
    (r'^(?P<mapid>[A-Za-z0-9_\-]+)/mobile/?$', 'mobilemap'),
    (r'^(?P<mapid>\d+)/data/?$', 'mapJSON'),
    (r'^addgeonodelayer/?$', 'addLayerJSON'),
    (r'^snapshot/create/?$', 'snapshot_create'),
    url(r'^search/?$', 'maps_search_page', name='maps_search'),
    url(r'^search/api/?$', 'maps_search', name='maps_search_api'),
    url(r'^(?P<mapid>\d+)/ajax-permissions/?$', 'ajax_map_permissions', name='ajax_map_permissions'),
    url(r'^(?P<mapid>\d+)/ajax-permissions-email/?$', 'ajax_map_permissions_by_email', name='ajax_map_permissions_by_email'),
    url(r'^change-poc/(?P<ids>\w+)/?$', 'change_poc', name="change_poc"),
    (r'^(?P<mapid>[A-Za-z0-9_\-]+)/(?P<snapshot>\w+)/?$', 'view'),
    (r'^(?P<mapid>[A-Za-z0-9_\-]+)/(?P<snapshot>\w+)/embed/?$', 'embed'),
    (r'^(?P<mapid>[A-Za-z0-9_\-]+)/(?P<snapshot>\w+)/mobile/?$', 'mobilemap'),
    (r'^(?P<mapid>[A-Za-z0-9_\-]+)/?$', 'view'),
)
