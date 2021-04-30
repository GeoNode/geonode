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

import sys

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from geonode.geoserver.helpers import gs_catalog
from geonode.layers.models import Layer


def is_gs_resource_valid(layer):
    gs_resource = gs_catalog.get_resource(
        name=layer.name,
        store=layer.store,
        workspace=layer.workspace)
    if gs_resource:
        return True
    else:
        return False


class Command(BaseCommand):
    help = 'Find GeoNode layers with a missing GeoServer resource'

    def add_arguments(self, parser):
        parser.add_argument(
            '--layername',
            dest='layername',
            default=None,
            help='Filter by a layername.',
        )
        parser.add_argument(
            '--owner',
            dest='owner',
            default=None,
            help='Filter by a owner.',
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            dest='remove',
            default=False,
            help='Remove a layer if it is broken.',
        )

    def handle(self, **options):
        if options['layername']:
            layers = Layer.objects.filter(name__icontains=options['layername'])
        else:
            layers = Layer.objects.all()
        if options['owner']:
            layers = layers.filter(owner=get_user_model().objects.filter(username=options['owner']))

        layers_count = layers.count()
        count = 0

        layer_errors = []
        for layer in layers:
            count += 1
            try:
                print(f"Checking layer {count}/{layers_count}: {layer.alternate} owned by {layer.owner.username}")
                if not is_gs_resource_valid(layer):
                    print(f"Layer {layer.alternate} is broken!")
                    layer_errors.append(layer)
                    if options['remove']:
                        print("Removing this layer...")
                        layer.delete()
            except Exception:
                print("Unexpected error:", sys.exc_info()[0])

        print("\n***** Layers with errors: {} in a total of {} *****".format(
            len(layer_errors),
            layers_count
        ))
        for layer_error in layer_errors:
            print(f"{layer_error.alternate} by {layer_error.owner.username}")
