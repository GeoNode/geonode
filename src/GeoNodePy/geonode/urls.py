from django.conf.urls.defaults import *
from django.conf import settings
from utils import path_extrapolate

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

js_info_dict = {
    'packages': ('geonode.maps',),
}

urlpatterns = patterns('',
    # Example:
    # (r'^geonode/', include('geonode.foo.urls')),
    (r'^(?:index/?)?$', 'geonode.views.index'),
    (r'^community/$', 'geonode.views.community'),
    (r'^(?P<page>developer|help)/?$', 'geonode.views.static'),
    (r'^lang\.js$', 'geonode.views.lang'),
    (r'^maps/', include('geonode.maps.urls')),
    (r'^proxy/', 'geonode.proxy.views.proxy'),
    (r'^geoserver/','geonode.proxy.views.geoserver'),
    url(r'^data/$', 'geonode.maps.views.browse_data', name='data'),
    url(r'^data/search/?$', 'geonode.maps.views.search_page', name='search'),
    url(r'^data/search/api/?$', 'geonode.maps.views.metadata_search', name='search_api'),
    url(r'^data/search/detail/?$', 'geonode.maps.views.search_result_detail', name='search_result_detail'),
    (r'^data/upload$', 'geonode.maps.views.upload_layer'),
    (r'^data/download$', 'geonode.maps.views.batch_layer_download'),
    (r'^data/(?P<layername>[^/]*)$', 'geonode.maps.views.layerController'),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    (r'^accounts/login', 'django.contrib.auth.views.login'),
    (r'^accounts/logout', 'django.contrib.auth.views.logout'),
    (r'^avatar/', include('avatar.urls')),
)

#
# Extra static file endpoint for development use
if settings.DEBUG:
    import os
    def here(*x): 
        return os.path.join(os.path.abspath(os.path.dirname(__file__)), *x)

    root = here("..", "..", "geonode-client", "build", "geonode-client") if settings.MINIFIED_RESOURCES else here("..", "..", "geonode-client", "")
    urlpatterns += patterns('',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': root}),
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': path_extrapolate('django/contrib/admin/media', 'django')})
    )


