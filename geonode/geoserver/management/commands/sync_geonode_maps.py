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

import sys

from django.core.management.base import BaseCommand

from geonode.maps.models import Map
from geonode.base.utils import remove_duplicate_links
from geonode.geoserver.helpers import (
    create_gs_thumbnail
)


def sync_geonode_maps(ignore_errors,
                      filter,
                      username,
                      removeduplicates,
                      updatethumbnails):
    maps = Map.objects.all().order_by('title')
    if filter:
        maps = maps.filter(title__icontains=filter)
    if username:
        maps = maps.filter(owner__username=username)
    maps_count = maps.count()
    count = 0
    map_errors = []
    for map in maps:
        try:
            count += 1
            print(f"Syncing map {count}/{maps_count}: {map.title}")
            if updatethumbnails:
                print("Regenerating thumbnails...")
                create_gs_thumbnail(map, overwrite=True, check_bbox=False)
            if removeduplicates:
                # remove duplicates
                print("Removing duplicate links...")
                remove_duplicate_links(map)
        except Exception:
            map_errors.append(map.title)
            exception_type, error, traceback = sys.exc_info()
            print(exception_type, error, traceback)
            if ignore_errors:
                pass
            else:
                import traceback
                traceback.print_exc()
                print("Stopping process because --ignore-errors was not set and an error was found.")
                return
    print("There are {} maps which could not be updated because of errors".format(len(map_errors)))
    for map_error in map_errors:
         print(map_error)


class Command(BaseCommand):
    help = 'Update the GeoNode maps: permissions, thumbnails'

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
            '-d',
            '--remove-duplicates',
            action='store_true',
            dest='removeduplicates',
            default=False,
            help='Remove duplicates first.'
        )
        parser.add_argument(
            '-f',
            '--filter',
            dest="filter",
            default=None,
            help="Only update data the maps that match the given filter."),
        parser.add_argument(
            '-u',
            '--username',
            dest="username",
            default=None,
            help="Only update data owned by the specified username.")
        parser.add_argument(
            '--updatethumbnails',
            action='store_true',
            dest="updatethumbnails",
            default=False,
            help="Update the map styles and thumbnails.")

    def handle(self, **options):
        ignore_errors = options.get('ignore_errors')
        removeduplicates = options.get('removeduplicates')
        updatethumbnails = options.get('updatethumbnails')
        filter = options.get('filter')
        if not options.get('username'):
            username = None
        else:
            username = options.get('username')
        sync_geonode_maps(
            ignore_errors,
            filter,
            username,
            removeduplicates,
            updatethumbnails)
