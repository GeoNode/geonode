
from django.conf.urls.defaults import *

from geonode.capabilities import views


urlpatterns = patterns('geonode.capabilities.views',
    url(r'^map/(?P<mapid>\d+)/$', 'get_capabilities', name="capabilities_map"),
    url(r'^user/(?P<user>\w+)/$', 'get_capabilities', name="capabilities_user"),
    url(r'^category/(?P<category>\w+)/$', 'get_capabilities', name="capabilities_category"),
    )