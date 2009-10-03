from django.conf.urls.defaults import *
from django.conf import settings
from utils import path_extrapolate

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^geonode/', include('geonode.foo.urls')),
    (r'^(?:index/?)?$', 'geonode.maps.views.index'),
    (r'^community/$', 'geonode.maps.views.community'),
    (r'^curated/$', 'geonode.maps.views.curated'),
    (r'^(?P<page>data|developer|help)/?$', 'geonode.maps.views.static'),
    (r'^lang\.js$', 'geonode.maps.views.lang'),
    (r'^maps/$', 'geonode.maps.views.maps'),
    (r'^maps/new$', 'geonode.maps.views.newmap'),
    (r'^maps/(?P<mapid>\d+)$', 'geonode.maps.views.maps'),
    (r'^maps/(?P<mapid>\d+).html$', 'geonode.maps.views.view'),
    (r'^maps/embed/$', 'geonode.maps.views.embed'),
    (r'^maps/embed/(?P<mapid>\d+)$', 'geonode.maps.views.embed'),
    (r'^proxy/', 'geonode.proxy.views.proxy'),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls))
)

#
# Extra static file endpoint for development use
if settings.DEBUG:
    import os
    def here(*x): 
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

    root = here("..", "geonode-client", "build", "geonode-client") if settings.MINIFIED_RESOURCES else here("..", "geonode-client", "")
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': root}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': path_extrapolate('django/contrib/admin/media', 'django')})
    )


