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

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Update the IP of local map layers'

    def handle(self, *args, **options):
        from geonode.maps.models import MapLayer
        from django.conf import settings

        map_layers = MapLayer.objects.filter(local=True)
        for maplayer in map_layers:
            maplayer.ows_url = settings.SITEURL + "geoserver/wms"
            maplayer.save()
