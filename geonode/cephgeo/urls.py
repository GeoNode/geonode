from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test

import views

urlpatterns = patterns('',
    url(r'^$', login_required(TemplateView.as_view(template_name='ceph_main.html')),
                           name='ceph_main'),
	url(r'^error/$', views.error ),
	url(r'^json_list/(?P<sort>[A-Za-z]+)/$', views.file_list_json ),
	url(r'^json_list/(?P<sort>[A-Za-z]+)/(?P<grid_ref>[A-Za-z0-9]+)/$', views.file_list_json ),
	url(r'^cart/$', views.get_cart, ),
	url(r'^cart_clear/$', views.clear_cart, ),
	url(r'^cart_json/$', views.get_cart_json, ),
	url(r'^geotypes/$', views.get_obj_ids_json, ),
	url(r'^ftp/$', views.create_ftp_folder, ),
	url(r'^ftp/(?P<projection>[A-Za-z0-9\-]+)/$', views.create_ftp_folder, ),
    url(r'^ftprequests/$', views.ftp_request_list, ),
	url(r'^ftprequests/(?P<sort>[A-Za-z]+)/$', views.ftp_request_list, ),
    url(r'^ftprequests/r=(?P<ftp_req_name>ftprequest_[0-9]{4}-[0-9]{2}-[0-9]{2}_[0-9]{4})/$', views.ftp_request_details),
    # Data Management Views
    url(r'^datamanager/$', views.management, name='data_management'),
    url(r'^datamanager/input/$', views.data_input ),
    url(r'^datamanager/remove_ceph_objects/$', views.data_remove ),
    url(r'^datamanager/update_layer_metadata/$', views.update_layer_metadata ),
    # url(r'^datamanager/update_fh_style/$', views.update_fh_style ),
    # url(r'^datamanager/update_fh_perms/$', views.update_fh_perms ),
    url(r'^datamanager/list/$', views.file_list_geonode ),
    url(r'^datamanager/list/(?P<sort>[A-Za-z]+)/$', views.file_list_geonode ),
    url(r'^datamanager/list/(?P<sort>[A-Za-z]+)/(?P<grid_ref>[A-Za-z0-9]+)/$', views.file_list_geonode ),
    url(r'^datamanager/list_ceph/$', views.file_list_ceph ),
    url(r'^datamanager/list_ceph/(?P<sort>[A-Za-z]+)/$', views.file_list_ceph ),

)
