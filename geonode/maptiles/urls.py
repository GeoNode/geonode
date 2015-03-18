from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
import views

urlpatterns = patterns('',
						url(r'^/?$',views.tiled_view),
                        url(r'^/test/?$',TemplateView.as_view(template_name="maptiles_geoext_test.html"))
						)
