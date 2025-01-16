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
from django.urls import path
from django.conf.urls import include
from django.urls import re_path
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf.urls.static import static
from geonode.sitemap import DatasetSitemap, MapSitemap
from django.views.generic import TemplateView
from django.contrib import admin
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import JavaScriptCatalog
from django.contrib.sitemaps.views import sitemap

import geonode.proxy.urls
from . import views
from . import version

from geonode.api.urls import api, router
from geonode.api.views import verify_token, user_info, roles, users, admin_role

from geonode import geoserver
from geonode.utils import check_ogc_backend
from geonode.base import register_url_event
from geonode.messaging.urls import urlpatterns as msg_urls
from .people.views import CustomSignupView, CustomLoginView
from oauth2_provider.urls import app_name as oauth2_app_name, base_urlpatterns, oidc_urlpatterns

admin.autodiscover()

js_info_dict = {"domain": "djangojs", "packages": "geonode"}

sitemaps = {"dataset": DatasetSitemap, "map": MapSitemap}

homepage = register_url_event()(TemplateView.as_view(template_name="index.html"))

urlpatterns = [
    re_path(r"^$", homepage, name="home"),
    re_path(r"^help/$", TemplateView.as_view(template_name="help.html"), name="help"),
    re_path(r"^developer/$", TemplateView.as_view(template_name="developer.html"), name="developer"),
    re_path(r"^about/$", TemplateView.as_view(template_name="about.html"), name="about"),
    re_path(r"^privacy_cookies/$", TemplateView.as_view(template_name="privacy-cookies.html"), name="privacy-cookies"),
    # Meta
    re_path(r"^sitemap\.xml$", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    re_path(r"^robots\.txt$", TemplateView.as_view(template_name="robots.txt"), name="robots"),
    re_path(r"(.*version\.txt)$", version.version, name="version"),
    re_path(r"^messages/", include(msg_urls)),
]

urlpatterns += [
    # ResourceBase views
    re_path(r"^base/", include("geonode.base.urls")),
    re_path(r"^resources/", include("geonode.base.base_urls")),
    # Dataset views
    re_path(r"^datasets/", include("geonode.layers.urls")),
    # Remote Services views
    re_path(r"^services/", include("geonode.services.urls")),
    # Map views
    re_path(r"^maps/", include("geonode.maps.urls")),
    # Documents views
    re_path(r"^documents/", include("geonode.documents.urls")),
    # Apps views
    re_path(r"^apps/", include("geonode.geoapps.urls")),
    # Catalogue views
    re_path(r"^catalogue/", include("geonode.catalogue.urls")),
    # Group Profiles views
    re_path(r"^groups/", include("geonode.groups.urls")),
    # Harvesting views
    re_path(r"^harvesters/", include("geonode.harvesting.urls")),
    # ident
    re_path(r"^ident.json$", views.ident_json, name="ident_json"),
    # h keywords
    re_path(r"^h_keywords_api$", views.h_keywords, name="h_keywords_api"),
    # Social views
    re_path(r"^account/signup/", CustomSignupView.as_view(), name="account_signup"),
    re_path(r"^account/login/", CustomLoginView.as_view(), name="account_login"),
    re_path(r"^account/", include("allauth.urls")),
    re_path(r"^invitations/", include("geonode.invitations.urls", namespace="geonode.invitations")),
    re_path(r"^people/", include("geonode.people.urls")),
    re_path(r"^api/v2/users/", include("geonode.people.api.urls")),
    re_path(r"^avatar/", include("avatar.urls")),
    re_path(r"^activity/", include("actstream.urls")),
    re_path(r"^announcements/", include("announcements.urls")),
    re_path(r"^messages/", include("user_messages.urls")),
    re_path(r"^social/", include("geonode.social.urls")),
    re_path(r"^security/", include("geonode.security.urls")),
    # Accounts
    re_path(r"^account/ajax_login$", geonode.views.ajax_login, name="account_ajax_login"),
    re_path(r"^account/ajax_lookup$", geonode.views.ajax_lookup, name="account_ajax_lookup"),
    re_path(
        r"^account/moderation_sent/(?P<inactive_user>[^/]*)$",
        geonode.views.moderator_contacted,
        name="moderator_contacted",
    ),
    re_path(
        r"^account/moderation_needed/",
        geonode.views.moderator_needed,
        name="moderator_needed",
    ),
    # OAuth2/OIDC Provider
    re_path(r"^o/", include((base_urlpatterns + oidc_urlpatterns, oauth2_app_name), namespace="oauth2_provider")),
    re_path(r"^api/o/v4/tokeninfo", verify_token, name="tokeninfo"),
    re_path(r"^api/o/v4/userinfo", user_info, name="userinfo"),
    # Api Views
    re_path(r"^api/roles", roles, name="roles"),
    re_path(r"^api/adminRole", admin_role, name="adminRole"),
    re_path(r"^api/users", users, name="users"),
    re_path(r"^api/v2/", include(router.urls)),
    re_path(r"^api/v2/", include("geonode.api.urls")),
    re_path(r"^api/v2/", include("geonode.management_commands_http.urls")),
    re_path(r"^api/v2/api-auth/", include("rest_framework.urls", namespace="geonode_rest_framework")),
    re_path(r"^api/v2/", include("geonode.facets.urls")),
    re_path(r"^api/v2/", include("geonode.assets.urls")),
    re_path(r"", include(api.urls)),
]

# tinymce WYSIWYG HTML Editor
if "tinymce" in settings.INSTALLED_APPS:
    urlpatterns += [
        re_path(r"^tinymce/", include("tinymce.urls")),
    ]

# django-select2 Widgets
if "django_select2" in settings.INSTALLED_APPS:
    urlpatterns += [
        path("select2/", include("django_select2.urls")),
    ]

urlpatterns += i18n_patterns(
    re_path(r"^grappelli/", include("grappelli.urls")),
    re_path(r"^admin/", admin.site.urls, name="admin"),
)

# Internationalization Javascript
urlpatterns += [
    re_path(r"^i18n/", include(django.conf.urls.i18n), name="i18n"),
    re_path(r"^jsi18n/$", JavaScriptCatalog.as_view(), js_info_dict, name="javascript-catalog"),
]

urlpatterns += [  # '',
    re_path(r"^showmetadata/", include("geonode.catalogue.metadataxsl.urls")),
]

if check_ogc_backend(geoserver.BACKEND_PACKAGE):
    if settings.CREATE_LAYER:
        urlpatterns += [  # '',
            re_path(r"^createlayer/", include("geonode.geoserver.createlayer.urls")),
        ]

    from geonode.geoserver.views import get_capabilities

    # GeoServer Helper Views
    urlpatterns += [  # '',
        # Upload views
        re_path(r"^upload/", include("geonode.upload.urls")),
        # capabilities - DEPRECATED: these urls and views will be removed in future versions of GeoNode
        re_path(r"^capabilities/layer/(?P<layerid>\d+)/$", get_capabilities, name="capabilities_dataset"),
        re_path(r"^capabilities/map/(?P<mapid>\d+)/$", get_capabilities, name="capabilities_map"),
        re_path(r"^capabilities/user/(?P<user>[\w.@+-]+)/$", get_capabilities, name="capabilities_user"),
        re_path(r"^capabilities/category/(?P<category>\w+)/$", get_capabilities, name="capabilities_category"),
        re_path(r"^gs/", include("geonode.geoserver.urls")),
    ]

if settings.NOTIFICATIONS_MODULE in settings.INSTALLED_APPS:
    notifications_urls = f"{settings.NOTIFICATIONS_MODULE}.urls"
    urlpatterns += [  # '',
        re_path(r"^notifications/", include(notifications_urls)),
    ]
if "djmp" in settings.INSTALLED_APPS:
    urlpatterns += [  # '',
        re_path(r"^djmp/", include("djmp.urls")),
    ]

# Set up proxy
urlpatterns += geonode.proxy.urls.urlpatterns

# Serve static files
urlpatterns += staticfiles_urlpatterns()
urlpatterns += static(settings.LOCAL_MEDIA_URL, document_root=settings.MEDIA_ROOT)
handler401 = "geonode.views.err403"
handler403 = "geonode.views.err403"
handler404 = "geonode.views.handler404"
handler500 = "geonode.views.handler500"


if settings.MONITORING_ENABLED:
    urlpatterns += [
        re_path(r"^monitoring/", include(("geonode.monitoring.urls", "geonode.monitoring"), namespace="monitoring"))
    ]


# Internationalization Javascript
urlpatterns += [
    re_path(r"^metadata_update_redirect$", views.metadata_update_redirect, name="metadata_update_redirect"),
]
