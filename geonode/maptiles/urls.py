from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView

import geonode.settings as settings

import views


urlpatterns = patterns('',
						url(r'^/?$', views.tiled_view, name='maptiles_main'),
                        url(r'^test/?$', views.tiled_view, { "overlay": settings.TILED_SHAPEFILE ,"test_mode":True} ),
                        url(r'^interest=(?P<interest>[^/]*)$', views.tiled_view, {"overlay": settings.TILED_SHAPEFILE_TEST}),
                        url(r'^addtocart/?$', views.process_georefs),
                        url(r'^validate/?$', views.georefs_validation),
                        url(r'^provinces/?$', views.province_lookup),
                        url(r'^provinces/(?P<province>[^/]*)$', views.province_lookup),
						url(r'^datasize/?$', views.georefs_datasize),
						url(r'^test2/?$', views.tiled_view2, { "overlay": settings.TILED_SHAPEFILE ,"test_mode":True} )
						)
