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

from django.conf import settings
from geonode import get_version
from geonode.catalogue import default_catalogue_backend
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse


def resource_urls(request):
    """Global values to pass to templates"""
    site = Site.objects.get_current()
    defaults = dict(
        STATIC_URL=settings.STATIC_URL,  
        CATALOGUE_BASE_URL=default_catalogue_backend()['URL'],
        REGISTRATION_OPEN=settings.REGISTRATION_OPEN,
        VERSION=get_version(),
        SITE_NAME=site.name,
        SITE_DOMAIN=site.domain,
        DEBUG_STATIC=getattr(settings, "DEBUG_STATIC", False),
        PROXY_URL=getattr(settings, 'PROXY_URL', '/proxy/?url='),
        SOCIAL_BUTTONS=getattr(settings, 'SOCIAL_BUTTONS', True),
        HAYSTACK_SEARCH=getattr(settings, 'HAYSTACK_SEARCH', False),
        CLIENT_RESULTS_LIMIT=getattr(settings, 'CLIENT_RESULTS_LIMIT', 10),
        LICENSES_ENABLED = getattr(settings, 'LICENSES', dict()).get('ENABLED', False),
        LICENSES_DETAIL = getattr(settings, 'LICENSES', dict()).get('DETAIL', 'never'),
        LICENSES_METADATA = getattr(settings, 'LICENSES', dict()).get('METADATA', 'never'),
    )
    
    return defaults
