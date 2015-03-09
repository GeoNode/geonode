from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

urlpatterns = patterns('',
						url(r'^/?$',TemplateView.as_view(template_name='maptiles/maptiles_base.html')),
						)
