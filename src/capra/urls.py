from django.conf.urls.defaults import *
from geonode.urls import urlpatterns

urlpatterns += patterns('capra.hazard.views',
    (r'^hazard/', 'index'),
)
