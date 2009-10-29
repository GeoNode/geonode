from django.conf.urls.defaults import *
from django.conf import settings

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
)
