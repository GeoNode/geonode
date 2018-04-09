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

from django.core.management.base import BaseCommand, CommandError

from geonode.base.models import ResourceBase
from geonode.layers.models import Layer, Style
from geonode.maps.models import Map
from geonode.base.models import Link

from geonode.utils import designals, resignals


class Command(BaseCommand):

    help = 'Migrate GeoNode VM Base URL'

    def add_arguments(self, parser):

        # Named (optional) arguments
        parser.add_argument(
            '-i',
            '--ignore-errors',
            action='store_true',
            dest='ignore_errors',
            default=False,
            help='Stop after any errors are encountered.')

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
        # ignore_errors = options.get('ignore_errors')
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

                maps = Map.objects.all()

                for map in maps:
                    print "Checking Map[%s]" % (map)
                    if map.thumbnail_url:
                        map.thumbnail_url = map.thumbnail_url.replace(source_address, target_address)
                    map_layers = map.layers
                    for layer in map_layers:
                        if layer.ows_url:
                            original = layer.ows_url
                            layer.ows_url = layer.ows_url.replace(source_address, target_address)
                            print "Updated OWS URL from [%s] to [%s]" % (original, layer.ows_url)
                        if layer.layer_params:
                            layer.layer_params = layer.layer_params.replace(source_address, target_address)
                            print "Updated Layer Params also for Layer [%s]" % (layer)
                        layer.save()
                    map.save()
                    print "Updated Map[%s]" % (map)

                layers = Layer.objects.all()

                for layer in layers:
                    print "Checking Layer[%s]" % (layer)
                    if layer.thumbnail_url:
                        original = layer.thumbnail_url
                        layer.thumbnail_url = layer.thumbnail_url.replace(source_address, target_address)
                        layer.save()
                        print "Updated Thumbnail URL from [%s] to [%s]" % (original, layer.thumbnail_url)

                styles = Style.objects.all()

                for style in styles:
                    print "Checking Style[%s]" % (style)
                    if style.sld_url:
                        original = style.sld_url
                        style.sld_url = style.sld_url.replace(source_address, target_address)
                        style.save()
                        print "Updated SLD URL from [%s] to [%s]" % (original, style.sld_url)

                links = Link.objects.all()

                for link in links:
                    print "Checking Link[%s]" % (link)
                    if link.url:
                        original = link.url
                        link.url = link.url.replace(source_address, target_address)
                        link.save()
                        print "Updated URL from [%s] to [%s]" % (original, link.url)

                resources = ResourceBase.objects.all()

                for res in resources:
                    print "Checking Resource[%s]" % (res)
                    if res.metadata_xml:
                        original = res.metadata_xml
                        res.metadata_xml = res.metadata_xml.replace(source_address, target_address)
                        res.save()
                        print "Updated URL in metadata XML for resource [%s]" % (res)

            finally:
                # Reactivate GeoNode Signals
                print "Reactivating GeoNode Signals..."
                resignals()
                print "...done!"
