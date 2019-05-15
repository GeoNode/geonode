# -*- coding: utf-8 -*-
#########################################################################
#
# Copyright (C) 2018 OSGeo
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

import ast
import sys
import json

from django.core.management.base import BaseCommand

from geonode.layers.models import Layer
from geonode.security.views import _perms_info_json
from geonode.geoserver.helpers import set_attributes_from_geoserver


def sync_geonode_layers(ignore_errors, filter, username, updatepermissions, updatethumbnails):
    layers = Layer.objects.all().order_by('name')
    if filter:
        layers = layers.filter(name__icontains=filter)
    if username:
        layers = layers.filter(owner__username=username)
    layers_count = layers.count()
    count = 0
    layer_errors = []
    for layer in layers:
        try:
            count += 1
            print 'Syncing layer %s/%s: %s' % (count, layers_count, layer.name)
            if ast.literal_eval(updatepermissions):
                print 'Syncing permissions...'
                # sync permissions in GeoFence
                perm_spec = json.loads(_perms_info_json(layer))
                # re-sync GeoFence security rules
                layer.set_permissions(perm_spec)
                # recalculate the layer statistics
                set_attributes_from_geoserver(layer, overwrite=True)
            if ast.literal_eval(updatethumbnails):
                print 'Regenerating thumbnails...'
                layer.save()
        except Exception:
            layer_errors.append(layer.alternate)
            exception_type, error, traceback = sys.exc_info()
            print exception_type, error, traceback
            if ignore_errors:
                pass
            else:
                print 'Stopping process because --ignore-errors was not set and an error was found.'
                return
    print 'There are %s layers which could not be updated because of errors' % len(layer_errors)
    for layer_error in layer_errors:
        print layer_error


class Command(BaseCommand):
    help = 'Update the GeoNode layers: permissions (including GeoFence database), statistics, thumbnails'

    def add_arguments(self, parser):
        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.'
        )
        parser.add_argument(
            '-f',
            '--filter',
            dest="filter",
            default=None,
            help="Only update data the layers that match the given filter"),
        parser.add_argument(
            '-u',
            '--username',
            dest="username",
            default=None,
            help="Only update data owned by the specified username")
        parser.add_argument(
            '--updatepermissions',
            dest="updatepermissions",
            default='True',
            help="Update only the layer permissions. Does not regenerate styles and thumbnails")
        parser.add_argument(
            '--updatethumbnails',
            dest="updatethumbnails",
            default='True',
            help="Update only the layer styles and thumbnails. Does not re-sync security rules.")

    def handle(self, **options):
        ignore_errors = options.get('ignore_errors')
        updatepermissions = options.get('updatepermissions')
        updatethumbnails = options.get('updatethumbnails')
        filter = options.get('filter')
        if not options.get('username'):
            username = None
        else:
            username = options.get('username')
        sync_geonode_layers(ignore_errors, filter, username, updatepermissions, updatethumbnails)
