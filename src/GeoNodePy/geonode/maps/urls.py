from django.conf.urls.defaults import patterns

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    (r'^$', 'maps'),
    (r'^new$', 'newmap'),
    (r'^(?P<mapid>\d+)$', 'maps'),
    (r'^(?P<mapid>\d+).html$', 'view'),
    (r'^embed/$', 'embed'),
    (r'^embed/(?P<mapid>\d+)$', 'embed'),
  
    # map information page
    (r'^detail/(?P<mapid>\d+)$', 'mapinfo'),
)
