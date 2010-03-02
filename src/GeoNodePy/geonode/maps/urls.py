from django.conf.urls.defaults import patterns

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('geonode.maps.views',
    (r'^$', 'maps'),
    (r'^new$', 'newmap'),
    (r'^(?P<mapid>\d+)$', 'mapdetail'),
    (r'^(?P<mapid>\d+)/view$', 'view'),
    (r'^embed/$', 'embed'),
    (r'^(?P<mapid>\d+)/embed$', 'embed'),
  	(r'^(?P<mapid>\d+)/data$', 'mapJSON'),
    # map information page
    (r'^detail/(?P<mapid>\d+)$', 'mapdetail'),
   
)
