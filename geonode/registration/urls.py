from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required, user_passes_test

import views

urlpatterns = patterns('',
    url(r'^$'),
    url(r'^key/$', views.error ),
    url(r'^admin/$', views.error ),
)