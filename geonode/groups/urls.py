from django.conf.urls import patterns, url
from django.views.generic import TemplateView

from .views import GroupDetailView, GroupActivityView

urlpatterns = patterns('geonode.groups.views',
                       url(r'^$', TemplateView.as_view(template_name='groups/group_list.html'), name="group_list"),
                       url(r'^create/$', 'group_create', name="group_create"),
                       url(r'^group/(?P<slug>[-\w]+)/$', GroupDetailView.as_view(), name='group_detail'),
                       url(r'^group/(?P<slug>[-\w]+)/update/$', 'group_update', name='group_update'),
                       url(r'^group/(?P<slug>[-\w]+)/members/$', 'group_members', name='group_members'),
                       url(r'^group/(?P<slug>[-\w]+)/invite/$', 'group_invite', name='group_invite'),
                       url(r'^group/(?P<slug>[-\w]+)/members_add/$', 'group_members_add', name='group_members_add'),
                       url(r'^group/(?P<slug>[-\w]+)/member_remove/(?P<username>.+)$', 'group_member_remove',
                           name='group_member_remove'),
                       url(r'^group/(?P<slug>[-\w]+)/remove/$', 'group_remove', name='group_remove'),
                       url(r'^group/(?P<slug>[-\w]+)/join/$', 'group_join', name='group_join'),
                       url(r'^group/[-\w]+/invite/(?P<token>[\w]{40})/$', 'group_invite_response',
                           name='group_invite_response'),
                       url(r'^group/(?P<slug>[-\w]+)/activity/$', GroupActivityView.as_view(), name='group_activity'),
                       )
