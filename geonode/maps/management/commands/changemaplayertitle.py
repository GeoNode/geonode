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

from django.core.management.base import BaseCommand, CommandError
from django.utils import simplejson as json


class Command(BaseCommand):
    help = ('Change the title of a layer on a particular map.\n\n'
            'Arguments:\n'
            'map_id - numeric map ID\n'
            'name - name of the layer (e.g., geonode:layer_name)\n'
            'title - title of layer as it should appear on the specified map')

    args = 'map_id name title'

    def handle(self, *args, **options):
        from geonode.maps.models import MapLayer

        if len(args) == 3:
            map_id, name, title = args
        else:
            raise CommandError("You must specify three arguments: map_id name title")

        maplayer = MapLayer.objects.filter(map_id=map_id, name=name)[0]

        layer_params = json.loads(maplayer.layer_params)
        layer_params['title'] = title
        layer_params['capability']['title'] = title
        maplayer.layer_params = json.dumps(layer_params)
        maplayer.save()
