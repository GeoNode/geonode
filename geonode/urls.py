# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

import django
from django.conf.urls import include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from geonode.sitemap import LayerSitemap, MapSitemap
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from django.contrib.sitemaps.views import sitemap

import geonode.proxy.urls
from . import views
from . import version

from geonode.api.urls import api
from geonode.api.views import verify_token, user_info, roles, users, admin_role
from geonode.base.views import thumbnail_upload

from geonode import geoserver, qgis_server  # noqa
from geonode.utils import check_ogc_backend
from geonode.monitoring import register_url_event
from geonode.messaging.urls import urlpatterns as msg_urls
from .people.views import CustomSignupView

admin.autodiscover()

js_info_dict = {
    'domain': 'djangojs',
    'packages': 'geonode'
}

sitemaps = {
    "layer": LayerSitemap,
    "map": MapSitemap
}

homepage = register_url_event()(TemplateView.as_view(template_name='index.html'))

urlpatterns = [
    url(r'^$',
        homepage,
        name='home'),
    url(r'^help/$',
        TemplateView.as_view(template_name='help.html'),
        name='help'),
    url(r'^developer/$',
        TemplateView.as_view(
            template_name='developer.html'),
        name='developer'),
    url(r'^about/$',
        TemplateView.as_view(template_name='about.html'),
        name='about'),
    url(r'^privacy_cookies/$',
        TemplateView.as_view(template_name='privacy-cookies.html'),
        name='privacy-cookies'),

    # Meta
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': sitemaps},
        name='sitemap'),
    url(r'^robots\.txt$', TemplateView.as_view(
        template_name='robots.txt'), name='robots'),
    url(r'(.*version\.txt)$', version.version, name='version'),
    url(r'^messages/', include(msg_urls))

]

urlpatterns += [

    # Layer views
    url(r'^layers/', include('geonode.layers.urls')),

    # Map views
    url(r'^maps/', include('geonode.maps.urls')),

    # Catalogue views
    url(r'^catalogue/', include('geonode.catalogue.urls')),

    # ident
    url(r'^ident.json$',
        views.ident_json,
        name='ident_json'),

    # h keywords
    url(r'^h_keywords_api$',
        views.h_keywords,
        name='h_keywords_api'),

    # Search views
    url(r'^search/$',
        TemplateView.as_view(template_name='search/search.html'),
        name='search'),

    # Social views
    url(r'^account/signup/', CustomSignupView.as_view(), name='account_signup'),
    url(r"^account/", include("allauth.urls")),
    url(r'^invitations/', include(
        'geonode.invitations.urls', namespace='geonode.invitations')),
    url(r'^people/', include('geonode.people.urls')),
    url(r'^avatar/', include('avatar.urls')),
    url(r'^comments/', include('dialogos.urls')),
    url(r'^ratings/', include('pinax.ratings.urls', namespace='pinax_ratings')),
    url(r'^activity/', include('actstream.urls')),
    url(r'^announcements/', include('announcements.urls')),
    url(r'^messages/', include('user_messages.urls')),
    url(r'^social/', include('geonode.social.urls')),
    url(r'^security/', include('geonode.security.urls')),

    # Accounts
    url(r'^account/ajax_login$',
        geonode.views.ajax_login,
        name='account_ajax_login'),
    url(r'^account/ajax_lookup$',
        geonode.views.ajax_lookup,
        name='account_ajax_lookup'),
    url(
        r'^account/moderation_sent/(?P<inactive_user>[^/]*)$',
        geonode.views.moderator_contacted,
        name='moderator_contacted'),

    url(r'^groups/', include('geonode.groups.urls')),
    url(r'^documents/', include('geonode.documents.urls')),
    url(r'^services/', include('geonode.services.urls')),
    url(r'^base/', include('geonode.base.urls')),

    # OAuth Provider
    url(r'^o/',
        include('oauth2_provider.urls',
                namespace='oauth2_provider')),

    # Api Views
    url(r'^api/o/v4/tokeninfo',
        verify_token, name='tokeninfo'),
    url(r'^api/o/v4/userinfo',
        user_info, name='userinfo'),
    url(r'^api/roles', roles, name='roles'),
    url(r'^api/adminRole', admin_role, name='adminRole'),
    url(r'^api/users', users, name='users'),
    url(r'', include(api.urls)),

    # Curated Thumbnail
    url(r'^base/(?P<res_id>[^/]+)/thumbnail_upload$', thumbnail_upload,
        name='thumbnail_upload'),

    # tinymce WYSIWYG HTML Editor
    url(r'^tinymce/', include('tinymce.urls')),
]

