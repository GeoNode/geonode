from django.conf.urls.defaults import *
from django.conf import settings
from staticfiles.urls import staticfiles_urlpatterns
from geonode.sitemap import LayerSitemap, MapSitemap
import geonode.proxy.urls
import geonode.maps.urls
import geonode.gazetteer.urls

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
    (r'^maps/', include(geonode.maps.urls.urlpatterns)),
    (r'^data/', include(geonode.maps.urls.datapatterns)),
    (r'^admin/', include(admin.site.urls)),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict),
    (r'^accounts/ajax_login$', 'geonode.views.ajax_login'),
    (r'^accounts/ajax_lookup$', 'geonode.views.ajax_lookup'),
    (r'^accounts/ajax_lookup_email$', 'geonode.views.ajax_lookup_email'),
    (r'^accounts/login', 'django.contrib.auth.views.login'),
    (r'^accounts/logout', 'django.contrib.auth.views.logout'),
    (r'^affiliation/confirm', 'geonode.registration.views.confirm'),
    (r'^avatar/', include('avatar.urls')),
    (r'^accounts/', include('geonode.registration.urls')),
    (r'^profiles/', include('geonode.profiles.urls')),
    (r'^accounts/', include('registration.urls')),
    (r'^profiles/', include('profiles.urls')),
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),
    (r'^download/(?P<service>[^/]*)/(?P<layer>[^/]*)/(?P<format>[^/]*)/?$','geonode.proxy.views.download'),
    (r'^gazetteer/', include('geonode.gazetteer.urls'))
    )

urlpatterns += geonode.proxy.urls.urlpatterns


official_site_url_patterns = patterns('',
    (r'^(?P<site>[A-Za-z0-9_\-]+)/$', 'geonode.maps.views.official_site'),
    (r'^(?P<site>[A-Za-z0-9_\-]+)/edit$', 'geonode.maps.views.official_site_controller'),
)

urlpatterns += official_site_url_patterns

# Extra static file endpoint for development use
if settings.SERVE_MEDIA:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns(
        url(r'^site_media/media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }))
