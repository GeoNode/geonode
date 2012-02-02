from django.conf.urls.defaults import *
from django.conf import settings
from django.views.generic.simple import direct_to_template

from staticfiles.urls import staticfiles_urlpatterns

from geonode.sitemap import LayerSitemap, MapSitemap
from geonode.proxy.urls import urlpatterns as proxy_urlpatterns

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

    url(r'^(?:index/?)?$',
        direct_to_template,
        {'template': 'index.html'},
        name='geonode_views_index'),

    (r'^(?P<page>help)/?$', 'geonode.views.static'),

    url(r'^developer/?$',
        direct_to_template,
        {'template': 'developer.html',
         'extra_context': {
                'GEOSERVER_BASE_URL': settings.GEOSERVER_BASE_URL,
                'GEONETWORK_BASE_URL': settings.GEONETWORK_BASE_URL,
                'site': settings.SITEURL
                }},
        name='geonode_views_developer'),

    url(r'^lang\.js$', 'django.views.generic.simple.direct_to_template',
               {'template': 'lang.js', 'mimetype': 'text/javascript'}, 'lang'),

    (r'^maps/', include('geonode.maps.urls')),

    url(r'^data/$', 'geonode.maps.views.browse_data', name='data'),
    url(r'^data/acls/?$', 'geonode.maps.views.layer_acls', name='layer_acls'),
    url(r'^data/search/?$', 'geonode.maps.views.search_page', name='search'),

    url(r'^data/search/api/?$',
        'geonode.maps.views.metadata_search',
        name='search_api'),

    url(r'^data/search/detail/?$',
        'geonode.maps.views.search_result_detail',
        name='search_result_detail'),

    url(r'^data/api/batch_permissions/?$',
        'geonode.maps.views.batch_permissions'),
    url(r'^data/api/batch_delete/?$', 'geonode.maps.views.batch_delete'),

    url(r'^data/upload$',
        'geonode.maps.views.upload_layer', name='data_upload'),

    (r'^data/download$', 'geonode.maps.views.batch_layer_download'),
    (r'^data/(?P<layername>[^/]*)$', 'geonode.maps.views.layerController'),

    (r'^data/(?P<layername>[^/]*)/ajax-permissions$',
     'geonode.maps.views.ajax_layer_permissions'),

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
    (r'^sitemap\.xml$',
     'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    )

urlpatterns += proxy_urlpatterns

# Extra static file endpoint for development use
if settings.SERVE_MEDIA:
    urlpatterns += staticfiles_urlpatterns()
