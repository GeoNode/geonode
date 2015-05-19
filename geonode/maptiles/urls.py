from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic import TemplateView
import views

urlpatterns = patterns('',
						url(r'^/?$',views.tiled_view),
                        url(r'^test/?$',views.tiled_view, { "overlay": settings.TILED_SHAPEFILE_TEST } ),
                        url(r'^addtocart/?$',views.process_georefs),
                        url(r'^validate/?$',views.georefs_validation)
						)
