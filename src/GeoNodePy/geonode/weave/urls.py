from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template
from geonode.weave import views
from django.conf import settings

urlpatterns = patterns('',
	url(r'^$', views.index, name='weave-index'),
	url(r'^(?P<visid>\d+)/$', views.edit, name='weave-edit'),
	url(r'^(?P<visid>\d+)/detail$', views.detail, name='weave-detail'),
	url(r'^(?P<visid>\d+)/sessionstate$', views.sessionstate, name='weave-sessionstate'),
	url(r'sessionstate$', views.sessionstate, name='weave-sessionstate'),
	url(r'^(?P<visid>\d+)/ajax-permissions$', views.ajax_visualization_permissions, name='ajax_visualization_permissions'),
	# url(r'^weaveStyle.css', direct_to_template, {'template': 'weaveStyle.css','mimetype': 'text/css'}),
)

