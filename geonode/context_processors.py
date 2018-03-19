# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2016 OSGeo
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

from django.conf import settings
from geonode import get_version
from geonode.catalogue import default_catalogue_backend
from django.contrib.sites.models import Site

from geonode.notifications_helper import has_notifications


def resource_urls(request):
    """Global values to pass to templates"""
    site = Site.objects.get_current()
    defaults = dict(
        STATIC_URL=settings.STATIC_URL,
        CATALOGUE_BASE_URL=default_catalogue_backend()['URL'],
        ACCOUNT_OPEN_SIGNUP=settings.ACCOUNT_OPEN_SIGNUP,
        ACCOUNT_APPROVAL_REQUIRED=settings.ACCOUNT_APPROVAL_REQUIRED,
        VERSION=get_version(),
        SITE_NAME=site.name,
        SITE_DOMAIN=site.domain,
        SITEURL=settings.SITEURL,
        INSTALLED_APPS=settings.INSTALLED_APPS,
        THEME_ACCOUNT_CONTACT_EMAIL=settings.THEME_ACCOUNT_CONTACT_EMAIL,
        DEBUG_STATIC=getattr(
            settings,
            "DEBUG_STATIC",
            False),
        PROXY_URL=getattr(
            settings,
            'PROXY_URL',
            '/proxy/?url='),
        DISPLAY_SOCIAL=getattr(
            settings,
            'DISPLAY_SOCIAL',
            False),
        DISPLAY_COMMENTS=getattr(
            settings,
            'DISPLAY_COMMENTS',
            False),
        DISPLAY_RATINGS=getattr(
            settings,
            'DISPLAY_RATINGS',
            False),
        DISPLAY_WMS_LINKS=getattr(
            settings,
            'DISPLAY_WMS_LINKS',
            False),
        TWITTER_CARD=getattr(
            settings,
            'TWITTER_CARD',
            False),
        TWITTER_SITE=getattr(
            settings,
            'TWITTER_SITE',
            '@GeoNode'),
        TWITTER_HASHTAGS=getattr(
            settings,
            'TWITTER_HASHTAGS',
            []),
        OPENGRAPH_ENABLED=getattr(
            settings,
            'OPENGRAPH_ENABLED',
            False),
        ADMIN_MODERATE_UPLOADS=getattr(
            settings,
            'ADMIN_MODERATE_UPLOADS',
            False),
        GROUP_MANDATORY_RESOURCES=getattr(
            settings,
            'GROUP_MANDATORY_RESOURCES',
            False),
        GROUP_PRIVATE_RESOURCES=getattr(
            settings,
            'GROUP_PRIVATE_RESOURCES',
            False),
        RESOURCE_PUBLISHING=getattr(
            settings,
            'RESOURCE_PUBLISHING',
            False),
        HAYSTACK_SEARCH=getattr(
            settings,
            'HAYSTACK_SEARCH',
            False),
        SKIP_PERMS_FILTER=getattr(
            settings,
            'SKIP_PERMS_FILTER',
            False),
        HAYSTACK_FACET_COUNTS=getattr(
            settings,
            'HAYSTACK_FACET_COUNTS',
            False),
        CLIENT_RESULTS_LIMIT=getattr(
            settings,
            'CLIENT_RESULTS_LIMIT',
            10),
        API_LIMIT_PER_PAGE=getattr(
            settings,
            'API_LIMIT_PER_PAGE',
            20),
        SRID_DETAIL=getattr(
            settings,
            'SRID',
            dict()).get(
            'DETAIL',
            'never'),
        LICENSES_ENABLED=getattr(
            settings,
            'LICENSES',
            dict()).get(
            'ENABLED',
            False),
        LICENSES_DETAIL=getattr(
            settings,
            'LICENSES',
            dict()).get(
            'DETAIL',
            'never'),
        LICENSES_METADATA=getattr(
            settings,
            'LICENSES',
            dict()).get(
            'METADATA',
            'never'),
        USE_GEOSERVER=settings.USE_GEOSERVER,
        USE_NOTIFICATIONS=has_notifications,
        USE_MONITORING='geonode.contrib.monitoring' in settings.INSTALLED_APPS and settings.MONITORING_ENABLED,
        DEFAULT_ANONYMOUS_VIEW_PERMISSION=getattr(settings, 'DEFAULT_ANONYMOUS_VIEW_PERMISSION', False),
        DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION=getattr(settings, 'DEFAULT_ANONYMOUS_DOWNLOAD_PERMISSION', False),
        EXIF_ENABLED=getattr(
            settings,
            "EXIF_ENABLED",
            False),
        NLP_ENABLED=getattr(
            settings,
            "NLP_ENABLED",
            False),
        SEARCH_FILTERS=getattr(
            settings,
            'SEARCH_FILTERS',
            False
        ),
        THESAURI_FILTERS=[t['name'] for t in settings.THESAURI if t.get('filter')],
        MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS=getattr(
            settings, 'MAP_CLIENT_USE_CROSS_ORIGIN_CREDENTIALS', False
        ),
        SHOW_PROFILE_EMAIL=getattr(
            settings,
            "SHOW_PROFILE_EMAIL",
            False
        ),
        OGC_SERVER=getattr(settings, 'OGC_SERVER', None),
    )
    return defaults
