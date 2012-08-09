#########################################################################
#
# Copyright (C) 2012 OpenPlans
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from django.conf.urls import include, patterns, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from geonode.sitemap import LayerSitemap, MapSitemap
import geonode.proxy.urls
import geonode.maps.urls

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

    # Static pages
    url(r'^$', 'django.views.generic.simple.direct_to_template',
                {'template': 'index.html'}, name='home'),
    url(r'^help/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'help.html'}, name='help'),
    url(r'^developer/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'developer.html'}, name='dev'),

    # Temp static pages
    url(r'^mapinfo/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'maps/map_detail_static.html'}, name='mapinfo'),
    url(r'^layerinfo/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'layers/layer_detail_static.html'}, name='layerinfo'),
    url(r'^search/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'search.html'}, name='search'),
    url(r'^advanced-search/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'advanced_search_static.html'}, name='advanced_search'),
    url(r'^upload/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'upload/upload.html'}, name='upload'),
    url(r'^upload-info/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'upload/upload_info.html'}, name='upload_info'),
    url(r'^upload-permissions/$', 'django.views.generic.simple.direct_to_template',
                {'template': 'upload/upload_permissions.html'}, name='upload_permissions'),

    # Data views
    (r'^data/', include('geonode.layers.urls')),

    # Map views
    (r'^maps/', include('geonode.maps.urls')),

    # Social
    (r'^comments/', include('dialogos.urls')),
    (r'^ratings/', include('agon_ratings.urls')),

    # Accounts
    url(r'^accounts/ajax_login$', 'geonode.views.ajax_login',
                                       name='auth_ajax_login'),
    url(r'^accounts/ajax_lookup$', 'geonode.views.ajax_lookup',
                                       name='auth_ajax_lookup'),
    (r'^accounts/', include('registration.urls')),
    (r'^profiles/', include('idios.urls')),
    (r'^people/', include('geonode.people.urls')),
    (r'^avatar/', include('avatar.urls')),

    # Meta
    url(r'^lang\.js$', 'django.views.generic.simple.direct_to_template',
         {'template': 'lang.js', 'mimetype': 'text/javascript'}, name='lang'),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
                                  js_info_dict, name='jscat'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
                                  {'sitemaps': sitemaps}, name='sitemap'),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^admin/', include(admin.site.urls)),
    )

urlpatterns += geonode.proxy.urls.urlpatterns

# Serve static files
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
