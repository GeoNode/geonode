from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^geonode/', include('geonode.foo.urls')),
    (r'^(?:index/?)?$', 'geonode.maps.views.index'),
    (r'^community/$', 'geonode.maps.views.community'),
    (r'^(?P<page>data|developer|help)/?$', 'geonode.maps.views.static'),
    (r'^lang\.js$', 'geonode.maps.views.lang'),
    (r'^maps/$', 'geonode.maps.views.maps'),
    (r'^maps/new$', 'geonode.maps.views.newmap'),
    (r'^maps/(?P<mapid>\d+)$', 'geonode.maps.views.view'),
    (r'^maps/embed/$', 'geonode.maps.views.embed'),
    (r'^maps/embed/(?P<mapid>\d+)$', 'geonode.maps.views.embed'),
    (r'^proxy/', 'geonode.proxy.views.proxy'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', 
        {'document_root': './static'}),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls))
)
