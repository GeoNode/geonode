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

import helpers

from django.db.models import Func, F, Value
from django.core.management.base import BaseCommand, CommandError

from geonode.base.models import ResourceBase
from geonode.layers.models import Layer, Style
from geonode.maps.models import Map, MapLayer
from geonode.base.models import Link

from geonode.utils import designals, resignals


class Command(BaseCommand):

    help = 'Migrate GeoNode VM Base URL'

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '-f',
            '--force',
            action='store_true',
            dest='force_exec',
            default=False,
            help='Forces the execution without asking for confirmation.')

        parser.add_argument(
            '--source-address',
            dest='source_address',
            help='Source Address (the one currently on DB e.g. http://192.168.1.23)')

        parser.add_argument(
            '--target-address',
            dest='target_address',
            help='Target Address (the one to be changed e.g. http://my-public.geonode.org)')

    def handle(self, **options):
        force_exec = options.get('force_exec')
        source_address = options.get('source_address')
        target_address = options.get('target_address')

        if not source_address or len(source_address) == 0:
            raise CommandError("Source Address '--source-address' is mandatory")

        if not target_address or len(target_address) == 0:
            raise CommandError("Target Address '--target-address' is mandatory")

        print "This will change all Maps, Layers, \
Styles and Links Base URLs from [%s] to [%s]." % (source_address, target_address)
        print "The operation may take some time, depending on the amount of Layer on GeoNode."
        message = 'You want to proceed?'

        if force_exec or helpers.confirm(prompt=message, resp=False):
            try:
                # Deactivate GeoNode Signals
                print "Deactivating GeoNode Signals..."
                designals()
                print "...done!"

                _cnt = Map.objects.filter(thumbnail_url__icontains=source_address).update(
                    thumbnail_url=Func(
                        F('thumbnail_url'),Value(source_address),Value(target_address),function='replace'))
                print "Updated %s Maps" % _cnt

                _cnt = MapLayer.objects.filter(ows_url__icontains=source_address).update(
                    ows_url=Func(
                        F('ows_url'),Value(source_address),Value(target_address),function='replace'))
                MapLayer.objects.filter(layer_params__icontains=source_address).update(
                    layer_params=Func(
                        F('layer_params'),Value(source_address),Value(target_address),function='replace'))
                print "Updated %s MapLayers" % _cnt

                _cnt = Layer.objects.filter(thumbnail_url__icontains=source_address).update(
                    thumbnail_url=Func(
                        F('thumbnail_url'),Value(source_address),Value(target_address),function='replace'))
                print "Updated %s Layers" % _cnt

                _cnt = Style.objects.filter(sld_url__icontains=source_address).update(
                    sld_url=Func(
                        F('sld_url'),Value(source_address),Value(target_address),function='replace'))
                print "Updated %s Styles" % _cnt

                _cnt = Link.objects.filter(url__icontains=source_address).update(
                    url=Func(
                        F('url'),Value(source_address),Value(target_address),function='replace'))
                print "Updated %s Links" % _cnt

                _cnt = ResourceBase.objects.filter(thumbnail_url__icontains=source_address).update(
                    thumbnail_url=Func(
                        F('thumbnail_url'),Value(source_address),Value(target_address),function='replace'))
                print "Updated %s ResourceBases" % _cnt
            finally:
                # Reactivate GeoNode Signals
                print "Reactivating GeoNode Signals..."
                resignals()
                print "...done!"
