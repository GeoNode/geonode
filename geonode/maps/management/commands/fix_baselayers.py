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

from geonode.maps.models import Map
from geonode.maps.utils import fix_baselayers


class Command(BaseCommand):
    help = ('Fix base layers for all of the GeoNode maps or for a given map.\n\n'
            'Arguments:\n'
            'map_id - numeric map ID (optional)\n')

    args = 'map_id'

    def handle(self, *args, **options):
        if len(args) == 1:
            map_id = args[0]
            fix_baselayers(map_id)
        else:
            for map in Map.objects.all():
                fix_baselayers(map.id)
