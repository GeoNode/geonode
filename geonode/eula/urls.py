from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

import views

urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='eula.html'), name='eula'),
    url(r'^form/$', views.eula_form, name='eula_form'),
)