urlpatterns += i18n_patterns(
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls, name="admin"),
)

# Internationalization Javascript
urlpatterns += [
    url(r'^i18n/', include(django.conf.urls.i18n), name="i18n"),
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), js_info_dict, name='javascript-catalog')
]

urlpatterns += [  # '',
    url(r'^showmetadata/',
        include('geonode.catalogue.metadataxsl.urls')),
]

if settings.FAVORITE_ENABLED:
    urlpatterns += [  # '',
        url(r'^favorite/',
            include('geonode.favorite.urls')),
    ]

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    if settings.CREATE_LAYER:
        urlpatterns += [  # '',
            url(r'^createlayer/',
                include('geonode.geoserver.createlayer.urls')),
        ]

    from geonode.geoserver.views import get_capabilities
    # GeoServer Helper Views
    urlpatterns += [  # '',
        # Upload views
        url(r'^upload/', include('geonode.upload.urls')),
        # capabilities
        url(r'^capabilities/layer/(?P<layerid>\d+)/$',
            get_capabilities, name='capabilities_layer'),
        url(r'^capabilities/map/(?P<mapid>\d+)/$',
            get_capabilities, name='capabilities_map'),
        url(r'^capabilities/user/(?P<user>[\w.@+-]+)/$',
            get_capabilities, name='capabilities_user'),
        url(r'^capabilities/category/(?P<category>\w+)/$',
            get_capabilities, name='capabilities_category'),
        url(r'^gs/', include('geonode.geoserver.urls')),
    ]
elif check_ogc_backend(qgis_server.BACKEND_PACKAGE):
    # QGIS Server's urls
    urlpatterns += [  # '',
        url(r'^qgis-server/',
            include(('geonode.qgis_server.urls', 'geonode.qgis_server'),
                    namespace='qgis_server')),
    ]

if settings.NOTIFICATIONS_MODULE in settings.INSTALLED_APPS:
    notifications_urls = f'{settings.NOTIFICATIONS_MODULE}.urls'
    urlpatterns += [  # '',
        url(r'^notifications/', include(notifications_urls)),
    ]
if "djmp" in settings.INSTALLED_APPS:
    urlpatterns += [  # '',
        url(r'^djmp/', include('djmp.urls')),
    ]

# Set up proxy
urlpatterns += geonode.proxy.urls.urlpatterns

# Serve static files
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.LOCAL_MEDIA_URL,
                      document_root=settings.MEDIA_ROOT)
handler401 = 'geonode.views.err403'
handler403 = 'geonode.views.err403'
handler404 = 'geonode.views.handler404'
handler500 = 'geonode.views.handler500'

# Featured Maps Pattens
urlpatterns += [  # '',
    url(r'^featured/(?P<site>[A-Za-z0-9_\-]+)/$',
        geonode.maps.views.featured_map),
    url(r'^featured/(?P<site>[A-Za-z0-9_\-]+)/info$',
        geonode.maps.views.featured_map_info),
]


if settings.MONITORING_ENABLED:
    urlpatterns += [url(r'^monitoring/',
                        include(('geonode.monitoring.urls', 'geonode.monitoring'),
                                namespace='monitoring'))]
