from django.conf.urls.defaults import *
from django.conf import settings
from staticfiles.urls import staticfiles_urlpatterns

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
    (r'^(?P<page>help)/?$', 'geonode.views.static'),
    (r'^developer/?$', 'geonode.views.developer'),
    (r'^lang\.js$', 'geonode.views.lang'),
    (r'^maps/', include('geonode.maps.urls')),
    (r'^proxy/', 'geonode.proxy.views.proxy'),
    (r'^geoserver/','geonode.proxy.views.geoserver'),
    url(r'^data/$', 'geonode.maps.views.browse_data', name='data'),
    url(r'^data/acls/?$', 'geonode.maps.views.layer_acls', name='layer_acls'),
    url(r'^data/search/?$', 'geonode.maps.views.search_page', name='search'),
    url(r'^data/search/api/?$', 'geonode.maps.views.metadata_search', name='search_api'),
    url(r'^data/search/detail/?$', 'geonode.maps.views.search_result_detail', name='search_result_detail'),
    url(r'^data/api/batch_permissions/?$', 'geonode.maps.views.batch_permissions'),
    url(r'^data/api/batch_delete/?$', 'geonode.maps.views.batch_delete'),
    url(r'^data/upload$', 'geonode.maps.views.upload_layer', name='data_upload'),
    (r'^data/download$', 'geonode.maps.views.batch_layer_download'),
    (r'^data/(?P<layername>[^/]*)$', 'geonode.maps.views.layerController'),
    (r'^data/(?P<layername>[^/]*)/ajax-permissions$', 'geonode.maps.views.ajax_layer_permissions'),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    (r'^accounts/ajax_login$', 'geonode.views.ajax_login'),
    (r'^accounts/ajax_lookup$', 'geonode.views.ajax_lookup'),
    (r'^accounts/login', 'django.contrib.auth.views.login'),
    (r'^accounts/logout', 'django.contrib.auth.views.logout'),
    (r'^avatar/', include('avatar.urls')),
    (r'^accounts/', include('registration.urls')),
    (r'^profiles/', include('profiles.urls')),
    )

# Extra static file endpoint for development use
if settings.SERVE_MEDIA:
    urlpatterns += staticfiles_urlpatterns()
