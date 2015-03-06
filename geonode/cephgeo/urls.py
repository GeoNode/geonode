from django.conf.urls import patterns, include, url
from django.contrib import admin
import views

urlpatterns = patterns('',
	url(r'^list/$', views.file_list ),
	url(r'^list/(?P<sort>[A-Za-z]+)/$', views.file_list, )
)
