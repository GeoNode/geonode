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
from django.views.generic import TemplateView

import geonode.proxy.urls

# Setup Django Admin
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
    url(r'^$', 'geonode.views.index', name='home'),
    url(r'^help/$', TemplateView.as_view(template_name='help.html'), name='help'),
    url(r'^developer/$', TemplateView.as_view(template_name='developer.html'), name='developer'),
    url(r'^about/$', TemplateView.as_view(template_name='about.html'), name='about'),

    # Layer views
    (r'^layers/', include('geonode.layers.urls')),

    # Map views
    (r'^maps/', include('geonode.maps.urls')),

    # Catalogue views
    (r'^catalogue/', include('geonode.catalogue.urls')),

    # Search views
    (r'^search/', include('geonode.search.urls')),

    # Upload views
    (r'^upload/', include('geonode.upload.urls')),

    # GeoServer Helper Views 
    (r'^gs/', include('geonode.geoserver.urls')),

    # Social views
    (r"^account/", include("account.urls")),
    (r'^people/', include('geonode.people.urls')),
    (r'^avatar/', include('avatar.urls')),
    (r'^comments/', include('dialogos.urls')),
    (r'^ratings/', include('agon_ratings.urls')),
    (r'^activity/', include('actstream.urls')),
    (r'^announcements/', include('announcements.urls')),
    #(r'^notifications/', include('notification.urls')),
    (r'^messages/', include('user_messages.urls')),
    (r'^social/', include('geonode.social.urls')),
    # Accounts
    url(r'^account/ajax_login$', 'geonode.views.ajax_login',
                                       name='account_ajax_login'),
    url(r'^account/ajax_lookup$', 'geonode.views.ajax_lookup',
                                       name='account_ajax_lookup'),

    # Meta
    url(r'^lang\.js$', TemplateView.as_view(template_name='lang.js', content_type='text/javascript'), name='lang'),
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
                                  js_info_dict, name='jscat'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
                                  {'sitemaps': sitemaps}, name='sitemap'),
    (r'^i18n/', include('django.conf.urls.i18n')),
    (r'^admin/', include(admin.site.urls)),

    )

#Documents views
if 'geonode.documents' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^documents/', include('geonode.documents.urls')),
    )

urlpatterns += geonode.proxy.urls.urlpatterns

# Serve static files
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler403 = 'geonode.views.err403'
