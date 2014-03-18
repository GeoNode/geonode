from django.conf.urls.defaults import *


urlpatterns = patterns('geonode.contrib.groups.views',
    url(r'^$', 'group_list', name="group_list"),
    url(r'^create/$', 'group_create', name="group_create"),
    url(r'^group/(?P<slug>[-\w]+)/$', 'group_detail', name='group_detail'),
    url(r'^group/(?P<slug>[-\w]+)/update/$', 'group_update', name='group_update'),
    url(r'^group/(?P<slug>[-\w]+)/members/$', 'group_members', name='group_members'),
    url(r'^group/(?P<slug>[-\w]+)/invite/$', 'group_invite', name='group_invite'),
    url(r'^group/(?P<slug>[-\w]+)/join/$', 'group_join', name='group_join'),
    url(r'^group/(?P<slug>[-\w]+)/maps/$', 'group_add_maps', name='group_add_maps'),
    url(r'^group/(?P<slug>[-\w]+)/layers/$', 'group_add_layers', name='group_add_layers'),
    url(r'^group/(?P<slug>[-\w]+)/remove/$', 'group_remove_maps_data', name='group_remove_maps_data'),
    url(r'^group/[-\w]+/invite/(?P<token>[\w]{40})/$', 'group_invite_response', name='group_invite_response'),
)
