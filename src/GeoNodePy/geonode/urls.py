from django.conf.urls.defaults import *
from django.conf import settings
from staticfiles.urls import staticfiles_urlpatterns
from geonode.sitemap import LayerSitemap, MapSitemap
from geonode.proxy.urls import urlpatterns as proxy_urlpatterns


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

js_info_dict = {
    'domain': 'djangojs',
    'packages': ('geonode',)
}

sitemaps = {
    "layer": LayerSitemap,
    "map": MapSitemap
}

urlpatterns = patterns('',
    # Example:
    # (r'^geonode/', include('geonode.foo.urls')),
    (r'^(?:index/?)?$', 'geonode.views.index'),
    (r'^(?P<page>developer|help|maphelp|about|maps\/upload_terms)/?$', 'geonode.views.static'),
    url(r'^lang\.js$', 'django.views.generic.simple.direct_to_template',
               {'template': 'lang.js', 'mimetype': 'text/javascript'}, 'lang'),
    (r'^maps/', include('geonode.maps.urls')),
    url(r'^data/$', 'geonode.maps.views.browse_data', name='data'),
    url(r'^data/acls/?$', 'geonode.maps.views.layer_acls', name='layer_acls'),
    url(r'^data/search/?$', 'geonode.maps.views.search_page', name='search'),
    url(r'^data/search/api/?$', 'geonode.maps.views.metadata_search', name='search_api'),
    url(r'^data/search/detail/?$', 'geonode.maps.views.search_result_detail', name='search_result_detail'),
    url(r'^data/addlayers/?$', 'geonode.maps.views.addlayers', name='addlayers'),
    url(r'^data/upload/?', 'geonode.maps.views.upload_layer', name='data_upload'),
    url(r'^upload/progress/$', 'geonode.maps.views.upload_progress', name='upload_progress'),
    url(r'^data/api/batch_permissions/?$', 'geonode.maps.views.batch_permissions'),
    url(r'^data/api/batch_permissions_by_email/?$', 'geonode.maps.views.batch_permissions_by_email'),
    url(r'^data/api/batch_delete/?$', 'geonode.maps.views.batch_delete'),
    (r'^data/download$', 'geonode.maps.views.batch_layer_download'),
    (r'^data/(?P<layername>[^/]*)$', 'geonode.maps.views.layerController'),
    (r'^data/(?P<layername>[^/]*)/ajax-permissions$', 'geonode.maps.views.ajax_layer_permissions'),
    (r'^data/(?P<layername>[^/]*)/ajax-permissions-email$', 'geonode.maps.views.ajax_layer_permissions_by_email'),
    (r'^data/(?P<layername>[^/]*)/ajax_layer_edit_check/?$', 'geonode.maps.views.ajax_layer_edit_check'),
    (r'^data/(?P<layername>[^/]*)/ajax_layer_update_bounds/?$', 'geonode.maps.views.ajax_layer_update_bounds'),
    (r'^data/layerstats/?$', 'geonode.maps.views.ajax_increment_layer_stats'),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    (r'^accounts/ajax_login$', 'geonode.views.ajax_login'),
    (r'^accounts/ajax_lookup$', 'geonode.views.ajax_lookup'),
    (r'^accounts/ajax_lookup_email$', 'geonode.views.ajax_lookup_email'),
    (r'^accounts/login', 'django.contrib.auth.views.login'),
    (r'^accounts/logout', 'django.contrib.auth.views.logout'),
    (r'^affiliation/confirm', 'geonode.accountforms.views.confirm'),
    (r'^avatar/', include('avatar.urls')),
    (r'^accounts/', include('geonode.accountforms.urls')),  
    (r'^profiles/', include('geonode.profileforms.urls')),
    (r'^accounts/', include('registration.urls')),
    (r'^profiles/', include('profiles.urls')),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'^download/(?P<service>[^/]*)/(?P<layer>[^/]*)/?$','geonode.proxy.views.download'),
    )

urlpatterns += proxy_urlpatterns


official_site_url_patterns = patterns('',
    (r'^(?P<site>\w+)/$', 'geonode.maps.views.official_site'),
    (r'^(?P<site>\w+)/edit$', 'geonode.maps.views.official_site_controller'),
)

urlpatterns += official_site_url_patterns

# Extra static file endpoint for development use
if settings.SERVE_MEDIA:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns(
        url(r'^site_media/media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }))
