# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2017 OSGeo
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

from geonode.people.utils import get_valid_user
from geonode.geoserver.createlayer.utils import create_layer


class Command(BaseCommand):
    help = "Create an empty PostGIS vector layer in GeoNode."

    def add_arguments(self, parser):
        # positional arguments
        parser.add_argument('name', type=str)
        # named (optional arguments)
        parser.add_argument('--user',
                            help='Name of the user account which should own the created layer')
        parser.add_argument('--geometry',
                            default='Point',
                            help=('Geometry type of the layer to be created. '
                                  'Can be Point, LineString or Polygon. Default is Point')
                            )
        parser.add_argument('--attributes',
                            help=('A json representation of the attributes to create. '
                                  'Example: '
                                  '{ "field_str": "string", "field_int": "integer", '
                                  '"field_date": "date", "field_float": "float"}')
                            )
        parser.add_argument('--title',
                            default='No title',
                            help='Title for the layer to be created.'
                            )

    def handle(self, *args, **options):
        name = options.get('name')
        username = options.get('user')
        user = get_valid_user(username)
        title = options.get('title')
        geometry_type = options.get('geometry')
        attributes = options.get('attributes')
        create_layer(name, title, user, geometry_type, attributes)
