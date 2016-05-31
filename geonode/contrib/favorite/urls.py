from django.conf.urls import patterns, url

urlpatterns = patterns(
    'geonode.contrib.favorite.views',
    url(r'^document/(?P<id>\d+)$', 'favorite', {'subject': 'document'}, name='add_favorite_document'),
    url(r'^map/(?P<id>\d+)$', 'favorite', {'subject': 'map'}, name='add_favorite_map'),
    url(r'^layer/(?P<id>\d+)$', 'favorite', {'subject': 'layer'}, name='add_favorite_layer'),
    url(r'^user/(?P<id>\d+)$', 'favorite', {'subject': 'user'}, name='add_favorite_user'),
    url(r'^(?P<id>\d+)/delete$', 'delete_favorite', name='delete_favorite'),
    url(r'^list/$', 'get_favorites', name='favorite_list'),
    )
