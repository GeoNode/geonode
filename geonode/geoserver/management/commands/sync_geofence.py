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

import json
import sys

from django.core.management.base import BaseCommand

from geonode.layers.models import Layer
from geonode.security.views import _perms_info_json


class Command(BaseCommand):
    help = 'Synchronize GeoNode permissions in GeoFence'

    def add_arguments(self, parser):
        parser.add_argument(
            '--layername',
            dest='layername',
            default=None,
            help='Process layer/s which name contain layername.',
        )

    def handle(self, **options):
        if options['layername']:
            layers = Layer.objects.filter(name__icontains=options['layername'])
        else:
            layers = Layer.objects.all()

        layers_count = layers.count()
        count = 0

        for layer in layers:
            count += 1
            try:
                print 'Synchronizing permissions for layer %s/%s: %s' % (count, layers_count, layer.alternate)
                perm_spec = json.loads(_perms_info_json(layer))
                layer.set_permissions(perm_spec)
            except:
                print("Unexpected error:", sys.exc_info()[0])
                print 'perm_spec is %s' % perm_spec
