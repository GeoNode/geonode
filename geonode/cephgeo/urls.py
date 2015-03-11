from django.conf.urls import patterns, include, url
from django.contrib import admin
import views

urlpatterns = patterns('',
	url(r'^input/$', views.data_input ),
	url(r'^error/$', views.error ),
	url(r'^list/(?P<sort>[A-Za-z]+)/$', views.file_list_geonode ),
	url(r'^list/(?P<sort>[A-Za-z]+)/(?P<grid_ref>[A-Za-z0-9]+)/$', views.file_list_geonode ),
	url(r'^list_ceph/$', views.file_list_ceph ),
	url(r'^json_list/(?P<sort>[A-Za-z]+)/$', views.file_list_json ),
	url(r'^json_list/(?P<sort>[A-Za-z]+)/(?P<grid_ref>[A-Za-z0-9]+)/$', views.file_list_json ),
	url(r'^list_ceph/$', views.file_list_ceph ),
	url(r'^list_ceph/(?P<sort>[A-Za-z]+)/$', views.file_list_ceph, )
)
