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

from django.contrib.sitemaps import Sitemap
from geonode.maps.models import Map
from geonode.layers.models import Dataset
from guardian.shortcuts import get_objects_for_user
from django.contrib.auth.models import AnonymousUser


class DatasetSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        permitted = get_objects_for_user(AnonymousUser(), 'base.view_resourcebase')
        return Dataset.objects.filter(id__in=permitted)

    def lastmod(self, obj):
        return obj.date


class MapSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        permitted = get_objects_for_user(AnonymousUser(), 'base.view_resourcebase')
        return Map.objects.filter(id__in=permitted)
