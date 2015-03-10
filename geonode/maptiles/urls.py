from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
import geonode.maptiles.views

urlpatterns = patterns('',
						url(r'^/?$',tiled_view),
						)
