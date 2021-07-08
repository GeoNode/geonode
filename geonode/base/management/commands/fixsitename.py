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

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from urllib.parse import urlsplit


class Command(BaseCommand):
    """Overrides the default Site object with information from
       SITENAME and SITEURL
    """
    can_import_settings = True

    def handle(self, *args, **options):
        from django.conf import settings
        name = getattr(settings, 'SITENAME', 'GeoNode')
        site_url = getattr(settings, 'SITEURL')
        url = site_url.rstrip('/') if site_url.startswith('http') else site_url
        parsed = urlsplit(url)

        site = Site.objects.get_current()
        site.name = name
        site.domain = parsed.netloc
        site.save()
