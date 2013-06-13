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


def resource_urls(request):
    """Global values to pass to templates"""
    site = Site.objects.get_current()

    return dict(
        STATIC_URL=settings.STATIC_URL,
        GEOSERVER_BASE_URL=settings.GEOSERVER_BASE_URL,
        CATALOGUE_BASE_URL=default_catalogue_backend()['URL'],
        REGISTRATION_OPEN=settings.REGISTRATION_OPEN,
        VERSION=get_version(),
        SITE_NAME=site.name,
        SITE_DOMAIN=site.domain,
        DOCUMENTS_APP = settings.DOCUMENTS_APP,
        METADATA_DOWNLOAD_ALLOWS = settings.METADATA_DOWNLOAD_ALLOWS,
    )
